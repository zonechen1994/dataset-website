from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import current_user
from models import User, db, Notification, PlanetApplication, EmailVerificationCode
from auth_enhanced import admin_required
from datetime import datetime
from timezone_utils import get_china_datetime

user_admin_bp = Blueprint('user_admin', __name__, url_prefix='/admin/users')

def cleanup_user_related_data(user):
    """
    清理用户相关的数据，避免外键约束错误
    在删除用户之前调用此函数
    
    Args:
        user: 要删除的用户对象
    """
    try:
        # 1. 删除该用户接收的所有通知
        received_notifications = Notification.query.filter_by(recipient_id=user.id).all()
        for notification in received_notifications:
            db.session.delete(notification)
        
        # 2. 删除该用户发送的所有通知
        sent_notifications = Notification.query.filter_by(sender_id=user.id).all()
        for notification in sent_notifications:
            db.session.delete(notification)
        
        # 3. 删除该用户的知识星球申请记录
        applications = PlanetApplication.query.filter_by(user_id=user.id).all()
        for application in applications:
            db.session.delete(application)
        
        # 4. 处理该用户审核的申请记录（将审核人设置为 NULL）
        reviewed_applications = PlanetApplication.query.filter_by(reviewed_by=user.id).all()
        for application in reviewed_applications:
            application.reviewed_by = None
        
        # 5. 处理该用户审核的其他用户知识星球权限（将审核人设置为 NULL）
        approved_users = User.query.filter_by(planet_approved_by=user.id).all()
        for approved_user in approved_users:
            approved_user.planet_approved_by = None
        
        # 6. 删除该用户邮箱的验证码记录（可选，但为了数据清洁）
        verification_codes = EmailVerificationCode.query.filter_by(email=user.email).all()
        for code in verification_codes:
            db.session.delete(code)
        
        # 注意：不要在这里提交事务，由调用者统一提交
        
    except Exception as e:
        # 重新抛出异常，让调用者处理
        raise e

