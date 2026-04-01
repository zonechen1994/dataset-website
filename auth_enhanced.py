from flask import session, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, login_user, logout_user, login_required as flask_login_required, current_user
from functools import wraps
import hashlib
import os

# 默认管理员配置 - 生产环境请修改
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'  # 请在生产环境修改！

def init_login_manager(app):
    """初始化登录管理器"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请登录后访问此页面'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    return login_manager

def hash_password(password):
    """密码哈希（兼容旧系统）"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash_value):
    """验证密码（兼容旧系统）"""
    return hash_password(password) == hash_value

def is_logged_in():
    """检查用户是否已登录"""
    # 优先使用Flask-Login的current_user
    if current_user and current_user.is_authenticated:
        return True
    # 兼容旧的session方式
    return session.get('is_admin', False)

def is_admin():
    """检查当前用户是否为管理员"""
    if current_user and current_user.is_authenticated:
        return current_user.is_admin()
    # 兼容旧的session方式
    return session.get('is_admin', False)

def get_current_user():
    """获取当前用户"""
    if current_user and current_user.is_authenticated:
        return current_user
    return None

def admin_required(f):
    """需要管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in() or not is_admin():
            flash('此操作需要管理员权限', 'error')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def planet_required(f):
    """需要知识星球权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # 管理员始终有权限
        if is_admin():
            return f(*args, **kwargs)
        
        # 检查是否有知识星球权限
        if current_user and current_user.is_authenticated:
            if not current_user.is_planet_user:
                flash('此操作需要知识星球权限，请先申请', 'warning')
                return redirect(url_for('planet.apply'))
        else:
            flash('请先登录并申请知识星球权限', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        return f(*args, **kwargs)
    return decorated_function

def has_planet_access():
    """检查当前用户是否有知识星球权限"""
    if not is_logged_in():
        return False
    
    # 管理员始终有权限
    if is_admin():
        return True
    
    # 检查是否有知识星球权限
    if current_user and current_user.is_authenticated:
        return current_user.is_planet_user
    
    return False

def login_required(f):
    """需要登录的装饰器（兼容旧系统）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def verify_admin_credentials(username, password):
    """验证管理员凭据（兼容旧系统）"""
    # 从环境变量获取管理员凭据，如果没有则使用默认值
    admin_username = os.environ.get('ADMIN_USERNAME', DEFAULT_ADMIN_USERNAME)
    admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH', 
                                       hash_password(DEFAULT_ADMIN_PASSWORD))
    
    return (username == admin_username and 
            verify_password(password, admin_password_hash))

def authenticate_user(username, password):
    """用户认证（数据库）"""
    from models import User
    
    # 先检查数据库用户
    user = User.query.filter_by(username=username, is_active=True).first()
    if user and user.check_password(password):
        return user
    
    # 兼容旧的admin认证方式
    if verify_admin_credentials(username, password):
        # 如果admin用户不存在，创建一个
        admin_user = User.query.filter_by(username=username).first()
        if not admin_user:
            from models import db
            admin_user = User(
                username=username,
                email=f"{username}@localhost",
                password=password,
                full_name="系统管理员",
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
        return admin_user
    
    return None

def get_user_role():
    """获取用户角色"""
    if current_user and current_user.is_authenticated:
        return current_user.role
    # 兼容旧的session方式
    if is_logged_in():
        return 'admin'
    return 'visitor'

def create_default_admin():
    """创建默认管理员账户"""
    from models import User, db
    
    try:
        admin_username = os.environ.get('ADMIN_USERNAME', DEFAULT_ADMIN_USERNAME)
        admin_password = os.environ.get('ADMIN_PASSWORD', DEFAULT_ADMIN_PASSWORD)
        
        # 检查admin用户是否存在
        admin_user = User.query.filter_by(username=admin_username).first()
        if not admin_user:
            admin_user = User(
                username=admin_username,
                email=f"{admin_username}@localhost",
                password=admin_password,
                full_name="系统管理员",
                role='admin'
            )
            # admin_user.is_planet_user = True  # 暂时注释，使用属性方式
            db.session.add(admin_user)
            db.session.commit()
            print(f"默认管理员账户已创建：{admin_username}")
        
        return admin_user
        
    except Exception as e:
        print(f"创建默认管理员时发生错误（可能是数据库结构问题）: {e}")
        print("应用将继续启动，请确保数据库结构正确")
        return None