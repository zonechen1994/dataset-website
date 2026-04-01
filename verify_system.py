"""
知识星球权限管理系统 - 部署前快速验证脚本
"""
import sys
import os

def verify_imports():
    """验证关键包导入"""
    print("\n" + "="*60)
    print("1. 验证依赖包安装")
    print("="*60)
    
    all_ok = True
    
    try:
        import zhipuai
        print("✅ zhipuai 已安装 (版本: {})".format(getattr(zhipuai, '__version__', '未知')))
    except ImportError:
        print("❌ zhipuai 未安装 - 请运行: pip install zhipuai")
        all_ok = False
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        print("✅ APScheduler 已安装")
    except ImportError:
        print("❌ APScheduler 未安装 - 请运行: pip install APScheduler==3.10.4")
        all_ok = False
    
    try:
        from dateutil.relativedelta import relativedelta
        print("✅ python-dateutil 已安装")
    except ImportError:
        print("❌ python-dateutil 未安装 - 请运行: pip install python-dateutil==2.8.2")
        all_ok = False
    
    try:
        from flask_mail import Mail
        print("✅ Flask-Mail 已安装")
    except ImportError:
        print("❌ Flask-Mail 未安装 - 请运行: pip install Flask-Mail==0.9.1")
        all_ok = False
    
    return all_ok

def verify_modules():
    """验证项目模块"""
    print("\n" + "="*60)
    print("2. 验证项目模块完整性")
    print("="*60)
    
    modules = [
        'models',
        'ocr_service',
        'planet_routes',
        'email_service',
        'scheduler_tasks',
        'timezone_utils'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}.py 可正常导入")
        except Exception as e:
            print(f"❌ {module}.py 导入失败: {e}")
            all_ok = False
    
    return all_ok

def verify_database():
    """验证数据库表结构"""
    print("\n" + "="*60)
    print("3. 验证数据库表结构")
    print("="*60)
    
    try:
        from app import create_app
        from models import db, User, PlanetApplication, PlanetExpiryNotification
        
        app = create_app()
        with app.app_context():
            # 检查用户表扩展字段
            inspector = db.inspect(db.engine)
            
            # 检查 users 表
            if 'users' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                required_fields = ['planet_expiry_date', 'planet_membership_duration']
                missing_fields = [f for f in required_fields if f not in columns]
                
                if missing_fields:
                    print(f"❌ Users 表缺少字段: {', '.join(missing_fields)}")
                    print("   请运行: python migrate_planet_ocr.py")
                    return False
                else:
                    print("✅ Users 表字段完整")
            else:
                print("❌ Users 表不存在")
                return False
            
            # 检查 planet_applications 表
            if 'planet_applications' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('planet_applications')]
                
                required_fields = [
                    'ocr_raw_text',
                    'ocr_extracted_date',
                    'ocr_confidence',
                    'is_permanent_member',
                    'date_confirmed_by_user',
                    'membership_duration'
                ]
                missing_fields = [f for f in required_fields if f not in columns]
                
                if missing_fields:
                    print(f"❌ PlanetApplications 表缺少字段: {', '.join(missing_fields)}")
                    print("   请运行: python migrate_planet_ocr.py")
                    return False
                else:
                    print("✅ PlanetApplications 表字段完整")
            else:
                print("❌ PlanetApplications 表不存在")
                return False
            
            # 检查 planet_expiry_notifications 表
            if 'planet_expiry_notifications' in inspector.get_table_names():
                print("✅ PlanetExpiryNotifications 表存在")
            else:
                print("❌ PlanetExpiryNotifications 表不存在")
                print("   请运行: python migrate_planet_ocr.py")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_env_config():
    """验证环境配置"""
    print("\n" + "="*60)
    print("4. 验证环境配置")
    print("="*60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    all_ok = True
    
    # 检查 GLM_API_KEY
    glm_key = os.getenv('GLM_API_KEY')
    if glm_key:
        print(f"✅ GLM_API_KEY 已配置 (长度: {len(glm_key)})")
    else:
        print("⚠️ GLM_API_KEY 未配置 - OCR识别功能将不可用")
        print("   请在 .env 文件中添加: GLM_API_KEY=your_api_key")
        all_ok = False
    
    # 检查邮件配置
    mail_server = os.getenv('MAIL_SERVER')
    if mail_server:
        print(f"✅ MAIL_SERVER 已配置: {mail_server}")
    else:
        print("⚠️ MAIL_SERVER 未配置 - 邮件功能将不可用")
        all_ok = False
    
    mail_username = os.getenv('MAIL_USERNAME')
    if mail_username:
        print(f"✅ MAIL_USERNAME 已配置: {mail_username}")
    else:
        print("⚠️ MAIL_USERNAME 未配置")
        all_ok = False
    
    return all_ok

def verify_static_files():
    """验证静态文件"""
    print("\n" + "="*60)
    print("5. 验证静态文件")
    print("="*60)
    
    example_image = 'static/images/planet/example.png'
    if os.path.exists(example_image):
        size = os.path.getsize(example_image)
        print(f"✅ 示例图片存在: {example_image} ({size} bytes)")
        return True
    else:
        print(f"❌ 示例图片缺失: {example_image}")
        return False

def main():
    """主验证流程"""
    print("\n" + "="*60)
    print("知识星球权限管理系统 - 部署前验证")
    print("版本: v2.1.0 (Phase 1-6A)")
    print("="*60)
    
    results = []
    
    # 1. 验证依赖包
    results.append(("依赖包", verify_imports()))
    
    # 2. 验证项目模块
    results.append(("项目模块", verify_modules()))
    
    # 3. 验证数据库
    results.append(("数据库结构", verify_database()))
    
    # 4. 验证环境配置
    results.append(("环境配置", verify_env_config()))
    
    # 5. 验证静态文件
    results.append(("静态文件", verify_static_files()))
    
    # 总结
    print("\n" + "="*60)
    print("验证结果总结")
    print("="*60)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有验证通过！系统准备就绪")
        print("="*60)
        print("\n下一步:")
        print("1. 运行测试脚本:")
        print("   - python test_scheduler.py  # 测试定时任务")
        print("   - python test_expiry_emails.py  # 测试邮件发送")
        print("\n2. 手动测试:")
        print("   - 完整申请流程测试")
        print("   - 管理员审核流程测试")
        print("\n3. 启动应用:")
        print("   - python app.py")
        print("\n4. 开启用户测试")
        return 0
    else:
        print("❌ 验证失败，请修复上述问题后重试")
        print("="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
