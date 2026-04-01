from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from models import User, PlanetApplication, Notification, db
from auth_enhanced import admin_required
from email_service import send_application_notification_email, send_test_email, send_application_result_email
from datetime import datetime
from timezone_utils import get_china_datetime, get_timestamp_filename
from ocr_service import recognize_planet_screenshot, calculate_membership_duration
import os

planet_bp = Blueprint('planet', __name__, url_prefix='/planet')

def allowed_file(filename):
    """检查文件是否为允许的图片格式"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_screenshot(file):
    """保存购买截图文件"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = get_timestamp_filename()
        filename = timestamp + filename
        
        # 确保目录存在
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'screenshots')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        return filename
    return None

def create_notification(recipient_id, notification_type, title, content, related_id=None, sender_id=None):
    """创建通知"""
    notification = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=notification_type,
        title=title,
        content=content,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def notify_all_admins(title, content, related_id=None, sender_id=None):
    """通知所有管理员"""
    admin_users = User.query.filter_by(role='admin', is_active=True).all()
    for admin in admin_users:
        create_notification(admin.id, 'application_submitted', title, content, related_id, sender_id)

def mark_application_notifications_read(application_id=None, user_id=None, notification_types=None):
    """
    智能标记申请相关通知为已读
    
    Args:
        application_id: 申请ID，标记该申请相关的通知
        user_id: 用户ID，默认为当前用户
        notification_types: 通知类型列表，如 ['application_submitted', 'application_approved']
    """
    if not user_id:
        user_id = current_user.id
    
    query = Notification.query.filter_by(
        recipient_id=user_id,
        is_read=False
    )
    
    # 如果指定了申请ID，只标记该申请相关的通知
    if application_id:
        query = query.filter_by(related_id=application_id)
    
    # 如果指定了通知类型，只标记这些类型的通知
    if notification_types:
        query = query.filter(Notification.type.in_(notification_types))
    
    try:
        notifications = query.all()
        marked_count = 0
        
        for notification in notifications:
            notification.is_read = True
            marked_count += 1
        
        if marked_count > 0:
            db.session.commit()
            
        return marked_count
    except Exception as e:
        db.session.rollback()
        import logging
        logging.error(f"自动标记通知已读失败: {str(e)}")
        return 0

@planet_bp.route('/apply', methods=['GET'])
@login_required
def apply():
    """申请知识星球权限（仅显示表单，POST请求由OCR路由处理）"""
    # 检查用户是否已经是知识星球用户
    if current_user.is_planet_user:
        flash('您已经是知识星球用户，无需重复申请', 'info')
        return redirect(url_for('index'))
    
    # 检查是否有待审核的申请
    existing_application = PlanetApplication.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).first()
    
    if existing_application:
        flash('您已提交申请，正在审核中，请耐心等待', 'info')
        return redirect(url_for('planet.status'))
    
    return render_template('planet/apply.html')

@planet_bp.route('/apply/ocr', methods=['POST'])
@login_required
def ocr_screenshot():
    """识别截图中的到期时间（OCR接口）"""
    try:
        screenshot = request.files.get('screenshot')
        
        if not screenshot or screenshot.filename == '':
            return jsonify({
                'success': False,
                'error': '请上传截图'
            }), 400
        
        if not allowed_file(screenshot.filename):
            return jsonify({
                'success': False,
                'error': '只支持 PNG、JPG、JPEG、GIF、WEBP 格式的图片'
            }), 400
        
        # 保存临时文件
        filename = secure_filename(screenshot.filename)
        timestamp = get_timestamp_filename()
        temp_filename = f'temp_{timestamp}{filename}'
        
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'screenshots')
        os.makedirs(upload_dir, exist_ok=True)
        
        temp_path = os.path.join(upload_dir, temp_filename)
        screenshot.save(temp_path)
        
        # 调用OCR识别
        ocr_result = recognize_planet_screenshot(temp_path)
        
        if not ocr_result['success']:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({
                'success': False,
                'error': ocr_result.get('error', 'OCR识别失败')
            }), 500
        
        # 返回OCR结果（临时文件保留，等待用户确认后再正式保存）
        return jsonify({
            'success': True,
            'ocr_result': {
                'expiry_date': ocr_result['expiry_date'].strftime('%Y-%m-%d') if ocr_result['expiry_date'] else None,
                'is_permanent': ocr_result['is_permanent'],
                'confidence': ocr_result['confidence'],
                'duration_months': ocr_result['duration_months'],
                'raw_text': ocr_result['raw_text']
            },
            'temp_filename': temp_filename  # 用于后续确认时关联
        })
        
    except Exception as e:
        import logging
        logging.error(f"OCR识别异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'OCR识别失败: {str(e)}'
        }), 500

