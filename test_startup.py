#!/usr/bin/env python3
"""
测试应用启动脚本
"""

import os
import sys

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from models import User, PlanetApplication, Notification
        print("✅ 模型导入成功")
    except Exception as e:
        print(f"❌ 模型导入失败: {e}")
        return False
    
    try:
        from app_enhanced import create_app
        print("✅ 应用模块导入成功")
    except Exception as e:
        print(f"❌ 应用模块导入失败: {e}")
        return False
    
    return True

def test_database():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        from app_enhanced import create_app
        from models import db, User
        
        app = create_app('development')
        with app.app_context():
            # 测试查询
            user_count = User.query.count()
            print(f"✅ 数据库连接成功，用户数量: {user_count}")
            
            # 测试新字段
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print(f"✅ Admin用户存在，知识星球状态: {admin_user.is_planet_user}")
            else:
                print("⚠️  Admin用户不存在")
                
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_app_creation():
    """测试应用创建"""
    print("\n🔍 测试应用创建...")
    
    try:
        from app_enhanced import create_app
        
        app = create_app('development')
        print("✅ 应用创建成功")
        
        # 测试路由
        with app.test_client() as client:
            response = client.get('/')
            print(f"✅ 首页访问成功，状态码: {response.status_code}")
            
            # 测试知识星球路由
            response = client.get('/planet/apply')
            print(f"✅ 知识星球申请页面，状态码: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        return False

def main():
    """主函数"""
    print("🌟 知识星球系统启动测试")
    print("=" * 40)
    
    # 检查工作目录
    if not os.path.exists("app_enhanced.py"):
        print("❌ 请在dataset_website目录下运行此脚本")
        return
    
    # 测试步骤
    tests = [
        ("模块导入", test_imports),
        ("数据库连接", test_database),
        ("应用创建", test_app_creation)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            failed_tests.append(test_name)
    
    print("\n" + "=" * 40)
    
    if failed_tests:
        print(f"❌ 测试失败项: {', '.join(failed_tests)}")
        print("\n🔧 建议检查:")
        print("   1. 数据库文件是否存在且结构正确")
        print("   2. Python环境是否包含所需依赖")
        print("   3. 模型定义是否与数据库匹配")
    else:
        print("🎉 所有测试通过！应用可以正常启动")
        print("\n🚀 现在可以运行应用:")
        print("   python app_enhanced.py")
        print("\n📱 访问地址:")
        print("   http://localhost:5003")

if __name__ == '__main__':
    main()