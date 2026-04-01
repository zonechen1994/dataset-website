from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_login import login_user, logout_user, current_user, login_required
from models import User, db
from auth_enhanced import authenticate_user, is_admin
from email_service import send_verification_code_email, verify_email_code

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    # 如果用户已经登录，重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        verification_code = request.form.get('verification_code', '').strip()
        
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
        elif password != confirm_password:
            errors.append('两次密码输入不一致')
        
        # 验证邮箱验证码
        if not verification_code:
            errors.append('请输入邮箱验证码')
        elif len(verification_code) != 6 or not verification_code.isdigit():
            errors.append('验证码格式不正确，应为6位数字')
        else:
            # 验证验证码
            verify_result = verify_email_code(email, verification_code, 'registration')
            if not verify_result['success']:
                errors.append(verify_result['message'])
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            # 创建新用户
            user = User(
                username=username,
                email=email,
                password=password,
                full_name=full_name or username,
                role='user'
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败：{str(e)}', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    # 如果用户已经登录，重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('auth/login.html')
        
        # 认证用户
        user = authenticate_user(username, password)
        
        if user:
            # 登录成功
            login_user(user, remember=remember)
            user.update_last_login()
            
            # 兼容旧系统的session
            session['is_admin'] = user.is_admin()
            session['username'] = user.username
            session['user_id'] = user.id
            
            flash(f'欢迎回来，{user.full_name}！', 'success')
            
            # 重定向到目标页面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # 根据角色重定向
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    user_name = current_user.full_name if current_user.is_authenticated else '用户'
    logout_user()
    session.clear()
    
    # 创建响应并清除所有cookie
    response = make_response(redirect(url_for('index')))
    
    # 获取当前环境的安全设置
    from flask import current_app
    secure = current_app.config.get('SESSION_COOKIE_SECURE', False)
    
    # 清除Flask-Login的remember_token cookie
    response.set_cookie('remember_token', '', expires=0, 
                       secure=secure, httponly=True, samesite='Lax')
    
    # 清除session cookie（Flask默认session cookie name是'session'）
    response.set_cookie('session', '', expires=0,
                       secure=secure, httponly=True, samesite='Lax')
    
    # 添加Cache-Control头防止缓存
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    flash(f'再见，{user_name}！', 'info')
    return response

@auth_bp.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        
        # 验证邮箱
        if not email or '@' not in email:
            flash('请输入有效的邮箱地址', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # 检查邮箱是否被其他用户使用
        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash('该邮箱已被其他用户使用', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        try:
            current_user.full_name = full_name or current_user.username
            current_user.email = email
            db.session.commit()
            
            flash('个人资料更新成功！', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)

@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码错误', 'error')
            return render_template('auth/change_password.html')
        
        # 验证新密码
        if len(new_password) < 6:
            flash('新密码至少6个字符', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('两次密码输入不一致', 'error')
            return render_template('auth/change_password.html')
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            
            flash('密码修改成功！', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'密码修改失败：{str(e)}', 'error')
    
    return render_template('auth/change_password.html')