@planet_bp.route('/apply/confirm', methods=['POST'])
@login_required
def confirm_and_submit_application():
    """用户确认OCR结果并提交申请"""
    try:
        # 获取用户确认的数据
        data = request.get_json()
        
        temp_filename = data.get('temp_filename')
        reason = data.get('reason', '').strip()
        expiry_date_str = data.get('expiry_date')
        is_permanent = data.get('is_permanent', False)
        ocr_raw_text = data.get('ocr_raw_text', '')
        ocr_confidence = data.get('ocr_confidence', 0.0)
        
        # 表单验证
        if not reason or len(reason) < 10:
            return jsonify({
                'success': False,
                'error': '申请理由至少需要10个字符'
            }), 400
        
        if not temp_filename:
            return jsonify({
                'success': False,
                'error': '截图文件丢失，请重新上传'
            }), 400
        
        # 将临时文件重命名为正式文件
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'screenshots')
        temp_path = os.path.join(upload_dir, temp_filename)
        
        if not os.path.exists(temp_path):
            return jsonify({
                'success': False,
                'error': '截图文件已过期，请重新上传'
            }), 400
        
        # 正式文件名（移除temp_前缀）
        final_filename = temp_filename.replace('temp_', '')
        final_path = os.path.join(upload_dir, final_filename)
        os.rename(temp_path, final_path)
        
        # 计算会员时长
        membership_duration = None
        ocr_extracted_date = None
        
        if not is_permanent and expiry_date_str:
            from datetime import datetime
            ocr_extracted_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            current_time = get_china_datetime()
            membership_duration = calculate_membership_duration(current_time, ocr_extracted_date)
        
        # 创建申请记录
        application = PlanetApplication(
            user_id=current_user.id,
            application_reason=reason,
            screenshot_filename=final_filename,
            ocr_raw_text=ocr_raw_text,
            ocr_extracted_date=ocr_extracted_date,
            ocr_confidence=ocr_confidence,
            is_permanent_member=is_permanent,
            date_confirmed_by_user=True,
            membership_duration=membership_duration
        )
        
        db.session.add(application)
        db.session.commit()
        
        # 通知所有管理员
        notify_all_admins(
            title=f'新的知识星球权限申请 - {current_user.username}',
            content=f'{current_user.full_name}（{current_user.username}）申请知识星球下载权限',
            related_id=application.id,
            sender_id=current_user.id
        )
        
        # 发送邮件通知管理员
        try:
            admin_url = url_for('planet.admin_view_application', app_id=application.id, _external=True)
            application_data = {
                'user_name': current_user.full_name or current_user.username,
                'username': current_user.username,
                'email': current_user.email or '未提供',
                'reason': reason,
                'application_id': application.id,
                'created_at': application.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'admin_url': admin_url
            }
            send_application_notification_email(application_data)
        except Exception as e:
            import logging
            logging.error(f"邮件发送失败: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': '申请已提交成功，请等待管理员审核',
            'redirect_url': url_for('planet.status')
        })
        
    except Exception as e:
        db.session.rollback()
        import logging
        logging.error(f"申请提交异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'申请提交失败：{str(e)}'
        }), 500

@planet_bp.route('/status')
@login_required
def status():
    """查看申请状态"""
    applications = PlanetApplication.query.filter_by(
        user_id=current_user.id
    ).order_by(PlanetApplication.created_at.desc()).all()
    
    return render_template('planet/status.html', 
                         applications=applications,
                         is_planet_user=current_user.is_planet_user)

