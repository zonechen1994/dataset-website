from flask import session, request, redirect, url_for, flash
from functools import wraps
import hashlib
import os

# 默认管理员配置 - 生产环境请修改
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'  # 请在生产环境修改！

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash_value):
    """验证密码"""
    return hash_password(password) == hash_value

def is_logged_in():
    """检查用户是否已登录"""
    return session.get('is_admin', False)

def login_required(f):
    """需要登录的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('此操作需要管理员权限，请先登录', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def verify_admin_credentials(username, password):
    """验证管理员凭据"""
    # 从环境变量获取管理员凭据，如果没有则使用默认值
    admin_username = os.environ.get('ADMIN_USERNAME', DEFAULT_ADMIN_USERNAME)
    admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH', 
                                       hash_password(DEFAULT_ADMIN_PASSWORD))
    
    return (username == admin_username and 
            verify_password(password, admin_password_hash))

def get_user_role():
    """获取用户角色"""
    if is_logged_in():
        return 'admin'
    return 'visitor'