#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户系统测试脚本
验证用户注册、登录、管理等功能是否正常
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/chenziqiang/Desktop/数据集md样例/dataset_website')

def test_import():
    """测试导入模块"""
    try:
        print("🔍 测试模块导入...")
        
        # 测试基础模块
        from models import User, db
        print("✅ models模块导入成功")
        
        from auth_enhanced import init_login_manager, create_default_admin
        print("✅ auth_enhanced模块导入成功")
        
        from auth_routes import auth_bp
        print("✅ auth_routes模块导入成功")
        
        from user_admin_routes import user_admin_bp  
        print("✅ user_admin_routes模块导入成功")
        
        from app_enhanced import create_app
        print("✅ app_enhanced模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_app_creation():
    """测试应用创建"""
    try:
        print("\n🏗️  测试应用创建...")
        
        from app_enhanced import create_app
        app = create_app('development')
        
        with app.app_context():
            from models import db, User
            
            # 检查数据库表是否创建
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 检查默认管理员是否存在
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print(f"✅ 默认管理员存在: {admin.username} ({admin.email})")
            else:
                print("⚠️  默认管理员不存在，正在创建...")
                from auth_enhanced import create_default_admin
                create_default_admin()
                admin = User.query.filter_by(username='admin').first()
                if admin:
                    print("✅ 默认管理员创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        return False

def test_user_creation():
    """测试用户创建功能"""
    try:
        print("\n👥 测试用户创建...")
        
        from app_enhanced import create_app
        app = create_app('development')
        
        with app.app_context():
            from models import db, User
            
            # 创建测试用户
            test_user = User.query.filter_by(username='testuser').first()
            if test_user:
                print("✅ 测试用户已存在")
            else:
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    password='testpass123',
                    full_name='测试用户',
                    role='user'
                )
                db.session.add(test_user)
                db.session.commit()
                print("✅ 测试用户创建成功")
            
            # 验证密码功能
            if test_user.check_password('testpass123'):
                print("✅ 密码验证功能正常")
            else:
                print("❌ 密码验证功能异常")
                return False
            
            # 验证角色功能
            if not test_user.is_admin():
                print("✅ 用户角色功能正常")
            else:
                print("❌ 用户角色功能异常")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 用户创建测试失败: {e}")
        return False

def test_routes():
    """测试路由注册"""
    try:
        print("\n🛣️  测试路由注册...")
        
        from app_enhanced import create_app
        app = create_app('development')
        
        with app.app_context():
            # 检查路由是否注册
            rules = [str(rule) for rule in app.url_map.iter_rules()]
            
            # 检查关键路由
            required_routes = [
                '/login',
                '/register', 
                '/logout',
                '/profile',
                '/admin/users/',
                '/admin/users/new'
            ]
            
            for route in required_routes:
                if any(route in rule for rule in rules):
                    print(f"✅ 路由已注册: {route}")
                else:
                    print(f"❌ 路由未注册: {route}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ 路由测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 用户系统测试开始")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_import),
        ("应用创建", test_app_creation),
        ("用户创建", test_user_creation),
        ("路由注册", test_routes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n❌ 测试 '{test_name}' 失败！")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！用户系统准备就绪！")
        print("\n🚀 启动命令:")
        print("   python run_enhanced.py")
        print("\n🌐 访问地址:")
        print("   http://localhost:5003")
        print("\n🔑 默认管理员:")
        print("   用户名: admin")
        print("   密码: admin123")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)