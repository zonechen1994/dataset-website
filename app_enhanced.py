from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required as flask_login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path

from config import config
from models import db, Dataset, Author, Category, Modality, TaskType, dataset_authors, User, Notification, PlanetApplication, EmailVerificationCode
from timezone_utils import format_china_time
from auth_enhanced import (
    init_login_manager, 
    login_required, 
    admin_required, 
    planet_required,
    has_planet_access,
    is_logged_in, 
    is_admin, 
    get_user_role, 
    create_default_admin,
    authenticate_user
)
from auth_routes import auth_bp
from user_admin_routes import user_admin_bp
from planet_routes import planet_bp
from email_service import init_mail

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化邮件服务
    init_mail(app)
    
    # 初始化登录管理器
    init_login_manager(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_admin_bp)
    app.register_blueprint(planet_bp)
    
    # 注册图片上传蓝图
    from image_upload_routes import image_upload_bp
    app.register_blueprint(image_upload_bp)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 添加自定义Jinja2过滤器
    @app.template_filter('from_json')
    def from_json_filter(value):
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @app.template_filter('format_time')
    def format_time_filter(value, format_str='%Y-%m-%d %H:%M:%S'):
        """格式化时间显示为中国时间"""
        return format_china_time(value, format_str)
    
    # 添加上下文处理器
    @app.context_processor
    def inject_user_info():
        unread_notifications_count = 0
        if current_user.is_authenticated:
            unread_notifications_count = Notification.query.filter_by(
                recipient_id=current_user.id,
                is_read=False
            ).count()
        
        return {
            'is_admin': is_admin(),
            'is_logged_in': is_logged_in(),
            'user_role': get_user_role(),
            'current_user': current_user if current_user.is_authenticated else None,
            'unread_notifications_count': unread_notifications_count
        }
    
    @app.route('/')
    def index():
        # 获取筛选参数
        organ_category = request.args.get('organ_category', '')
        modality = request.args.get('modality', '')
        task_type = request.args.get('task_type', '')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        
        # 构建查询
        query = Dataset.query
        
        if organ_category:
            query = query.filter(Dataset.organ_category == organ_category)
        if modality:
            query = query.filter(Dataset.modality.like(f'%{modality}%'))
        if task_type:
            query = query.filter(Dataset.task_type.like(f'%{task_type}%'))
        if search:
            query = query.filter(
                Dataset.name.like(f'%{search}%') | 
                Dataset.description.like(f'%{search}%') |
                Dataset.anatomical_structure.like(f'%{search}%')
            )
        
        # 分页
        datasets = query.paginate(
            page=page, 
            per_page=app.config['DATASETS_PER_PAGE'],
            error_out=False
        )
        
        # 获取筛选选项
        categories = Category.query.all()
        
        # 从数据库获取模态类型
        modalities = Modality.query.order_by(Modality.category, Modality.name).all()
        
        # 从数据库获取任务类型
        task_types = TaskType.query.order_by(TaskType.name).all()
        
        return render_template('index.html', 
                             datasets=datasets,
                             categories=categories,
                             modalities=modalities,
                             task_types=task_types,
                             current_filters={
                                 'organ_category': organ_category,
                                 'modality': modality,
                                 'task_type': task_type,
                                 'search': search
                             })
    
    @app.route('/dataset/<int:dataset_id>')
    def dataset_detail(dataset_id):
        dataset = Dataset.query.get_or_404(dataset_id)
        # 不需要手动传递is_admin，因为上下文处理器已经提供了
        return render_template('dataset_detail.html', dataset=dataset)
    
    @app.route('/dataset/<int:dataset_id>/download')
    def download_dataset(dataset_id):
        """开放的数据集下载 - 不需要知识星球权限"""
        dataset = Dataset.query.get_or_404(dataset_id)
        
        if not dataset.download_link or dataset.download_link.upper() in ['NA', 'TBD', 'N/A', '待定', '无']:
            flash('此数据集暂无下载链接', 'warning')
            return redirect(url_for('dataset_detail', dataset_id=dataset_id))
        
        # 记录下载日志（可选）
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            print(f"用户 {current_user.username} 下载数据集 {dataset.name}")
        else:
            print(f"匿名用户下载数据集 {dataset.name}")
        
        return redirect(dataset.download_link)
    
    @app.route('/dataset/<int:dataset_id>/baidu-pan')
    @planet_required
    def baidu_pan_dataset(dataset_id):
        """受保护的百度网盘访问"""
        dataset = Dataset.query.get_or_404(dataset_id)
        
        if not dataset.baidu_pan_link or dataset.baidu_pan_link.upper() in ['NA', 'TBD', 'N/A', '待定', '无']:
            flash('此数据集暂无百度网盘链接', 'warning')
            return redirect(url_for('dataset_detail', dataset_id=dataset_id))
        
        # 记录访问日志（可选）
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            print(f"用户 {current_user.username} 访问数据集 {dataset.name} 的百度网盘")
        
        return redirect(dataset.baidu_pan_link)
    
    @app.route('/dataset/new', methods=['GET', 'POST'])
    @admin_required
    def new_dataset():
        if request.method == 'POST':
            # 创建新数据集
            dataset = Dataset()
            dataset.name = request.form.get('name')
            dataset.organ_category = request.form.get('organ_category')
            dataset.dimension = request.form.get('dimension')
            dataset.modality = request.form.get('modality')
            dataset.task_type = request.form.get('task_type')
            dataset.anatomical_structure = request.form.get('anatomical_structure')
            dataset.anatomical_region = request.form.get('anatomical_region')
            dataset.num_classes = request.form.get('num_classes', type=int)
            dataset.data_volume = request.form.get('data_volume')
            dataset.file_format = request.form.get('file_format')
            dataset.official_website = request.form.get('official_website')
            dataset.download_link = request.form.get('download_link')
            dataset.baidu_pan_link = request.form.get('baidu_pan_link')
            dataset.baidu_pan_password = request.form.get('baidu_pan_password')
            dataset.paper_link = request.form.get('paper_link')
            dataset.publication_date = request.form.get('publication_date')
            dataset.description = request.form.get('description')
            dataset.file_structure = request.form.get('file_structure')
            dataset.citation = request.form.get('citation')
            
            # 处理作者信息（文本格式）
            authors_text = request.form.get('authors_text', '').strip()
            
            # 处理可视化图片 - 支持上传的图片和URL链接
            images = []
            
            # 处理上传的图片（来自拖放上传组件）
            uploaded_images_json = request.form.get('uploaded_images', '').strip()
            if uploaded_images_json:
                try:
                    uploaded_images = json.loads(uploaded_images_json)
                    images.extend(uploaded_images)
                except json.JSONDecodeError:
                    print("解析上传图片JSON失败")
            
            # 处理URL链接（备用方式）
            visualization_images_text = request.form.get('visualization_images', '').strip()
            if visualization_images_text:
                urls = [line.strip() for line in visualization_images_text.split('\n') if line.strip()]
                url_images = [{'url': url, 'alt': f'可视化图片 {len(images) + i + 1}'} for i, url in enumerate(urls)]
                images.extend(url_images)
            
            # 保存图片信息
            if images:
                dataset.visualization_images = json.dumps(images, ensure_ascii=False)
            else:
                dataset.visualization_images = None
            
            # 处理图像尺寸统计
            image_stats = {}
            
            # 处理最小值
            min_size = request.form.get('min_size', '').strip()
            min_spacing = request.form.get('min_spacing', '').strip()
            if min_size:
                image_stats['min'] = {
                    'size': min_size,
                    'spacing': min_spacing if min_spacing else None
                }
            
            # 处理中位值
            median_size = request.form.get('median_size', '').strip()
            median_spacing = request.form.get('median_spacing', '').strip()
            if median_size:
                image_stats['median'] = {
                    'size': median_size,
                    'spacing': median_spacing if median_spacing else None
                }
            
            # 处理最大值
            max_size = request.form.get('max_size', '').strip()
            max_spacing = request.form.get('max_spacing', '').strip()
            if max_size:
                image_stats['max'] = {
                    'size': max_size,
                    'spacing': max_spacing if max_spacing else None
                }
            
            dataset.image_stats = json.dumps(image_stats, ensure_ascii=False)
            
            try:
                db.session.add(dataset)
                db.session.flush()  # 获取数据集ID
                
                # 处理作者信息
                if authors_text:
                    for line in authors_text.split('\n'):
                        line = line.strip()
                        if line:
                            # 解析格式：姓名 | 机构名称
                            if '|' in line:
                                name, institution = line.split('|', 1)
                                name = name.strip()
                                institution = institution.strip()
                            else:
                                name = line.strip()
                                institution = None
                            
                            if name:  # 只处理非空的作者姓名
                                # 查找或创建作者
                                author = Author.query.filter_by(name=name).first()
                                if not author:
                                    author = Author(name=name, institution=institution)
                                    db.session.add(author)
                                else:
                                    # 更新机构信息（如果提供了新的机构）
                                    if institution:
                                        author.institution = institution
                                
                                # 关联数据集和作者
                                if author not in dataset.authors:
                                    dataset.authors.append(author)
                
                db.session.commit()
                flash('数据集创建成功！', 'success')
                return redirect(url_for('dataset_detail', dataset_id=dataset.id))
            except Exception as e:
                db.session.rollback()
                flash(f'创建失败：{str(e)}', 'error')
        
        categories = Category.query.all()
        modalities = Modality.query.order_by(Modality.category, Modality.name).all()
        task_types = TaskType.query.order_by(TaskType.name).all()
        return render_template('new_dataset.html', categories=categories, modalities=modalities, task_types=task_types)
    
    @app.route('/dataset/<int:dataset_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def edit_dataset(dataset_id):
        dataset = Dataset.query.get_or_404(dataset_id)
        
        if request.method == 'POST':
            # 更新数据集信息
            dataset.name = request.form.get('name')
            dataset.organ_category = request.form.get('organ_category')
            dataset.dimension = request.form.get('dimension')
            dataset.modality = request.form.get('modality')
            dataset.task_type = request.form.get('task_type')
            dataset.anatomical_structure = request.form.get('anatomical_structure')
            dataset.anatomical_region = request.form.get('anatomical_region')
            dataset.num_classes = request.form.get('num_classes', type=int)
            dataset.data_volume = request.form.get('data_volume')
            dataset.file_format = request.form.get('file_format')
            dataset.official_website = request.form.get('official_website')
            dataset.download_link = request.form.get('download_link')
            dataset.baidu_pan_link = request.form.get('baidu_pan_link')
            dataset.baidu_pan_password = request.form.get('baidu_pan_password')
            dataset.paper_link = request.form.get('paper_link')
            dataset.publication_date = request.form.get('publication_date')
            dataset.description = request.form.get('description')
            dataset.file_structure = request.form.get('file_structure')
            dataset.citation = request.form.get('citation')
            
            # 处理作者信息（文本格式）
            authors_text = request.form.get('authors_text', '').strip()
            
            # 清除现有作者关联
            dataset.authors.clear()
            
            # 解析作者文本
            if authors_text:
                for line in authors_text.split('\n'):
                    line = line.strip()
                    if line:
                        # 解析格式：姓名 | 机构名称
                        if '|' in line:
                            name, institution = line.split('|', 1)
                            name = name.strip()
                            institution = institution.strip()
                        else:
                            name = line.strip()
                            institution = None
                        
                        if name:  # 只处理非空的作者姓名
                            # 查找或创建作者
                            author = Author.query.filter_by(name=name).first()
                            if not author:
                                author = Author(name=name, institution=institution)
                                db.session.add(author)
                            else:
                                # 更新机构信息（如果提供了新的机构）
                                if institution:
                                    author.institution = institution
                            
                            # 关联数据集和作者
                            if author not in dataset.authors:
                                dataset.authors.append(author)
            
            # 处理可视化图片 - 支持上传的图片和URL链接
            images = []
            
            # 处理上传的图片（来自拖放上传组件）
            uploaded_images_json = request.form.get('uploaded_images', '').strip()
            if uploaded_images_json:
                try:
                    uploaded_images = json.loads(uploaded_images_json)
                    images.extend(uploaded_images)
                except json.JSONDecodeError:
                    print("解析上传图片JSON失败")
            
            # 处理URL链接（备用方式）
            visualization_images_text = request.form.get('visualization_images', '').strip()
            if visualization_images_text:
                urls = [line.strip() for line in visualization_images_text.split('\n') if line.strip()]
                url_images = [{'url': url, 'alt': f'可视化图片 {len(images) + i + 1}'} for i, url in enumerate(urls)]
                images.extend(url_images)
            
            # 保存图片信息
            if images:
                dataset.visualization_images = json.dumps(images, ensure_ascii=False)
            else:
                dataset.visualization_images = None
            
            # 处理图像尺寸统计
            image_stats = {}
            
            # 处理最小值
            min_size = request.form.get('min_size', '').strip()
            min_spacing = request.form.get('min_spacing', '').strip()
            if min_size:
                image_stats['min'] = {
                    'size': min_size,
                    'spacing': min_spacing if min_spacing else None
                }
            
            # 处理中位值
            median_size = request.form.get('median_size', '').strip()
            median_spacing = request.form.get('median_spacing', '').strip()
            if median_size:
                image_stats['median'] = {
                    'size': median_size,
                    'spacing': median_spacing if median_spacing else None
                }
            
            # 处理最大值
            max_size = request.form.get('max_size', '').strip()
            max_spacing = request.form.get('max_spacing', '').strip()
            if max_size:
                image_stats['max'] = {
                    'size': max_size,
                    'spacing': max_spacing if max_spacing else None
                }
            
            dataset.image_stats = json.dumps(image_stats, ensure_ascii=False)
            
            try:
                db.session.commit()
                flash('数据集更新成功！', 'success')
                return redirect(url_for('dataset_detail', dataset_id=dataset.id))
            except Exception as e:
                db.session.rollback()
                flash(f'更新失败：{str(e)}', 'error')
        
        categories = Category.query.all()
        modalities = Modality.query.order_by(Modality.category, Modality.name).all()
        task_types = TaskType.query.order_by(TaskType.name).all()
        return render_template('edit_dataset.html', dataset=dataset, categories=categories, modalities=modalities, task_types=task_types)
    
    @app.route('/dataset/<int:dataset_id>/delete', methods=['POST'])
    @admin_required
    def delete_dataset(dataset_id):
        dataset = Dataset.query.get_or_404(dataset_id)
        
        try:
            db.session.delete(dataset)
            db.session.commit()
            flash('数据集删除成功！', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'删除失败：{str(e)}', 'error')
        
        return redirect(url_for('index'))
    
    @app.route('/datasets/batch-delete', methods=['POST'])
    @admin_required
    def batch_delete_datasets():
        dataset_ids = request.form.getlist('dataset_ids')
        
        if not dataset_ids:
            flash('请选择要删除的数据集', 'error')
            return redirect(url_for('index'))
        
        try:
            # 查找要删除的数据集
            datasets = Dataset.query.filter(Dataset.id.in_(dataset_ids)).all()
            
            if not datasets:
                flash('未找到要删除的数据集', 'error')
                return redirect(url_for('index'))
            
            # 删除数据集
            for dataset in datasets:
                db.session.delete(dataset)
            
            db.session.commit()
            
            flash(f'成功删除 {len(datasets)} 个数据集', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'批量删除失败：{str(e)}', 'error')
        
        return redirect(url_for('index'))
    
    @app.route('/upload', methods=['GET', 'POST'])
    @admin_required
    def upload_markdown():
        if request.method == 'POST':
            file = request.files.get('file')
            if file and file.filename.endswith('.md'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # 解析MD文件并保存到数据库
                try:
                    from md_parser import parse_markdown_file, extract_authors_from_content
                    
                    # 解析MD文件
                    dataset_data = parse_markdown_file(filepath)
                    
                    # 读取文件内容以提取作者信息
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 创建数据集
                    dataset = Dataset()
                    for field, value in dataset_data.items():
                        if hasattr(dataset, field) and value is not None:
                            setattr(dataset, field, value)
                    
                    db.session.add(dataset)
                    db.session.flush()  # 获取数据集ID
                    
                    # 处理作者信息
                    authors_data = extract_authors_from_content(content)
                    for author_data in authors_data:
                        # 查找或创建作者
                        author = Author.query.filter_by(
                            name=author_data['name'],
                            institution=author_data['institution']
                        ).first()
                        
                        if not author:
                            author = Author(**author_data)
                            db.session.add(author)
                            db.session.flush()
                        
                        # 建立关联
                        if author not in dataset.authors:
                            dataset.authors.append(author)
                    
                    db.session.commit()
                    
                    # 删除临时文件
                    os.remove(filepath)
                    
                    flash('MD文件上传并解析成功！', 'success')
                    return redirect(url_for('dataset_detail', dataset_id=dataset.id))
                except Exception as e:
                    db.session.rollback()
                    # 删除临时文件
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    flash(f'文件解析失败：{str(e)}', 'error')
            else:
                flash('请选择有效的MD文件', 'error')
        
        return render_template('upload.html')
    
    @app.route('/upload/batch', methods=['GET', 'POST'])
    @admin_required
    def batch_upload_markdown():
        if request.method == 'POST':
            files = request.files.getlist('files')
            target_category = request.form.get('target_category', '').strip()
            
            if not files:
                flash('请选择要上传的文件', 'error')
                return redirect(request.url)
            
            success_count = 0
            error_count = 0
            results = []
            
            # 如果指定了目标类别，验证类别是否存在
            target_category_name = None
            if target_category:
                category_obj = Category.query.filter_by(code=target_category).first()
                if category_obj:
                    target_category_name = category_obj.name
                else:
                    flash(f'指定的类别"{target_category}"不存在', 'error')
                    return redirect(request.url)
            
            for file in files:
                if file and file.filename.endswith('.md'):
                    try:
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        # 解析MD文件
                        from md_parser import parse_markdown_file, extract_authors_from_content
                        
                        # 解析MD文件
                        dataset_data = parse_markdown_file(filepath)
                        
                        # 读取文件内容以提取作者信息
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 创建数据集
                        dataset = Dataset()
                        for field, value in dataset_data.items():
                            if hasattr(dataset, field) and value is not None:
                                setattr(dataset, field, value)
                        
                        # 如果指定了目标类别，覆盖解析结果
                        original_category = dataset.organ_category
                        if target_category:
                            dataset.organ_category = target_category
                        
                        db.session.add(dataset)
                        db.session.flush()  # 获取数据集ID
                        
                        # 处理作者信息
                        authors_data = extract_authors_from_content(content)
                        for author_data in authors_data:
                            # 查找或创建作者
                            author = Author.query.filter_by(
                                name=author_data['name'],
                                institution=author_data['institution']
                            ).first()
                            
                            if not author:
                                author = Author(**author_data)
                                db.session.add(author)
                                db.session.flush()
                            
                            # 建立关联
                            if author not in dataset.authors:
                                dataset.authors.append(author)
                        
                        db.session.commit()
                        
                        # 删除临时文件
                        os.remove(filepath)
                        
                        success_count += 1
                        
                        # 构建结果信息
                        result_info = {
                            'filename': filename,
                            'status': 'success',
                            'dataset_name': dataset.name,
                            'organ_category': dataset.organ_category,
                            'modality': dataset.modality,
                            'dataset_id': dataset.id
                        }
                        
                        # 如果类别被覆盖，记录原始类别
                        if target_category and original_category != target_category:
                            result_info['category_changed'] = True
                            result_info['original_category'] = original_category
                            result_info['target_category_name'] = target_category_name
                        else:
                            result_info['category_changed'] = False
                        
                        results.append(result_info)
                        
                    except Exception as e:
                        db.session.rollback()
                        # 删除临时文件
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        
                        error_count += 1
                        results.append({
                            'filename': filename,
                            'status': 'error',
                            'error': str(e)
                        })
                else:
                    error_count += 1
                    results.append({
                        'filename': file.filename if file else '未知文件',
                        'status': 'error',
                        'error': '不是有效的MD文件'
                    })
            
            flash(f'批量上传完成！成功：{success_count} 个，失败：{error_count} 个', 'info')
            return render_template('batch_upload_result.html', 
                                 results=results,
                                 target_category=target_category,
                                 target_category_name=target_category_name,
                                 success_count=success_count,
                                 error_count=error_count,
                                 total_count=len(results))
        
        # 获取所有类别数据供模板使用
        categories = Category.query.order_by(Category.name).all()
        return render_template('batch_upload.html', categories=categories)
    
    # 管理后台路由
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        # 统计信息
        categories_count = Category.query.count()
        modalities_count = Modality.query.count()
        task_types_count = TaskType.query.count()
        datasets_count = Dataset.query.count()
        users_count = User.query.count()
        
        return render_template('admin/dashboard.html', 
                             categories_count=categories_count,
                             modalities_count=modalities_count,
                             task_types_count=task_types_count,
                             datasets_count=datasets_count,
                             users_count=users_count)
    
    # 数据集管理
    @app.route('/admin/datasets')
    @admin_required  
    def admin_datasets():
        # 获取筛选和搜索参数
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        modality = request.args.get('modality', '')
        task_type = request.args.get('task_type', '')
        
        # 构建查询
        query = Dataset.query
        
        if search:
            query = query.filter(
                Dataset.name.like(f'%{search}%') | 
                Dataset.description.like(f'%{search}%') |
                Dataset.anatomical_structure.like(f'%{search}%')
            )
        if category:
            query = query.filter(Dataset.organ_category == category)
        if modality:
            query = query.filter(Dataset.modality.like(f'%{modality}%'))
        if task_type:
            query = query.filter(Dataset.task_type.like(f'%{task_type}%'))
        
        # 按ID倒序排列，获取分页数据
        datasets = query.order_by(Dataset.id.desc()).paginate(
            page=page,
            per_page=20,  # 管理页面每页显示更多
            error_out=False
        )
        
        # 获取筛选选项数据
        categories = Category.query.all()
        modalities = Modality.query.order_by(Modality.category, Modality.name).all()
        task_types = TaskType.query.order_by(TaskType.name).all()
        
        return render_template('admin/datasets.html',
                             datasets=datasets,
                             categories=categories,
                             modalities=modalities,
                             task_types=task_types,
                             current_filters={
                                 'search': search,
                                 'category': category,
                                 'modality': modality,
                                 'task_type': task_type
                             })
    
    # 器官分类管理
    @app.route('/admin/categories')
    @admin_required
    def admin_categories():
        categories = Category.query.order_by(Category.name).all()
        return render_template('admin/categories.html', categories=categories)
    
    @app.route('/admin/categories/new', methods=['GET', 'POST'])
    @admin_required
    def admin_new_category():
        if request.method == 'POST':
            code = request.form.get('code')
            name = request.form.get('name')
            description = request.form.get('description')
            
            # 检查代码是否已存在
            existing = Category.query.filter_by(code=code).first()
            if existing:
                flash(f'器官分类代码 "{code}" 已存在', 'error')
                return render_template('admin/category_form.html')
            
            category = Category(code=code, name=name, description=description)
            db.session.add(category)
            db.session.commit()
            
            flash(f'器官分类 "{name}" 创建成功！', 'success')
            return redirect(url_for('admin_categories'))
        
        return render_template('admin/category_form.html')
    
    @app.route('/admin/categories/<int:category_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_category(category_id):
        category = Category.query.get_or_404(category_id)
        
        if request.method == 'POST':
            old_code = category.code
            category.code = request.form.get('code')
            category.name = request.form.get('name')
            category.description = request.form.get('description')
            
            # 检查代码是否与其他分类冲突
            if old_code != category.code:
                existing = Category.query.filter_by(code=category.code).first()
                if existing:
                    flash(f'器官分类代码 "{category.code}" 已存在', 'error')
                    return render_template('admin/category_form.html', category=category)
            
            db.session.commit()
            
            flash(f'器官分类 "{category.name}" 更新成功！', 'success')
            return redirect(url_for('admin_categories'))
        
        return render_template('admin/category_form.html', category=category)
    
    @app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_category(category_id):
        category = Category.query.get_or_404(category_id)
        
        # 检查是否有数据集使用此分类
        datasets_count = Dataset.query.filter_by(organ_category=category.code).count()
        if datasets_count > 0:
            flash(f'无法删除器官分类 "{category.name}"，还有 {datasets_count} 个数据集正在使用', 'error')
        else:
            db.session.delete(category)
            db.session.commit()
            flash(f'器官分类 "{category.name}" 删除成功！', 'success')
        
        return redirect(url_for('admin_categories'))
    
    # 模态类型管理
    @app.route('/admin/modalities')
    @admin_required
    def admin_modalities():
        modalities = Modality.query.order_by(Modality.category, Modality.name).all()
        return render_template('admin/modalities.html', modalities=modalities)
    
    @app.route('/admin/modalities/new', methods=['GET', 'POST'])
    @admin_required
    def admin_new_modality():
        if request.method == 'POST':
            code = request.form.get('code')
            name = request.form.get('name')
            description = request.form.get('description')
            category = request.form.get('category')
            
            # 检查代码是否已存在
            existing = Modality.query.filter_by(code=code).first()
            if existing:
                flash(f'模态类型代码 "{code}" 已存在', 'error')
                return render_template('admin/modality_form.html')
            
            modality = Modality(code=code, name=name, description=description, category=category)
            db.session.add(modality)
            db.session.commit()
            
            flash(f'模态类型 "{name}" 创建成功！', 'success')
            return redirect(url_for('admin_modalities'))
        
        return render_template('admin/modality_form.html')
    
    @app.route('/admin/modalities/<int:modality_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_modality(modality_id):
        modality = Modality.query.get_or_404(modality_id)
        
        if request.method == 'POST':
            old_code = modality.code
            modality.code = request.form.get('code')
            modality.name = request.form.get('name')
            modality.description = request.form.get('description')
            modality.category = request.form.get('category')
            
            # 检查代码是否与其他模态冲突
            if old_code != modality.code:
                existing = Modality.query.filter_by(code=modality.code).first()
                if existing:
                    flash(f'模态类型代码 "{modality.code}" 已存在', 'error')
                    return render_template('admin/modality_form.html', modality=modality)
            
            db.session.commit()
            
            flash(f'模态类型 "{modality.name}" 更新成功！', 'success')
            return redirect(url_for('admin_modalities'))
        
        return render_template('admin/modality_form.html', modality=modality)
    
    @app.route('/admin/modalities/<int:modality_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_modality(modality_id):
        modality = Modality.query.get_or_404(modality_id)
        
        # 检查是否有数据集使用此模态
        datasets_count = Dataset.query.filter_by(modality=modality.code).count()
        if datasets_count > 0:
            flash(f'无法删除模态类型 "{modality.name}"，还有 {datasets_count} 个数据集正在使用', 'error')
        else:
            db.session.delete(modality)
            db.session.commit()
            flash(f'模态类型 "{modality.name}" 删除成功！', 'success')
        
        return redirect(url_for('admin_modalities'))
    
    # 任务类型管理
    @app.route('/admin/task-types')
    @admin_required
    def admin_task_types():
        task_types = TaskType.query.order_by(TaskType.name).all()
        return render_template('admin/task_types.html', task_types=task_types)
    
    @app.route('/admin/task-types/new', methods=['GET', 'POST'])
    @admin_required
    def admin_new_task_type():
        if request.method == 'POST':
            code = request.form.get('code')
            name = request.form.get('name')
            description = request.form.get('description')
            
            # 检查代码是否已存在
            existing = TaskType.query.filter_by(code=code).first()
            if existing:
                flash(f'任务类型代码 "{code}" 已存在', 'error')
                return render_template('admin/task_type_form.html')
            
            task_type = TaskType(code=code, name=name, description=description)
            db.session.add(task_type)
            db.session.commit()
            
            flash(f'任务类型 "{name}" 创建成功！', 'success')
            return redirect(url_for('admin_task_types'))
        
        return render_template('admin/task_type_form.html')
    
    @app.route('/admin/task-types/<int:task_type_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_task_type(task_type_id):
        task_type = TaskType.query.get_or_404(task_type_id)
        
        if request.method == 'POST':
            old_code = task_type.code
            task_type.code = request.form.get('code')
            task_type.name = request.form.get('name')
            task_type.description = request.form.get('description')
            
            # 检查代码是否与其他任务类型冲突
            if old_code != task_type.code:
                existing = TaskType.query.filter_by(code=task_type.code).first()
                if existing:
                    flash(f'任务类型代码 "{task_type.code}" 已存在', 'error')
                    return render_template('admin/task_type_form.html', task_type=task_type)
            
            db.session.commit()
            
            flash(f'任务类型 "{task_type.name}" 更新成功！', 'success')
            return redirect(url_for('admin_task_types'))
        
        return render_template('admin/task_type_form.html', task_type=task_type)
    
    @app.route('/admin/task-types/<int:task_type_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_task_type(task_type_id):
        task_type = TaskType.query.get_or_404(task_type_id)
        
        # 检查是否有数据集使用此任务类型
        datasets_count = Dataset.query.filter_by(task_type=task_type.code).count()
        if datasets_count > 0:
            flash(f'无法删除任务类型 "{task_type.name}"，还有 {datasets_count} 个数据集正在使用', 'error')
        else:
            db.session.delete(task_type)
            db.session.commit()
            flash(f'任务类型 "{task_type.name}" 删除成功！', 'success')
        
        return redirect(url_for('admin_task_types'))
    
    # 文件服务路由
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """提供上传文件的访问服务"""
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # API接口
    @app.route('/api/datasets')
    def api_datasets():
        datasets = Dataset.query.all()
        return jsonify([dataset.to_dict() for dataset in datasets])
    
    @app.route('/api/stats')
    def api_stats():
        """系统统计API"""
        stats = {
            'datasets': Dataset.query.count(),
            'users': User.query.count(),
            'categories': Category.query.count(),
            'modalities': Modality.query.count(),
            'task_types': TaskType.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'admin_users': User.query.filter_by(role='admin', is_active=True).count()
        }
        return jsonify(stats)
    
    @app.route('/send-verification-code', methods=['POST'])
    def send_verification_code():
        """发送邮箱验证码API"""
        from email_service import send_verification_code_email
        
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求数据格式错误'
                }), 400
            
            email = data.get('email', '').strip()
            purpose = data.get('purpose', 'registration').strip()
            
            # 验证邮箱格式
            if not email:
                return jsonify({
                    'success': False,
                    'message': '邮箱地址不能为空'
                }), 400
            
            if '@' not in email or '.' not in email.split('@')[1]:
                return jsonify({
                    'success': False,
                    'message': '请输入有效的邮箱地址'
                }), 400
            
            # 检查邮箱是否已被注册（仅注册时检查）
            if purpose == 'registration':
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    return jsonify({
                        'success': False,
                        'message': '该邮箱已被注册，请使用其他邮箱'
                    }), 400
            
            # 发送验证码
            result = send_verification_code_email(email, purpose)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'expires_in': result['expires_in']
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result['message']
                }), 500
                
        except Exception as e:
            import logging
            logging.error(f"发送验证码API异常: {str(e)}")
            return jsonify({
                'success': False,
                'message': '服务器内部错误，请稍后重试'
            }), 500
    
    # 兼容旧的登录路由（重定向到新路由）
    @app.route('/login', methods=['GET', 'POST'])
    def legacy_login():
        return redirect(url_for('auth.login'), code=301)
    
    @app.route('/logout')
    def legacy_logout():
        return redirect(url_for('auth.logout'), code=301)
    
    # 初始化数据库和默认管理员
    with app.app_context():
        try:
            db.create_all()
            create_default_admin()
        except Exception as e:
            print(f"数据库初始化警告: {e}")
            print("应用将继续运行，但某些功能可能受限")
            # 即使出错也继续启动应用
            pass
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5004)
