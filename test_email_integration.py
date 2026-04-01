#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件集成测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_email_config():
    """测试邮件配置"""
    print("=" * 50)
    print("邮件功能集成测试")
    print("=" * 50)
    
    try:
        from config import config
        mail_config = config['default']
        
        print("📧 邮件配置信息:")
        print(f"  SMTP服务器: {mail_config.MAIL_SERVER}")
        print(f"  端口: {mail_config.MAIL_PORT}")
        print(f"  TLS加密: {mail_config.MAIL_USE_TLS}")
        print(f"  发件人: {mail_config.MAIL_USERNAME}")
        print(f"  管理员邮箱: {mail_config.ADMIN_EMAILS}")
        print()
        
        print("✅ 邮件配置加载成功")
        
    except Exception as e:
        print(f"❌ 邮件配置错误: {str(e)}")
        return False
    
    return True

def test_email_service_import():
    """测试邮件服务模块导入"""
    try:
        from email_service import init_mail, send_test_email, send_application_notification_email
        print("✅ 邮件服务模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 邮件服务模块导入失败: {str(e)}")
        return False

def test_planet_routes_integration():
    """测试planet_routes集成"""
    try:
        from planet_routes import planet_bp
        print("✅ planet_routes邮件集成成功")
        return True
    except Exception as e:
        print(f"❌ planet_routes集成失败: {str(e)}")
        return False

def check_flask_mail_dependency():
    """检查Flask-Mail依赖"""
    try:
        import flask_mail
        print("✅ Flask-Mail已安装")
        return True
    except ImportError:
        print("❌ Flask-Mail未安装")
        print("   请运行: pip install Flask-Mail==0.9.1")
        return False

def main():
    """主测试函数"""
    all_tests_passed = True
    
    # 检查依赖
    if not check_flask_mail_dependency():
        print("\n⚠️  请先安装Flask-Mail依赖:")
        print("   pip install Flask-Mail==0.9.1")
        print("\n然后重新运行此测试脚本")
        return False
    
    # 测试配置
    if not test_email_config():
        all_tests_passed = False
    
    # 测试模块导入
    if not test_email_service_import():
        all_tests_passed = False
    
    # 测试路由集成
    if not test_planet_routes_integration():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 所有测试通过！邮件功能集成成功")
        print("\n📋 下一步操作:")
        print("1. 启动应用: python app.py")
        print("2. 访问邮件测试页面: http://localhost:5002/planet/admin/test-email")
        print("3. 发送测试邮件验证功能")
        print("4. 测试申请流程触发邮件通知")
    else:
        print("❌ 部分测试失败，请检查错误信息并修复")
    print("=" * 50)
    
    return all_tests_passed

if __name__ == "__main__":
    main()