@planet_bp.route('/admin/applications')
@admin_required
def admin_list_applications():
    """管理员查看所有申请"""
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    # 访问申请列表时，自动标记申请提交相关的通知为已读
    mark_application_notifications_read(
        notification_types=['application_submitted']
    )
    
    query = PlanetApplication.query.join(User, PlanetApplication.user_id == User.id)
    
    if status_filter:
        query = query.filter(PlanetApplication.status == status_filter)
    
    applications = query.order_by(PlanetApplication.created_at.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    # 统计信息
    stats = {
        'total': PlanetApplication.query.count(),
        'pending': PlanetApplication.query.filter_by(status='pending').count(),
        'approved': PlanetApplication.query.filter_by(status='approved').count(),
        'rejected': PlanetApplication.query.filter_by(status='rejected').count()
    }
    
    return render_template('admin/planet/applications.html',
                         applications=applications,
                         stats=stats,
                         status_filter=status_filter)

@planet_bp.route('/admin/applications/<int:app_id>')
@admin_required
def admin_view_application(app_id):
    """管理员查看申请详情"""
    application = PlanetApplication.query.get_or_404(app_id)
    
    # 查看申请详情时，自动标记该申请相关的通知为已读
    mark_application_notifications_read(application_id=app_id)
    
    return render_template('admin/planet/application_detail.html', application=application)

@planet_bp.route('/admin/applications/<int:app_id>/review', methods=['POST'])
@admin_required
def admin_review_application(app_id):
    """管理员审核申请"""
    application = PlanetApplication.query.get_or_404(app_id)
    
    if application.status != 'pending':
        return jsonify({
            'success': False,
            'message': '该申请已被审核过，无法重复操作'
        }), 400
    
    action = request.form.get('action')  # 'approve' 或 'reject'
    comment = request.form.get('comment', '').strip()
    
    if action not in ['approve', 'reject']:
        return jsonify({
            'success': False,
            'message': '无效的审核操作'
        }), 400
    
    try:
        # 更新申请状态
        application.status = 'approved' if action == 'approve' else 'rejected'
        application.reviewed_at = get_china_datetime()
        application.reviewed_by = current_user.id
        application.review_comment = comment
        
        # 如果通过申请，更新用户权限
        if action == 'approve':
            user = application.user
            user.is_planet_user = True
            user.planet_approved_at = get_china_datetime()
            user.planet_approved_by = current_user.id
            
            # Phase 5: 设置到期时间
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                try:
                    # 解析前端传来的 datetime-local 格式 (YYYY-MM-DDTHH:mm)
                    from datetime import datetime as dt
                    # 直接解析 ISO 格式
                    expiry_date = dt.fromisoformat(expiry_date_str)
                    user.planet_expiry_date = expiry_date
                except (ValueError, TypeError) as e:
                    return jsonify({
                        'success': False,
                        'message': f'到期时间格式错误：{str(e)}'
                    }), 400
            else:
                # 如果未设置到期时间，返回错误
                return jsonify({
                    'success': False,
                    'message': '请设置权限到期时间'
                }), 400
            
            # 通知用户申请通过
            expiry_info = f"到期时间：{user.planet_expiry_date.strftime('%Y年%m月%d日 %H:%M')}" if user.planet_expiry_date else ""
            create_notification(
                recipient_id=user.id,
                notification_type='application_approved',
                title='知识星球权限申请已通过',
                content=f'恭喜！您的知识星球权限申请已通过审核，现在可以下载所有数据集。{expiry_info} {f"审核备注：{comment}" if comment else ""}',
                related_id=application.id,
                sender_id=current_user.id
            )
            
            message = f'用户 {user.username} 的知识星球申请已通过，权限到期时间：{user.planet_expiry_date.strftime("%Y-%m-%d %H:%M") if user.planet_expiry_date else "未设置"}'
        else:
            # 通知用户申请被拒绝
            create_notification(
                recipient_id=application.user.id,
                notification_type='application_rejected',
                title='知识星球权限申请未通过',
                content=f'很抱歉，您的知识星球权限申请未通过审核。{f"审核备注：{comment}" if comment else ""}',
                related_id=application.id,
                sender_id=current_user.id
            )
            
            message = f'用户 {application.user.username} 的知识星球申请已拒绝'
        
        db.session.commit()
        
        # 审核操作完成后，标记该申请相关的所有通知为已读
        mark_application_notifications_read(application_id=app_id)
        
        # 发送邮件通知用户申请结果
        try:
            website_url = url_for('index', _external=True)
            result_data = {
                'user_name': application.user.full_name or application.user.username,
                'username': application.user.username,
                'user_email': application.user.email,
                'application_id': application.id,
                'status': application.status,
                'review_comment': comment,
                'reviewed_at': application.reviewed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'admin_name': current_user.full_name or current_user.username,
                'website_url': website_url
            }
            send_application_result_email(result_data)
        except Exception as e:
            # 邮件发送失败不影响审核流程，只记录日志
            import logging
            logging.error(f"申请结果邮件发送失败: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': message,
            'new_status': application.status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'审核操作失败：{str(e)}'
        }), 500

@planet_bp.route('/admin/notifications')
@admin_required  
def admin_notifications():
    """
    管理员查看通知
    注意：此功能暂时在UI中隐藏，避免与权限申请功能重复
    路由保留以便未来复用，可通过直接访问URL使用
    """
    page = request.args.get('page', 1, type=int)
    unread_only = request.args.get('unread') == '1'
    
    query = Notification.query.filter_by(recipient_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    # 统计未读通知数量
    unread_count = Notification.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template('admin/notifications.html',
                         notifications=notifications,
                         unread_count=unread_count)

@planet_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """标记通知为已读"""
    notification = Notification.query.filter_by(
        id=notif_id,
        recipient_id=current_user.id
    ).first_or_404()
    
    try:
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '通知已标记为已读'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }), 500

@planet_bp.route('/api/notifications/unread-count')
@login_required
def get_unread_count():
    """获取未读通知数量"""
    count = Notification.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})

@planet_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """批量标记所有通知为已读"""
    try:
        unread_notifications = Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).all()
        
        if not unread_notifications:
            return jsonify({
                'success': True,
                'message': '没有未读通知',
                'count': 0
            })
        
        # 批量更新
        for notification in unread_notifications:
            notification.is_read = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已标记 {len(unread_notifications)} 条通知为已读',
            'count': len(unread_notifications)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }), 500

@planet_bp.route('/admin/test-email', methods=['GET', 'POST'])
@admin_required
def test_email():
    """邮件测试功能"""
    if request.method == 'POST':
        recipient = request.form.get('recipient', '').strip()
        
        if not recipient:
            flash('请输入收件人邮箱', 'error')
            return render_template('admin/test_email.html')
        
        try:
            success = send_test_email(recipient)
            if success:
                flash(f'测试邮件已发送到 {recipient}', 'success')
            else:
                flash('邮件发送失败，请检查配置', 'error')
        except Exception as e:
            flash(f'邮件发送异常：{str(e)}', 'error')
    
    return render_template('admin/test_email.html')