@user_admin_bp.route('/')
@admin_required
def list_users():
    """用户列表"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    planet_filter = request.args.get('planet', '')
    
    # 构建查询
    query = User.query
    
    if search:
        query = query.filter(
            User.username.like(f'%{search}%') |
            User.email.like(f'%{search}%') |
            User.full_name.like(f'%{search}%')
        )
    
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    
    # 知识星球权限筛选
    if planet_filter:
        from datetime import timedelta
        from timezone_utils import get_china_datetime
        
        if planet_filter == 'has_access':
            # 有权限（不论是否到期）
            query = query.filter(User.is_planet_user == True)
        elif planet_filter == 'no_access':
            # 无权限
            query = query.filter(User.is_planet_user == False)
        elif planet_filter == 'expiring_soon':
            # 即将到期（7天内）
            now = get_china_datetime()
            seven_days_later = now + timedelta(days=7)
            query = query.filter(
                User.is_planet_user == True,
                User.planet_expiry_date != None,
                User.planet_expiry_date <= seven_days_later,
                User.planet_expiry_date > now
            )
        elif planet_filter == 'expired':
            # 已到期
            now = get_china_datetime()
            query = query.filter(
                User.is_planet_user == True,
                User.planet_expiry_date != None,
                User.planet_expiry_date <= now
            )
        elif planet_filter == 'permanent':
            # 永久会员（有权限但无到期时间）
            query = query.filter(
                User.is_planet_user == True,
                User.planet_expiry_date == None
            )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, 
        per_page=20,
        error_out=False
    )
    
    return render_template('admin/users/list.html', 
                         users=users, 
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         planet_filter=planet_filter)

@user_admin_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def create_user():
    """创建新用户"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'user')
        is_active = request.form.get('is_active') == 'on'
        is_planet_user = request.form.get('is_planet_user') == 'on'
        
        # 验证表单
        errors = []
        
        if not username:
            errors.append('用户名不能为空')
        elif len(username) < 3:
            errors.append('用户名至少3个字符')
        elif User.query.filter_by(username=username).first():
            errors.append('用户名已存在')
        
        if not email:
            errors.append('邮箱不能为空')
        elif '@' not in email:
            errors.append('邮箱格式不正确')
        elif User.query.filter_by(email=email).first():
            errors.append('邮箱已被注册')
        
        if not password:
            errors.append('密码不能为空')
        elif len(password) < 6:
            errors.append('密码至少6个字符')
        
        if role not in ['user', 'admin']:
            errors.append('角色设置错误')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/users/form.html')
        
        try:
            # 创建新用户
            user = User(
                username=username,
                email=email,
                password=password,
                full_name=full_name or username,
                role=role
            )
            user.is_active = is_active
            user.is_planet_user = is_planet_user
            
            # 如果创建时就给予知识星球权限，记录授权信息
            if is_planet_user:
                user.planet_approved_at = get_china_datetime()
                user.planet_approved_by = current_user.id if current_user.is_authenticated else None
                
                # 处理到期时间
                expiry_date_str = request.form.get('planet_expiry_date', '').strip()
                if expiry_date_str:
                    from datetime import datetime
                    try:
                        user.planet_expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
                    except ValueError:
                        errors.append('到期日期格式不正确')
                        flash('到期日期格式不正确', 'error')
                else:
                    # 未填写到期日期，视为永久
                    user.planet_expiry_date = None
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'用户 "{username}" 创建成功！', 'success')
            return redirect(url_for('user_admin.list_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'创建用户失败：{str(e)}', 'error')
    
    return render_template('admin/users/form.html')

@user_admin_bp.route('/<int:user_id>')
@admin_required
def view_user(user_id):
    """查看用户详情"""
    user = User.query.get_or_404(user_id)
    return render_template('admin/users/detail.html', user=user)

@user_admin_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """编辑用户"""
    user = User.query.get_or_404(user_id)
    
    # 防止普通管理员编辑超级管理员
    if user.username == 'admin' and current_user.username != 'admin':
        flash('无权限编辑超级管理员账户', 'error')
        return redirect(url_for('user_admin.list_users'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'user')
        is_active = request.form.get('is_active') == 'on'
        is_planet_user = request.form.get('is_planet_user') == 'on'
        
        # 验证表单
        errors = []
        
        if not username:
            errors.append('用户名不能为空')
        elif len(username) < 3:
            errors.append('用户名至少3个字符')
        elif username != user.username and User.query.filter_by(username=username).first():
            errors.append('用户名已存在')
        
        if not email:
            errors.append('邮箱不能为空')
        elif '@' not in email:
            errors.append('邮箱格式不正确')
        elif email != user.email and User.query.filter_by(email=email).first():
            errors.append('邮箱已被注册')
        
        if role not in ['user', 'admin']:
            errors.append('角色设置错误')
        
        # 防止最后一个管理员被降级
        if user.role == 'admin' and role != 'admin':
            admin_count = User.query.filter_by(role='admin', is_active=True).count()
            if admin_count <= 1:
                errors.append('不能删除最后一个管理员')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('admin/users/form.html', user=user, edit_mode=True)
        
        try:
            # 更新用户信息
            user.username = username
            user.email = email
            user.full_name = full_name or username
            user.role = role
            user.is_active = is_active
            
            # 处理知识星球权限变化
            was_planet_user = user.is_planet_user
            user.is_planet_user = is_planet_user
            
            # 如果权限从无到有，记录授权信息
            if not was_planet_user and is_planet_user:
                user.planet_approved_at = get_china_datetime()
                user.planet_approved_by = current_user.id if current_user.is_authenticated else None
            # 如果权限从有到无，清除授权信息和到期时间
            elif was_planet_user and not is_planet_user:
                user.planet_approved_at = None
                user.planet_expiry_date = None
                # 保留 planet_approved_by 用于记录历史
            
            # 处理到期时间（仅在有权限时处理）
            if is_planet_user:
                expiry_date_str = request.form.get('planet_expiry_date', '').strip()
                if expiry_date_str:
                    from datetime import datetime
                    try:
                        user.planet_expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
                    except ValueError:
                        errors.append('到期日期格式不正确')
                        flash('到期日期格式不正确', 'error')
                        return render_template('admin/users/form.html', user=user, edit_mode=True)
                else:
                    # 未填写到期日期，视为永久
                    user.planet_expiry_date = None
            
            user.updated_at = get_china_datetime()
            
            db.session.commit()
            
            flash(f'用户 "{username}" 更新成功！', 'success')
            return redirect(url_for('user_admin.view_user', user_id=user.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新用户失败：{str(e)}', 'error')
    
    return render_template('admin/users/form.html', user=user, edit_mode=True)

@user_admin_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    """重置用户密码"""
    user = User.query.get_or_404(user_id)
    
    # 防止普通管理员重置超级管理员密码
    if user.username == 'admin' and current_user.username != 'admin':
        return jsonify({'success': False, 'message': '无权限重置超级管理员密码'}), 403
    
    new_password = request.form.get('new_password', '').strip()
    
    if not new_password:
        return jsonify({'success': False, 'message': '新密码不能为空'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': '密码至少6个字符'}), 400
    
    try:
        user.set_password(new_password)
        user.updated_at = get_china_datetime()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'用户 "{user.username}" 的密码已重置'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'密码重置失败：{str(e)}'
        }), 500

@user_admin_bp.route('/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """切换用户激活状态"""
    user = User.query.get_or_404(user_id)
    
    # 防止禁用超级管理员
    if user.username == 'admin':
        return jsonify({'success': False, 'message': '不能禁用超级管理员账户'}), 403
    
    # 防止最后一个管理员被禁用
    if user.role == 'admin' and user.is_active:
        active_admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if active_admin_count <= 1:
            return jsonify({'success': False, 'message': '不能禁用最后一个管理员'}), 403
    
    try:
        user.is_active = not user.is_active
        user.updated_at = get_china_datetime()
        db.session.commit()
        
        status_text = "激活" if user.is_active else "禁用"
        return jsonify({
            'success': True,
            'message': f'用户 "{user.username}" 已{status_text}',
            'new_status': user.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }), 500

@user_admin_bp.route('/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)
    
    # 防止删除超级管理员
    if user.username == 'admin':
        flash('不能删除超级管理员账户', 'error')
        return redirect(url_for('user_admin.list_users'))
    
    # 防止删除最后一个管理员
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if admin_count <= 1:
            flash('不能删除最后一个管理员', 'error')
            return redirect(url_for('user_admin.list_users'))
    
    try:
        username = user.username
        
        # 清理用户相关的数据，避免外键约束错误
        cleanup_user_related_data(user)
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        flash(f'用户 "{username}" 及其相关数据已删除', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'删除用户失败：{str(e)}', 'error')
    
    return redirect(url_for('user_admin.list_users'))

@user_admin_bp.route('/<int:user_id>/revoke-planet-access', methods=['POST'])
@admin_required
def revoke_planet_access(user_id):
    """收回用户的知识星球权限"""
    user = User.query.get_or_404(user_id)
    
    # 检查用户是否有知识星球权限
    if not user.is_planet_user:
        return jsonify({
            'success': False,
            'message': '该用户没有知识星球权限'
        }), 400
    
    try:
        # 记录当前管理员ID
        admin_user = current_user if current_user.is_authenticated else None
        
        # 收回权限
        user.is_planet_user = False
        user.planet_approved_at = None
        # 保留 planet_approved_by 字段用于记录谁批准过，但可以选择清空
        
        db.session.commit()
        
        # 发送邮件通知用户权限被收回
        try:
            from email_service import send_planet_revocation_email
            send_planet_revocation_email(user, admin_user)
        except Exception as email_error:
            print(f"发送邮件失败: {email_error}")
            # 邮件发送失败不影响权限收回操作
        
        # 创建通知
        try:
            from models import Notification
            notification = Notification(
                recipient_id=user.id,
                title="知识星球权限已被收回",
                content=f"您的知识星球权限已被管理员收回。如有疑问，请联系管理员。",
                notification_type="system"
            )
            db.session.add(notification)
            db.session.commit()
        except Exception as notification_error:
            print(f"创建通知失败: {notification_error}")
            # 通知创建失败不影响权限收回操作
        
        return jsonify({
            'success': True,
            'message': f'已成功收回用户 "{user.username}" 的知识星球权限'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'收回权限失败：{str(e)}'
        }), 500