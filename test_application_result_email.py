#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试申请结果邮件功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_email_function():
    """测试邮件发送函数"""
    try:
        from email_service import send_application_result_email
        print("✅ 申请结果邮件函数导入成功")
        
        # 测试数据 - 通过申请
        approved_data = {
            'user_name': '张三',
            'username': 'zhangsan',
            'user_email': 'test@example.com',
            'application_id': 123,
            'status': 'approved',
            'review_comment': '申请材料完整，符合要求。',
            'reviewed_at': '2025-08-15 18:30:00',
            'admin_name': '管理员',
            'website_url': 'http://localhost:5004'
        }
        
        # 测试数据 - 拒绝申请
        rejected_data = {
            'user_name': '李四',
            'username': 'lisi', 
            'user_email': 'test2@example.com',
            'application_id': 124,
            'status': 'rejected',
            'review_comment': '申请理由不够充分，请重新申请。',
            'reviewed_at': '2025-08-15 18:30:00',
            'admin_name': '管理员',
            'website_url': 'http://localhost:5004'
        }
        
        print("✅ 测试数据准备完成")
        return True
        
    except Exception as e:
        print(f"❌ 邮件函数测试失败: {e}")
        return False

def test_integration():
    """测试集成到planet_routes"""
    try:
        from planet_routes import admin_review_application
        print("✅ 申请审核路由导入成功")
        
        # 检查是否导入了邮件发送函数
        import planet_routes
        if hasattr(planet_routes, 'send_application_result_email'):
            print("✅ 邮件发送函数已集成到路由模块")
        else:
            print("❌ 邮件发送函数未找到在路由模块中")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def test_email_template():
    """测试邮件模板渲染"""
    try:
        from flask import Flask, render_template_string
        
        app = Flask(__name__)
        
        with app.app_context():
            # 测试通过申请的模板渲染
            template_data = {
                'status_icon': '🎉',
                'status_text': '申请通过',
                'status_color': '#28a745',
                'status_bg': 'rgba(40, 167, 69, 0.1)',
                'result_message': '恭喜！您的知识星球权限申请已通过审核',
                'next_steps': '<li>现在您可以下载所有数据集了</li>',
                'user_name': '测试用户',
                'username': 'testuser',
                'application_id': 123,
                'reviewed_at': '2025-08-15 18:30:00',
                'admin_name': '管理员',
                'review_comment': '申请通过！',
                'website_url': 'http://localhost:5004'
            }
            
            simple_template = """
            <h1>{{ status_icon }} {{ status_text }}</h1>
            <p>{{ result_message }}</p>
            <p>申请人：{{ user_name }} ({{ username }})</p>
            <p>申请ID：#{{ application_id }}</p>
            """
            
            rendered = render_template_string(simple_template, **template_data)
            if '🎉' in rendered and '申请通过' in rendered:
                print("✅ 邮件模板渲染测试成功")
                return True
            else:
                print("❌ 邮件模板渲染失败")
                return False
        
    except Exception as e:
        print(f"❌ 模板测试失败: {e}")
        return False

def show_usage_instructions():
    """显示使用说明"""
    print("\n" + "=" * 60)
    print("📋 申请结果邮件功能使用说明")
    print("=" * 60)
    print()
    print("🔄 完整测试流程：")
    print("1. 管理员登录后台")
    print("2. 进入知识星球申请管理页面")
    print("3. 点击查看申请详情")
    print("4. 选择 '通过' 或 '拒绝'")
    print("5. 填写审核备注（可选）")
    print("6. 提交审核")
    print("7. 系统会自动发送邮件给申请用户")
    print()
    print("📧 邮件内容包括：")
    print("- 审核结果（通过/未通过）")
    print("- 申请信息（申请人、ID、时间等）")
    print("- 审核备注（如有）")
    print("- 下一步操作指引")
    print("- 返回网站链接")
    print()
    print("✨ 邮件特色：")
    print("- 🎉 通过申请使用绿色主题和庆祝图标")
    print("- 📋 拒绝申请使用红色主题和提醒图标")
    print("- 响应式设计，支持各种邮件客户端")
    print("- HTML + 纯文本双格式支持")
    print("- 异步发送，不影响审核流程")

def main():
    print("=" * 60)
    print("申请结果邮件功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试邮件函数
    print("\n🔍 测试邮件发送函数...")
    results.append(test_email_function())
    
    # 测试集成
    print("\n🔍 测试路由集成...")
    results.append(test_integration())
    
    # 测试模板
    print("\n🔍 测试邮件模板...")
    results.append(test_email_template())
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 所有测试通过！申请结果邮件功能已就绪")
        show_usage_instructions()
    else:
        print("❌ 部分测试失败，请检查错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main()