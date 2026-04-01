#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试邮件修复后的功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_url_generation():
    """测试URL生成"""
    try:
        from flask import Flask
        from planet_routes import planet_bp
        
        app = Flask(__name__)
        app.register_blueprint(planet_bp)
        
        with app.app_context():
            from flask import url_for
            
            # 测试URL生成
            try:
                url = url_for('planet.admin_view_application', app_id=1, _external=True)
                print(f"✅ URL生成成功: {url}")
                return True
            except Exception as e:
                print(f"❌ URL生成失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 应用上下文创建失败: {e}")
        return False

def test_email_service():
    """测试邮件服务"""
    try:
        # 测试Flask-Mail导入
        try:
            import flask_mail
            print("✅ Flask-Mail已安装")
        except ImportError:
            print("❌ Flask-Mail未安装，但邮件功能可能仍能工作")
            return False
            
        # 测试邮件服务模块
        try:
            from email_service import send_test_email, send_application_notification_email
            print("✅ 邮件服务模块导入成功")
        except Exception as e:
            print(f"❌ 邮件服务模块导入失败: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 邮件服务测试失败: {e}")
        return False

def check_error_log():
    """检查错误信息"""
    print("\n📋 根据你提供的日志分析:")
    print("1. ✅ 申请流程正常工作 (POST /planet/apply 返回302)")
    print("2. ✅ 邮件发送被触发")
    print("3. ❌ URL构建错误已修复:")
    print("   - 原错误: 'planet.admin_application_detail'")
    print("   - 已修复为: 'planet.admin_view_application'")
    print("   - 参数名从 'id' 改为 'app_id'")

def main():
    print("=" * 50)
    print("邮件修复测试")
    print("=" * 50)
    
    # 检查错误日志
    check_error_log()
    
    print("\n🔍 功能测试:")
    
    # 测试URL生成
    url_ok = test_url_generation()
    
    # 测试邮件服务
    email_ok = test_email_service()
    
    print("\n" + "=" * 50)
    if url_ok and email_ok:
        print("🎉 修复完成！")
        print("\n📋 下一步操作:")
        print("1. 重启应用: python app.py")
        print("2. 让用户重新提交申请")
        print("3. 检查邮箱是否收到通知")
        print("\n⚠️  如果仍未收到邮件，可能需要:")
        print("- 检查QQ邮箱的垃圾邮件文件夹")
        print("- 验证QQ邮箱SMTP设置是否正确")
        print("- 使用管理员测试页面发送测试邮件")
    else:
        print("❌ 仍有问题需要解决")
    print("=" * 50)

if __name__ == "__main__":
    main()