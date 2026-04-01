from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required as flask_login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path

from config import config
from models_basic import db, Dataset, Author, Category, Modality, TaskType, dataset_authors, User
from auth_enhanced import (
    init_login_manager, 
    login_required, 
    admin_required, 
    is_logged_in, 
    is_admin, 
    get_user_role, 
    create_default_admin,
    authenticate_user
)
from auth_routes import auth_bp
from user_admin_routes import user_admin_bp

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化登录管理器
    init_login_manager(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_admin_bp)
    
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
    
    # 添加上下文处理器
    @app.context_processor
    def inject_user_info():
        unread_notifications_count = 0
        # 暂时设为0，等通知功能完善后再启用
        
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
        return render_template('dataset_detail_basic.html', dataset=dataset)
    
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
            print("✅ 应用初始化成功！")
        except Exception as e:
            print(f"数据库初始化警告: {e}")
            print("应用将继续运行")
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5005)