#!/usr/bin/env python3
"""
服务器调试脚本 - 用于排查500错误
"""

import sys
import os
import traceback
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """测试所有关键模块导入"""
    print("=== 测试模块导入 ===")
    
    try:
        from flask import Flask
        print("✓ Flask 导入成功")
    except Exception as e:
        print(f"✗ Flask 导入失败: {e}")
        return False
    
    try:
        from config import config
        print("✓ config 导入成功")
    except Exception as e:
        print(f"✗ config 导入失败: {e}")
        return False
    
    try:
        from models import db, Dataset, User
        print("✓ models 导入成功")
    except Exception as e:
        print(f"✗ models 导入失败: {e}")
        return False
    
    try:
        from auth_enhanced import admin_required, is_admin
        print("✓ auth_enhanced 导入成功")
    except Exception as e:
        print(f"✗ auth_enhanced 导入失败: {e}")
        return False
    
    return True

def test_database():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    
    try:
        from flask import Flask
        from config import config
        from models import db, User
        
        app = Flask(__name__)
        app.config.from_object(config['default'])
        
        db.init_app(app)
        
        with app.app_context():
            # 测试数据库连接
            users_count = User.query.count()
            print(f"✓ 数据库连接成功，用户数量: {users_count}")
            
            # 检查管理员用户
            admin_users = User.query.filter_by(role='admin').all()
            print(f"✓ 管理员用户数量: {len(admin_users)}")
            for admin in admin_users:
                print(f"  - {admin.username} ({admin.email})")
            
            return True
            
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        traceback.print_exc()
        return False

def test_route_access():
    """测试路由访问"""
    print("\n=== 测试路由访问 ===")
    
    try:
        from app_enhanced import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            with app.app_context():
                # 测试首页
                response = client.get('/')
                print(f"✓ 首页访问: {response.status_code}")
                
                # 测试 /dataset/new (未登录，应该重定向)
                response = client.get('/dataset/new')
                print(f"✓ /dataset/new (未登录): {response.status_code}")
                
                return True
                
    except Exception as e:
        print(f"✗ 路由测试失败: {e}")
        traceback.print_exc()
        return False

def check_file_permissions():
    """检查文件权限"""
    print("\n=== 检查文件权限 ===")
    
    files_to_check = [
        'dataset.db',
        'uploads',
        'static',
        'templates'
    ]
    
    for file_path in files_to_check:
        full_path = current_dir / file_path
        if full_path.exists():
            if full_path.is_file():
                readable = os.access(full_path, os.R_OK)
                writable = os.access(full_path, os.W_OK)
                print(f"✓ {file_path}: 读取={readable}, 写入={writable}")
            else:
                print(f"✓ {file_path}: 目录存在")
        else:
            print(f"✗ {file_path}: 不存在")

def main():
    """主函数"""
    print("服务器错误调试工具")
    print("=" * 50)
    
    all_passed = True
    
    # 测试导入
    if not test_imports():
        all_passed = False
    
    # 测试数据库
    if not test_database():
        all_passed = False
    
    # 测试路由
    if not test_route_access():
        all_passed = False
    
    # 检查权限
    check_file_permissions()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有测试通过")
        print("\n可能的解决方案:")
        print("1. 确保服务器上有管理员用户")
        print("2. 检查防火墙和端口5002是否开放")
        print("3. 查看服务器实际运行日志")
    else:
        print("✗ 发现问题，请查看上述错误信息")
    
    return all_passed

if __name__ == '__main__':
    main()