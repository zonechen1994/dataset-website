# -*- coding: utf-8 -*-
"""
邮件发送服务模块
提供邮件发送功能，支持HTML模板和异步发送
"""

import logging
import random
from threading import Thread
from flask import current_app, render_template_string
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from timezone_utils import get_china_datetime, get_current_time_str

# 配置日志
logger = logging.getLogger(__name__)

# Flask-Mail实例
mail = Mail()

def init_mail(app):
    """初始化邮件服务"""
    mail.init_app(app)
    logger.info("邮件服务初始化完成")

def send_async_email(app, msg):
    """异步发送邮件"""
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"邮件发送成功: {msg.subject} -> {msg.recipients}")
        except Exception as e:
            logger.error(f"邮件发送失败: {msg.subject} -> {msg.recipients}, 错误: {str(e)}")

def send_email(subject, recipients, text_body=None, html_body=None, sender=None, async_send=True):
    """
    发送邮件
    
    Args:
        subject (str): 邮件主题
        recipients (list): 收件人列表
        text_body (str): 文本内容
        html_body (str): HTML内容
        sender (str): 发件人，为空时使用默认配置
        async_send (bool): 是否异步发送
    
    Returns:
        bool: 同步发送时返回是否成功，异步发送时返回True
    """
    if not recipients:
        logger.warning("收件人列表为空，跳过邮件发送")
        return False
    
    # 确保recipients是列表
    if isinstance(recipients, str):
        recipients = [recipients]
    
    # 过滤空邮箱
    recipients = [email.strip() for email in recipients if email and email.strip()]
    if not recipients:
        logger.warning("有效收件人列表为空，跳过邮件发送")
        return False
    
    try:
        # 创建邮件消息
        msg = Message(
            subject=current_app.config['MAIL_SUBJECT_PREFIX'] + subject,
            recipients=recipients,
            sender=sender or current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        if text_body:
            msg.body = text_body
        if html_body:
            msg.html = html_body
        
        if async_send:
            # 异步发送
            thread = Thread(target=send_async_email, args=(current_app._get_current_object(), msg))
            thread.start()
            return True
        else:
            # 同步发送
            mail.send(msg)
            logger.info(f"邮件发送成功: {subject} -> {recipients}")
            return True
            
    except Exception as e:
        logger.error(f"邮件发送失败: {subject} -> {recipients}, 错误: {str(e)}")
        return False

def send_application_notification_email(application_data):
    """
    发送申请通知邮件
    
    Args:
        application_data (dict): 申请信息数据
            - user_name: 用户姓名
            - username: 用户名  
            - email: 用户邮箱
            - reason: 申请理由
            - application_id: 申请ID
            - created_at: 申请时间
            - admin_url: 管理后台URL
    """
    
    # 邮件主题
    subject = f"新的知识星球权限申请 - {application_data['user_name']}"
    
    # HTML邮件模板
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>申请通知</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif;
                line-height: 1.6; 
                color: #333; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f8f9fa;
            }
            .container {
                background: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            .header {
                text-align: center;
                border-bottom: 2px solid #667eea;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .header h1 {
                color: #667eea;
                margin: 0;
                font-size: 24px;
            }
            .content {
                margin-bottom: 30px;
            }
            .info-box {
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }
            .info-item {
                margin: 10px 0;
                display: flex;
                align-items: flex-start;
            }
            .info-label {
                font-weight: bold;
                color: #495057;
                min-width: 80px;
                margin-right: 10px;
            }
            .info-value {
                flex: 1;
                word-break: break-word;
            }
            .reason-box {
                background: #e9ecef;
                padding: 15px;
                border-radius: 4px;
                margin: 15px 0;
                border-left: 4px solid #28a745;
            }
            .action-buttons {
                text-align: center;
                margin: 30px 0;
            }
            .btn {
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin: 0 10px;
            }
            .btn:hover {
                background: #5a67d8;
            }
            .footer {
                text-align: center;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
                font-size: 14px;
            }
            .time {
                color: #6c757d;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌟 知识星球权限申请通知</h1>
            </div>
            
            <div class="content">
                <p>尊敬的管理员，您好！</p>
                <p>有用户申请知识星球下载权限，请及时处理。</p>
                
                <div class="info-box">
                    <div class="info-item">
                        <span class="info-label">👤 申请人：</span>
                        <span class="info-value">{{ user_name }} ({{ username }})</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">📧 邮箱：</span>
                        <span class="info-value">{{ email }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">🆔 申请ID：</span>
                        <span class="info-value">#{{ application_id }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">🕒 申请时间：</span>
                        <span class="info-value time">{{ created_at }}</span>
                    </div>
                </div>
                
                <div class="reason-box">
                    <strong>📝 申请理由：</strong><br>
                    {{ reason }}
                </div>
                
                <div class="action-buttons">
                    <a href="{{ admin_url }}" class="btn">🔍 查看详情并处理</a>
                </div>
                
                <p><strong>⚡ 请及时登录管理后台处理该申请！</strong></p>
            </div>
            
            <div class="footer">
                <p>此邮件由人体器官数据集展示网站系统自动发送</p>
                <p>请勿直接回复此邮件</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 文本版本邮件模板（用于不支持HTML的邮件客户端）
    text_template = """
知识星球权限申请通知

申请人：{{ user_name }} ({{ username }})
邮箱：{{ email }}
申请ID：#{{ application_id }}
申请时间：{{ created_at }}

申请理由：
{{ reason }}

请登录管理后台查看详情并处理该申请：
{{ admin_url }}

---
此邮件由人体器官数据集展示网站系统自动发送，请勿直接回复。
    """
    
    # 渲染邮件内容
    html_body = render_template_string(html_template, **application_data)
    text_body = render_template_string(text_template, **application_data)
    
    # 获取管理员邮箱列表
    admin_emails = current_app.config.get('ADMIN_EMAILS', [])
    
    # 发送邮件
    return send_email(
        subject=subject,
        recipients=admin_emails,
        text_body=text_body,
        html_body=html_body,
        async_send=True
    )

def send_test_email(recipient):
    """
    发送测试邮件
    
    Args:
        recipient (str): 收件人邮箱
    
    Returns:
        bool: 是否发送成功
    """
    subject = "邮件服务测试"
    
    html_body = """
    <h2>🎉 邮件服务测试成功！</h2>
    <p>这是一封测试邮件，用于验证邮件发送功能是否正常工作。</p>
    <p>如果您收到这封邮件，说明邮件服务配置正确。</p>
    <hr>
    <p><small>发送时间：{}</small></p>
    """.format(get_current_time_str())
    
    text_body = f"""
邮件服务测试成功！

这是一封测试邮件，用于验证邮件发送功能是否正常工作。
如果您收到这封邮件，说明邮件服务配置正确。

发送时间：{get_current_time_str()}
    """
    
    return send_email(
        subject=subject,
        recipients=[recipient],
        text_body=text_body,
        html_body=html_body,
        async_send=False  # 测试邮件使用同步发送
    )

def send_application_result_email(result_data):
    """
    发送申请处理结果邮件
    
    Args:
        result_data (dict): 申请结果数据
            - user_name: 用户姓名
            - username: 用户名
            - user_email: 用户邮箱
            - application_id: 申请ID
            - status: 申请状态 ('approved' 或 'rejected')
            - review_comment: 审核备注
            - reviewed_at: 审核时间
            - admin_name: 审核管理员姓名
            - website_url: 网站地址
    """
    
    # 根据状态确定邮件主题和内容
    if result_data['status'] == 'approved':
        subject = f"🎉 知识星球权限申请通过 - {result_data['user_name']}"
        status_text = "申请通过"
        status_color = "#28a745"
        status_bg = "rgba(40, 167, 69, 0.1)"
        status_icon = "🎉"
        result_message = "恭喜！您的知识星球权限申请已通过审核"
        next_steps = """
        <li>现在您可以下载所有数据集了</li>
        <li>在数据集详情页面点击下载按钮即可</li>
        <li>感谢您对我们平台的支持！</li>
        """
    else:
        subject = f"📋 知识星球权限申请结果 - {result_data['user_name']}"
        status_text = "申请未通过"
        status_color = "#dc3545"
        status_bg = "rgba(220, 53, 69, 0.1)"
        status_icon = "📋"
        result_message = "很抱歉，您的知识星球权限申请未通过审核"
        next_steps = """
        <li>您可以重新提交申请</li>
        <li>请仔细阅读申请要求</li>
        <li>如有疑问，可以联系管理员</li>
        """
    
    # HTML邮件模板
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>申请审核结果</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif;
                line-height: 1.6; 
                color: #333; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f8f9fa;
            }
            .container {
                background: #ffffff;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }
            .header {
                text-align: center;
                padding-bottom: 25px;
                margin-bottom: 30px;
                border-bottom: 2px solid #667eea;
            }
            .header h1 {
                color: #667eea;
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }
            .status-card {
                background: {{ status_bg }};
                border-left: 5px solid {{ status_color }};
                border-radius: 8px;
                padding: 20px;
                margin: 25px 0;
                text-align: center;
            }
            .status-icon {
                font-size: 48px;
                margin-bottom: 15px;
                display: block;
            }
            .status-text {
                font-size: 24px;
                font-weight: 700;
                color: {{ status_color }};
                margin: 0;
            }
            .result-message {
                font-size: 18px;
                margin: 15px 0;
                color: #495057;
            }
            .info-section {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin: 25px 0;
            }
            .info-item {
                margin: 12px 0;
                display: flex;
                align-items: flex-start;
            }
            .info-label {
                font-weight: 600;
                color: #495057;
                min-width: 100px;
                margin-right: 15px;
            }
            .info-value {
                flex: 1;
                word-break: break-word;
            }
            .comment-section {
                background: #e9ecef;
                border-radius: 8px;
                padding: 18px;
                margin: 25px 0;
                border-left: 4px solid #6c757d;
            }
            .next-steps {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                padding: 20px;
                margin: 25px 0;
            }
            .next-steps h4 {
                margin: 0 0 15px 0;
                font-size: 18px;
            }
            .next-steps ul {
                margin: 0;
                padding-left: 20px;
            }
            .next-steps li {
                margin: 8px 0;
                color: rgba(255, 255, 255, 0.95);
            }
            .website-link {
                text-align: center;
                margin: 30px 0;
            }
            .btn {
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                transition: background 0.3s ease;
            }
            .btn:hover {
                background: #5a67d8;
            }
            .footer {
                text-align: center;
                padding-top: 25px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
                font-size: 14px;
            }
            .time {
                color: #6c757d;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{{ status_icon }} 申请审核结果通知</h1>
            </div>
            
            <div class="status-card" style="background: {{ status_bg }};">
                <span class="status-icon">{{ status_icon }}</span>
                <h2 class="status-text" style="color: {{ status_color }};">{{ status_text }}</h2>
                <p class="result-message">{{ result_message }}</p>
            </div>
            
            <div class="info-section">
                <h4 style="margin-top: 0; color: #495057;">📋 申请信息</h4>
                <div class="info-item">
                    <span class="info-label">申请人：</span>
                    <span class="info-value">{{ user_name }} ({{ username }})</span>
                </div>
                <div class="info-item">
                    <span class="info-label">申请ID：</span>
                    <span class="info-value">#{{ application_id }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">审核时间：</span>
                    <span class="info-value time">{{ reviewed_at }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">审核管理员：</span>
                    <span class="info-value">{{ admin_name }}</span>
                </div>
            </div>
            
            {% if review_comment %}
            <div class="comment-section">
                <h4 style="margin-top: 0; color: #495057;">💬 审核备注</h4>
                <p style="margin: 0;">{{ review_comment }}</p>
            </div>
            {% endif %}
            
            <div class="next-steps">
                <h4>📌 接下来您可以：</h4>
                <ul>
                    {{ next_steps|safe }}
                </ul>
            </div>
            
            <div class="website-link">
                <a href="{{ website_url }}" class="btn">🔗 返回网站</a>
            </div>
            
            <div class="footer">
                <p>此邮件由数据网站系统自动发送</p>
                <p>请勿直接回复此邮件，如有问题请联系管理员</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 文本版本邮件模板
    text_template = """
{{ status_icon }} 知识星球权限申请审核结果

审核结果：{{ status_text }}
{{ result_message }}

申请信息：
- 申请人：{{ user_name }} ({{ username }})
- 申请ID：#{{ application_id }}
- 审核时间：{{ reviewed_at }}
- 审核管理员：{{ admin_name }}

{% if review_comment %}
审核备注：
{{ review_comment }}
{% endif %}

接下来您可以：
{% if status == 'approved' %}
- 现在您可以下载所有数据集了
- 在数据集详情页面点击下载按钮即可
- 感谢您对我们平台的支持！
{% else %}
- 您可以重新提交申请
- 请仔细阅读申请要求
- 如有疑问，可以联系管理员
{% endif %}

网站地址：{{ website_url }}

---
此邮件由数据集展示网站系统自动发送，请勿直接回复。
    """
    
    # 准备模板数据
    template_data = {
        'status_icon': status_icon,
        'status_text': status_text,
        'status_color': status_color,
        'status_bg': status_bg,
        'result_message': result_message,
        'next_steps': next_steps,
        **result_data
    }
    
    # 渲染邮件内容
    html_body = render_template_string(html_template, **template_data)
    text_body = render_template_string(text_template, **template_data)
    
    # 发送邮件给用户
    return send_email(
        subject=subject,
        recipients=[result_data['user_email']],
        text_body=text_body,
        html_body=html_body,
        async_send=True
    )

def send_verification_code_email(email, purpose='registration'):
    """
    发送邮箱验证码邮件
    
    Args:
        email (str): 接收验证码的邮箱地址
        purpose (str): 验证码用途 ('registration' 或 'password_reset')
    
    Returns:
        dict: 包含发送结果的字典
            - success (bool): 是否发送成功
            - code (str): 验证码（仅在成功时返回）
            - message (str): 结果消息
            - expires_in (int): 过期时间（分钟）
    """
    
    # 导入必要的模块
    from models import EmailVerificationCode, db
    
    try:
        # 生成6位随机验证码
        verification_code = str(random.randint(100000, 999999))
        
        # 设置过期时间（15分钟）
        expires_in_minutes = 15
        expires_at = get_china_datetime() + timedelta(minutes=expires_in_minutes)
        
        # 清理该邮箱的旧验证码（同一用途）
        old_codes = EmailVerificationCode.query.filter_by(
            email=email,
            purpose=purpose,
            is_used=False
        ).all()
        
        for old_code in old_codes:
            db.session.delete(old_code)
        
        # 创建新的验证码记录
        verification_record = EmailVerificationCode(
            email=email,
            code=verification_code,
            purpose=purpose,
            expires_at=expires_at
        )
        
        db.session.add(verification_record)
        db.session.commit()
        
        # 根据用途确定邮件内容
        if purpose == 'registration':
            subject = "邮箱验证码 - 用户注册"
            purpose_text = "注册新账户"
            action_text = "完成账户注册"
        else:
            subject = "邮箱验证码 - 密码重置"
            purpose_text = "重置密码"
            action_text = "重置您的密码"
        
        # HTML邮件模板
        html_template = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>邮箱验证码</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif;
                    line-height: 1.6; 
                    color: #333; 
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background-color: #f8f9fa;
                }
                .container {
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                }
                .header {
                    text-align: center;
                    padding-bottom: 25px;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #667eea;
                }
                .header h1 {
                    color: #667eea;
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }
                .verification-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin: 25px 0;
                    text-align: center;
                }
                .code-display {
                    font-size: 32px;
                    font-weight: 700;
                    letter-spacing: 8px;
                    margin: 20px 0;
                    padding: 15px;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    border: 2px dashed rgba(255, 255, 255, 0.5);
                }
                .instructions {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #28a745;
                }
                .warning-box {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 25px 0;
                    color: #856404;
                }
                .expiry-info {
                    text-align: center;
                    background: #e9ecef;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #495057;
                }
                .footer {
                    text-align: center;
                    padding-top: 25px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                    font-size: 14px;
                }
                .highlight {
                    color: #667eea;
                    font-weight: 600;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 邮箱验证码</h1>
                </div>
                
                <p>您好！</p>
                <p>您正在进行<span class="highlight">{{ purpose_text }}</span>操作，请使用以下验证码：</p>
                
                <div class="verification-card">
                    <h3 style="margin: 0 0 15px 0; font-size: 18px;">您的验证码</h3>
                    <div class="code-display">{{ verification_code }}</div>
                    <p style="margin: 15px 0 0 0; opacity: 0.9;">请在 {{ expires_in_minutes }} 分钟内使用</p>
                </div>
                
                <div class="instructions">
                    <h4 style="margin-top: 0; color: #495057;">📋 使用说明：</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>在验证页面输入上述6位数字验证码</li>
                        <li>验证码将在 <strong>{{ expires_in_minutes }} 分钟</strong>后失效</li>
                        <li>每个验证码只能使用一次</li>
                        <li>如果没有进行{{ purpose_text }}操作，请忽略此邮件</li>
                    </ul>
                </div>
                
                <div class="expiry-info">
                    ⏰ <strong>过期时间：</strong>{{ expires_at }}
                </div>
                
                <div class="warning-box">
                    <strong>🛡️ 安全提醒：</strong>
                    请勿将验证码告诉他人，以保护您的账户安全。如果您没有请求此验证码，请忽略此邮件。
                </div>
                
                <div class="footer">
                    <p>此邮件由数据集展示网站系统自动发送</p>
                    <p>请勿直接回复此邮件</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 文本版本邮件模板
        text_template = """
邮箱验证码 - {{ purpose_text }}

您好！

您正在进行{{ purpose_text }}操作，请使用以下验证码：

验证码：{{ verification_code }}

使用说明：
- 在验证页面输入上述6位数字验证码
- 验证码将在 {{ expires_in_minutes }} 分钟后失效（{{ expires_at }}）
- 每个验证码只能使用一次
- 如果没有进行{{ purpose_text }}操作，请忽略此邮件

安全提醒：
请勿将验证码告诉他人，以保护您的账户安全。如果您没有请求此验证码，请忽略此邮件。

---
此邮件由数据集展示网站系统自动发送，请勿直接回复。
        """
        
        # 准备模板数据
        template_data = {
            'verification_code': verification_code,
            'purpose_text': purpose_text,
            'action_text': action_text,
            'expires_in_minutes': expires_in_minutes,
            'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'email': email
        }
        
        # 渲染邮件内容
        html_body = render_template_string(html_template, **template_data)
        text_body = render_template_string(text_template, **template_data)
        
        # 发送邮件
        email_sent = send_email(
            subject=subject,
            recipients=[email],
            text_body=text_body,
            html_body=html_body,
            async_send=False  # 验证码邮件使用同步发送，确保立即发送
        )
        
        if email_sent:
            logger.info(f"验证码邮件发送成功: {email} (用途: {purpose})")
            return {
                'success': True,
                'code': verification_code,
                'message': f'验证码已发送到 {email}',
                'expires_in': expires_in_minutes
            }
        else:
            # 发送失败，删除验证码记录
            db.session.delete(verification_record)
            db.session.commit()
            logger.error(f"验证码邮件发送失败: {email}")
            return {
                'success': False,
                'message': '邮件发送失败，请稍后重试'
            }
            
    except Exception as e:
        # 发生异常，回滚数据库操作
        db.session.rollback()
        logger.error(f"发送验证码邮件异常: {email}, 错误: {str(e)}")
        return {
            'success': False,
            'message': f'发送验证码失败：{str(e)}'
        }

def verify_email_code(email, code, purpose='registration'):
    """
    验证邮箱验证码
    
    Args:
        email (str): 邮箱地址
        code (str): 验证码
        purpose (str): 验证码用途
    
    Returns:
        dict: 验证结果
            - success (bool): 是否验证成功
            - message (str): 结果消息
    """
    
    # 导入必要的模块
    from models import EmailVerificationCode, db
    
    try:
        # 查找验证码记录
        verification_record = EmailVerificationCode.query.filter_by(
            email=email,
            code=code,
            purpose=purpose,
            is_used=False
        ).first()
        
        if not verification_record:
            logger.warning(f"验证码验证失败: {email} - 验证码不存在或已使用")
            return {
                'success': False,
                'message': '验证码无效或已使用'
            }
        
        if verification_record.is_expired():
            logger.warning(f"验证码验证失败: {email} - 验证码已过期")
            return {
                'success': False,
                'message': '验证码已过期，请重新获取'
            }
        
        # 验证成功，标记为已使用
        verification_record.mark_as_used()
        
        logger.info(f"验证码验证成功: {email} (用途: {purpose})")
        return {
            'success': True,
            'message': '验证码验证成功'
        }
        
    except Exception as e:
        logger.error(f"验证邮箱验证码异常: {email}, 错误: {str(e)}")
        return {
            'success': False,
            'message': f'验证失败：{str(e)}'
        }

def send_planet_revocation_email(user, admin_user=None):
    """
    发送知识星球权限收回通知邮件
    
    Args:
        user: 被收回权限的用户对象
        admin_user: 执行收回操作的管理员用户对象（可选）
    
    Returns:
        dict: 发送结果
            - success (bool): 是否发送成功
            - message (str): 结果消息
    """
    
    try:
        # 获取当前时间
        formatted_time = get_current_time_str()
        
        # 构建邮件内容
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>知识星球权限收回通知</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 25px;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #dc3545;
                }}
                .header h1 {{
                    color: #dc3545;
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .header .icon {{
                    font-size: 48px;
                    color: #dc3545;
                    margin-bottom: 15px;
                }}
                .notice-card {{
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin: 25px 0;
                    text-align: center;
                }}
                .notice-title {{
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 15px;
                }}
                .notice-content {{
                    font-size: 16px;
                    line-height: 1.6;
                }}
                .info-section {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #6c757d;
                }}
                .info-section h3 {{
                    color: #495057;
                    margin-top: 0;
                    font-size: 18px;
                }}
                .warning-box {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #856404;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .contact-info {{
                    background: #e3f2fd;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #2196f3;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">⚠️</div>
                    <h1>知识星球权限收回通知</h1>
                </div>
                
                <div class="notice-card">
                    <div class="notice-title">权限已被收回</div>
                    <div class="notice-content">
                        您在数据集管理系统中的知识星球权限已被管理员收回
                    </div>
                </div>
                
                <div class="info-section">
                    <h3>📋 详细信息</h3>
                    <p><strong>用户名：</strong>{user.username}</p>
                    <p><strong>邮箱：</strong>{user.email}</p>
                    <p><strong>收回时间：</strong>{formatted_time}</p>
                    {f'<p><strong>操作管理员：</strong>{admin_user.username}</p>' if admin_user else ''}
                </div>
                
                <div class="warning-box">
                    <strong>⚠️ 权限变更影响：</strong><br>
                    • 您将无法下载需要知识星球权限的数据集<br>
                    • 现有的下载权限立即失效<br>
                    • 如需重新获得权限，请重新申请
                </div>
                
                <div class="contact-info">
                    <h3>📞 联系我们</h3>
                    <p>如果您对此次权限收回有疑问，请通过以下方式联系我们：</p>
                    <p>• 登录系统查看通知详情</p>
                    <p>• 联系系统管理员</p>
                    <p>• 重新提交知识星球权限申请</p>
                </div>
                
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                    <p>人体器官数据集管理系统 © 2024</p>
                    <p>发送时间：{formatted_time}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 构建纯文本内容（作为备用）
        text_content = f"""
知识星球权限收回通知

亲爱的 {user.username}，

您在数据集管理系统中的知识星球权限已被管理员收回。

详细信息：
• 用户名：{user.username}
• 邮箱：{user.email}
• 收回时间：{formatted_time}
{f'• 操作管理员：{admin_user.username}' if admin_user else ''}

权限变更影响：
• 您将无法下载需要知识星球权限的数据集
• 现有的下载权限立即失效
• 如需重新获得权限，请重新申请

如果您对此次权限收回有疑问，请联系系统管理员。

此邮件由系统自动发送，请勿直接回复。
人体器官数据集管理系统 © 2024
发送时间：{formatted_time}
        """
        
        # 发送邮件
        subject = "【重要通知】知识星球权限已被收回"
        
        result = send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if result['success']:
            logger.info(f"权限收回通知邮件发送成功: {user.email}")
            return {
                'success': True,
                'message': '权限收回通知邮件发送成功'
            }
        else:
            logger.error(f"权限收回通知邮件发送失败: {user.email} - {result['message']}")
            return {
                'success': False,
                'message': f'邮件发送失败：{result["message"]}'
            }
            
    except Exception as e:
        logger.error(f"发送权限收回邮件异常: {user.email if user else 'unknown'}, 错误: {str(e)}")
        return {
            'success': False,
            'message': f'发送邮件失败：{str(e)}'
        }


def send_permission_expiring_soon_email(user, days):
    """
    发送知识星球权限即将到期提醒邮件
    
    Args:
        user: 用户对象（包含 username, email, planet_expiry_date）
        days: 提前天数（7, 3, 或 1）
    
    Returns:
        dict: 发送结果
            - success (bool): 是否发送成功
            - message (str): 结果消息
    """
    
    try:
        # 获取当前时间和格式化的到期时间
        current_time = get_china_datetime()
        formatted_time = get_current_time_str()
        expiry_date_str = user.planet_expiry_date.strftime('%Y年%m月%d日 %H:%M')
        
        # 根据剩余天数设置不同的视觉样式
        if days == 7:
            alert_color = "#ff9800"  # 橙色
            alert_bg = "rgba(255, 152, 0, 0.1)"
            urgency_level = "提醒"
            icon = "⏰"
        elif days == 3:
            alert_color = "#ff5722"  # 深橙色
            alert_bg = "rgba(255, 87, 34, 0.1)"
            urgency_level = "重要提醒"
            icon = "⚠️"
        else:  # days == 1
            alert_color = "#f44336"  # 红色
            alert_bg = "rgba(244, 67, 54, 0.1)"
            urgency_level = "紧急提醒"
            icon = "🔔"
        
        # 构建邮件主题
        subject = f"{icon} 知识星球权限即将到期提醒 - {days}天后到期"
        
        # HTML邮件模板
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>权限到期提醒</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 25px;
                    margin-bottom: 30px;
                    border-bottom: 2px solid {alert_color};
                }}
                .header .icon {{
                    font-size: 48px;
                    margin-bottom: 15px;
                }}
                .header h1 {{
                    color: {alert_color};
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .alert-card {{
                    background: {alert_bg};
                    border-left: 5px solid {alert_color};
                    border-radius: 12px;
                    padding: 30px;
                    margin: 25px 0;
                    text-align: center;
                }}
                .urgency-level {{
                    font-size: 14px;
                    color: {alert_color};
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                }}
                .expiry-message {{
                    font-size: 24px;
                    font-weight: 700;
                    color: {alert_color};
                    margin: 15px 0;
                }}
                .days-remaining {{
                    font-size: 48px;
                    font-weight: 700;
                    color: {alert_color};
                    margin: 20px 0;
                }}
                .days-label {{
                    font-size: 16px;
                    color: #6c757d;
                    margin-top: 5px;
                }}
                .info-section {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #6c757d;
                }}
                .info-section h3 {{
                    color: #495057;
                    margin-top: 0;
                    font-size: 18px;
                }}
                .info-item {{
                    margin: 12px 0;
                    font-size: 15px;
                }}
                .info-label {{
                    font-weight: 600;
                    color: #495057;
                    display: inline-block;
                    min-width: 100px;
                }}
                .info-value {{
                    color: #333;
                }}
                .action-section {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 25px;
                    margin: 25px 0;
                }}
                .action-section h3 {{
                    margin: 0 0 15px 0;
                    font-size: 20px;
                }}
                .action-list {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .action-list li {{
                    margin: 10px 0;
                    color: rgba(255, 255, 255, 0.95);
                    line-height: 1.5;
                }}
                .btn-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 14px 32px;
                    background: {alert_color};
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }}
                .btn:hover {{
                    opacity: 0.9;
                    transform: translateY(-2px);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .highlight {{
                    color: {alert_color};
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">{icon}</div>
                    <h1>权限到期提醒</h1>
                </div>
                
                <div class="alert-card">
                    <div class="urgency-level">{urgency_level}</div>
                    <div class="expiry-message">您的知识星球权限即将到期</div>
                    <div class="days-remaining">{days}</div>
                    <div class="days-label">天后到期</div>
                </div>
                
                <div class="info-section">
                    <h3>📋 权限信息</h3>
                    <div class="info-item">
                        <span class="info-label">用户名：</span>
                        <span class="info-value">{user.username}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">邮箱：</span>
                        <span class="info-value">{user.email}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">到期时间：</span>
                        <span class="info-value highlight">{expiry_date_str}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">剩余天数：</span>
                        <span class="info-value highlight">{days} 天</span>
                    </div>
                </div>
                
                <div class="action-section">
                    <h3>💡 如何续期？</h3>
                    <ul class="action-list">
                        <li>请在权限到期前重新提交知识星球权限申请</li>
                        <li>上传最新的知识星球截图（包含到期时间）</li>
                        <li>申请通过后，系统将自动更新您的权限</li>
                        <li>权限到期后将无法下载数据集，请及时续期</li>
                    </ul>
                </div>
                
                <div class="btn-container">
                    <a href="http://your-website-url/planet/apply" class="btn">
                        🔄 立即续期申请
                    </a>
                </div>
                
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                    <p>人体器官数据集管理系统 © 2024</p>
                    <p>发送时间：{formatted_time}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 纯文本版本
        text_content = f"""
知识星球权限即将到期提醒

{urgency_level}！您的知识星球权限即将到期

剩余天数：{days} 天

权限信息：
• 用户名：{user.username}
• 邮箱：{user.email}
• 到期时间：{expiry_date_str}
• 剩余天数：{days} 天

如何续期？
• 请在权限到期前重新提交知识星球权限申请
• 上传最新的知识星球截图（包含到期时间）
• 申请通过后，系统将自动更新您的权限
• 权限到期后将无法下载数据集，请及时续期

立即续期：http://your-website-url/planet/apply

---
此邮件由系统自动发送，请勿直接回复。
人体器官数据集管理系统 © 2024
发送时间：{formatted_time}
        """
        
        # 发送邮件
        result = send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_content,
            html_body=html_content,
            async_send=True  # 异步发送
        )
        
        if result:
            logger.info(f"权限到期提醒邮件发送成功: {user.email} (提前{days}天)")
            return {
                'success': True,
                'message': f'到期提醒邮件发送成功（提前{days}天）'
            }
        else:
            logger.error(f"权限到期提醒邮件发送失败: {user.email}")
            return {
                'success': False,
                'message': '邮件发送失败'
            }
            
    except Exception as e:
        logger.error(f"发送到期提醒邮件异常: {user.email if user else 'unknown'}, 错误: {str(e)}")
        return {
            'success': False,
            'message': f'发送邮件失败：{str(e)}'
        }


def send_permission_expired_email(user):
    """
    发送知识星球权限已到期通知邮件
    
    Args:
        user: 用户对象（包含 username, email, planet_expiry_date）
    
    Returns:
        dict: 发送结果
            - success (bool): 是否发送成功
            - message (str): 结果消息
    """
    
    try:
        # 获取当前时间和格式化的到期时间
        formatted_time = get_current_time_str()
        expiry_date_str = user.planet_expiry_date.strftime('%Y年%m月%d日 %H:%M') if user.planet_expiry_date else '未知'
        
        # 构建邮件主题
        subject = "❌ 知识星球权限已到期通知"
        
        # HTML邮件模板
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>权限到期通知</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 30px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 25px;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #dc3545;
                }}
                .header .icon {{
                    font-size: 48px;
                    color: #dc3545;
                    margin-bottom: 15px;
                }}
                .header h1 {{
                    color: #dc3545;
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }}
                .expired-card {{
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin: 25px 0;
                    text-align: center;
                }}
                .expired-title {{
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 15px;
                }}
                .expired-message {{
                    font-size: 16px;
                    line-height: 1.6;
                    opacity: 0.95;
                }}
                .info-section {{
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #6c757d;
                }}
                .info-section h3 {{
                    color: #495057;
                    margin-top: 0;
                    font-size: 18px;
                }}
                .info-item {{
                    margin: 12px 0;
                    font-size: 15px;
                }}
                .info-label {{
                    font-weight: 600;
                    color: #495057;
                    display: inline-block;
                    min-width: 100px;
                }}
                .info-value {{
                    color: #333;
                }}
                .warning-box {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    color: #856404;
                    border-left: 4px solid #ffc107;
                }}
                .warning-box h4 {{
                    margin: 0 0 10px 0;
                    color: #856404;
                    font-size: 16px;
                }}
                .warning-box ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .warning-box li {{
                    margin: 8px 0;
                }}
                .action-section {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px;
                    padding: 25px;
                    margin: 25px 0;
                }}
                .action-section h3 {{
                    margin: 0 0 15px 0;
                    font-size: 20px;
                }}
                .action-list {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .action-list li {{
                    margin: 10px 0;
                    color: rgba(255, 255, 255, 0.95);
                    line-height: 1.5;
                }}
                .btn-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .btn {{
                    display: inline-block;
                    padding: 14px 32px;
                    background: #dc3545;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }}
                .btn:hover {{
                    background: #c82333;
                    transform: translateY(-2px);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                    color: #6c757d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">❌</div>
                    <h1>权限到期通知</h1>
                </div>
                
                <div class="expired-card">
                    <div class="expired-title">您的知识星球权限已到期</div>
                    <div class="expired-message">
                        您的知识星球权限已于 {expiry_date_str} 到期，<br>
                        系统已自动关闭您的下载权限
                    </div>
                </div>
                
                <div class="info-section">
                    <h3>📋 权限信息</h3>
                    <div class="info-item">
                        <span class="info-label">用户名：</span>
                        <span class="info-value">{user.username}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">邮箱：</span>
                        <span class="info-value">{user.email}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">到期时间：</span>
                        <span class="info-value">{expiry_date_str}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">权限状态：</span>
                        <span class="info-value" style="color: #dc3545; font-weight: 600;">已关闭</span>
                    </div>
                </div>
                
                <div class="warning-box">
                    <h4>⚠️ 权限到期影响：</h4>
                    <ul>
                        <li>您将无法下载需要知识星球权限的数据集</li>
                        <li>现有的下载权限已失效</li>
                        <li>如需继续使用，请重新申请权限</li>
                    </ul>
                </div>
                
                <div class="action-section">
                    <h3>🔄 如何恢复权限？</h3>
                    <ul class="action-list">
                        <li>重新提交知识星球权限申请</li>
                        <li>上传最新的知识星球截图（包含到期时间）</li>
                        <li>等待管理员审核通过</li>
                        <li>审核通过后，即可恢复数据集下载权限</li>
                    </ul>
                </div>
                
                <div class="btn-container">
                    <a href="http://your-website-url/planet/apply" class="btn">
                        📝 立即重新申请
                    </a>
                </div>
                
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿直接回复</p>
                    <p>人体器官数据集管理系统 © 2024</p>
                    <p>发送时间：{formatted_time}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 纯文本版本
        text_content = f"""
知识星球权限已到期通知

您的知识星球权限已于 {expiry_date_str} 到期
系统已自动关闭您的下载权限

权限信息：
• 用户名：{user.username}
• 邮箱：{user.email}
• 到期时间：{expiry_date_str}
• 权限状态：已关闭

权限到期影响：
• 您将无法下载需要知识星球权限的数据集
• 现有的下载权限已失效
• 如需继续使用，请重新申请权限

如何恢复权限？
• 重新提交知识星球权限申请
• 上传最新的知识星球截图（包含到期时间）
• 等待管理员审核通过
• 审核通过后，即可恢复数据集下载权限

立即重新申请：http://your-website-url/planet/apply

---
此邮件由系统自动发送，请勿直接回复。
人体器官数据集管理系统 © 2024
发送时间：{formatted_time}
        """
        
        # 发送邮件
        result = send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_content,
            html_body=html_content,
            async_send=True  # 异步发送
        )
        
        if result:
            logger.info(f"权限到期通知邮件发送成功: {user.email}")
            return {
                'success': True,
                'message': '到期通知邮件发送成功'
            }
        else:
            logger.error(f"权限到期通知邮件发送失败: {user.email}")
            return {
                'success': False,
                'message': '邮件发送失败'
            }
            
    except Exception as e:
        logger.error(f"发送到期通知邮件异常: {user.email if user else 'unknown'}, 错误: {str(e)}")
        return {
            'success': False,
            'message': f'发送邮件失败：{str(e)}'
        }
