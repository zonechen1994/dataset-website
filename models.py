from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from timezone_utils import get_china_datetime
import json

db = SQLAlchemy()

class Dataset(db.Model):
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    organ_category = db.Column(db.String(50))
    dimension = db.Column(db.String(10))
    modality = db.Column(db.String(100))
    task_type = db.Column(db.String(50))
    anatomical_structure = db.Column(db.String(100))
    anatomical_region = db.Column(db.String(100))
    num_classes = db.Column(db.Integer)
    data_volume = db.Column(db.String(50))
    file_format = db.Column(db.String(50))
    official_website = db.Column(db.Text)
    download_link = db.Column(db.Text)
    baidu_pan_link = db.Column(db.Text)  # 百度网盘下载链接
    baidu_pan_password = db.Column(db.String(20))  # 百度网盘提取码
    paper_link = db.Column(db.Text)
    publication_date = db.Column(db.String(20))
    description = db.Column(db.Text)
    visualization_images = db.Column(db.Text)  # JSON格式存储图片路径
    file_structure = db.Column(db.Text)
    citation = db.Column(db.Text)
    image_stats = db.Column(db.Text)  # JSON格式存储图像统计
    label_stats = db.Column(db.Text)  # JSON格式存储标签统计
    created_at = db.Column(db.DateTime, default=get_china_datetime)
    updated_at = db.Column(db.DateTime, default=get_china_datetime, onupdate=get_china_datetime)
    
    # 关联作者
    authors = db.relationship('Author', secondary='dataset_authors', backref='datasets')
    
    def __repr__(self):
        return f'<Dataset {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'organ_category': self.organ_category,
            'dimension': self.dimension,
            'modality': self.modality,
            'task_type': self.task_type,
            'anatomical_structure': self.anatomical_structure,
            'anatomical_region': self.anatomical_region,
            'num_classes': self.num_classes,
            'data_volume': self.data_volume,
            'file_format': self.file_format,
            'official_website': self.official_website,
            'download_link': self.download_link,
            'baidu_pan_link': self.baidu_pan_link,
            'baidu_pan_password': self.baidu_pan_password,
            'paper_link': self.paper_link,
            'publication_date': self.publication_date,
            'description': self.description,
            'visualization_images': json.loads(self.visualization_images) if self.visualization_images else [],
            'file_structure': self.file_structure,
            'citation': self.citation,
            'image_stats': json.loads(self.image_stats) if self.image_stats else {},
            'label_stats': json.loads(self.label_stats) if self.label_stats else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'authors': [author.to_dict() for author in self.authors]
        }

class Author(db.Model):
    __tablename__ = 'authors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    institution = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Author {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'institution': self.institution
        }

# 数据集-作者关联表
dataset_authors = db.Table('dataset_authors',
    db.Column('dataset_id', db.Integer, db.ForeignKey('datasets.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('authors.id'), primary_key=True)
)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description
        }

class Modality(db.Model):
    __tablename__ = 'modalities'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(20), default='其他')  # 分组：医学影像、其他检查等
    
    def __repr__(self):
        return f'<Modality {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category
        }

class TaskType(db.Model):
    __tablename__ = 'task_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<TaskType {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # 'admin' 或 'user'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_china_datetime)
    updated_at = db.Column(db.DateTime, default=get_china_datetime, onupdate=get_china_datetime)
    last_login = db.Column(db.DateTime)
    
    # 知识星球相关字段
    is_planet_user = db.Column(db.Boolean, default=False)  # 是否为知识星球用户
    planet_approved_at = db.Column(db.DateTime)  # 知识星球权限获得时间
    planet_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 审核管理员ID
    planet_expiry_date = db.Column(db.DateTime, nullable=True)  # 知识星球权限到期时间（NULL表示永久）
    planet_membership_duration = db.Column(db.Integer, nullable=True)  # 知识星球会员时长（月数，NULL表示永久）
    
    def __init__(self, username, email, password, full_name=None, role='user'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.full_name = full_name or username
        self.role = role
    
    def set_password(self, password):
        """设置密码（加密存储）"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.role == 'admin'
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = get_china_datetime()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class PlanetApplication(db.Model):
    """知识星球申请表"""
    __tablename__ = 'planet_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_reason = db.Column(db.Text)  # 申请理由
    screenshot_filename = db.Column(db.String(255))  # 购买截图文件名
    status = db.Column(db.String(20), default='pending')  # 申请状态: pending, approved, rejected
    created_at = db.Column(db.DateTime, default=get_china_datetime)
    updated_at = db.Column(db.DateTime, default=get_china_datetime, onupdate=get_china_datetime)
    reviewed_at = db.Column(db.DateTime)  # 审核时间
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 审核管理员ID
    review_comment = db.Column(db.Text)  # 审核备注
    
    # OCR识别相关字段
    ocr_raw_text = db.Column(db.Text)  # OCR识别的原始文本
    ocr_extracted_date = db.Column(db.DateTime, nullable=True)  # OCR提取的到期日期
    ocr_confidence = db.Column(db.Float)  # OCR识别置信度
    is_permanent_member = db.Column(db.Boolean, default=False)  # 是否为永久会员
    date_confirmed_by_user = db.Column(db.Boolean, default=False)  # 用户是否确认了识别的日期
    membership_duration = db.Column(db.Integer, nullable=True)  # 会员时长（月数）
    
    # 关联关系
    user = db.relationship('User', foreign_keys=[user_id], backref='planet_applications')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], post_update=True)
    
    def __repr__(self):
        return f'<PlanetApplication {self.id} - {self.user.username} ({self.status})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'application_reason': self.application_reason,
            'screenshot_filename': self.screenshot_filename,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
            'reviewer': self.reviewer.to_dict() if self.reviewer else None,
            'review_comment': self.review_comment
        }

class Notification(db.Model):
    """消息通知表"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 接收者ID
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 发送者ID
    type = db.Column(db.String(50), nullable=False)  # 通知类型
    title = db.Column(db.String(200), nullable=False)  # 通知标题
    content = db.Column(db.Text)  # 通知内容
    related_id = db.Column(db.Integer)  # 相关记录ID（如申请ID）
    is_read = db.Column(db.Boolean, default=False)  # 是否已读
    created_at = db.Column(db.DateTime, default=get_china_datetime)
    
    # 关联关系
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_notifications')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications', post_update=True)
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.title} (to: {self.recipient.username})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'recipient_id': self.recipient_id,
            'sender_id': self.sender_id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'related_id': self.related_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'recipient': {'username': self.recipient.username, 'full_name': self.recipient.full_name} if self.recipient else None,
            'sender': {'username': self.sender.username, 'full_name': self.sender.full_name} if self.sender else None
        }

class EmailVerificationCode(db.Model):
    """邮箱验证码表"""
    __tablename__ = 'email_verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)  # 邮箱地址
    code = db.Column(db.String(10), nullable=False)  # 验证码
    purpose = db.Column(db.String(20), nullable=False, default='registration')  # 用途：registration, password_reset等
    is_used = db.Column(db.Boolean, default=False)  # 是否已使用
    expires_at = db.Column(db.DateTime, nullable=False)  # 过期时间
    created_at = db.Column(db.DateTime, default=get_china_datetime)
    used_at = db.Column(db.DateTime)  # 使用时间
    
    def __repr__(self):
        return f'<EmailVerificationCode {self.email} - {self.code} ({self.purpose})>'
    
    def is_expired(self):
        """检查是否已过期"""
        return get_china_datetime() > self.expires_at
    
    def is_valid(self):
        """检查验证码是否有效（未使用且未过期）"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        """标记为已使用"""
        self.is_used = True
        self.used_at = get_china_datetime()
        db.session.commit()
    
    @staticmethod
    def cleanup_expired_codes():
        """清理过期的验证码"""
        expired_codes = EmailVerificationCode.query.filter(
            EmailVerificationCode.expires_at < get_china_datetime()
        ).all()
        
        for code in expired_codes:
            db.session.delete(code)
        
        db.session.commit()
        return len(expired_codes)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'code': self.code,
            'purpose': self.purpose,
            'is_used': self.is_used,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }

class PlanetExpiryNotification(db.Model):
    """知识星球权限到期提醒记录表"""
    __tablename__ = 'planet_expiry_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)  # 通知类型: expiring_soon, expired
    sent_at = db.Column(db.DateTime, default=get_china_datetime)
    expiry_date = db.Column(db.DateTime, nullable=False)  # 到期时间
    days_before_expiry = db.Column(db.Integer)  # 到期前几天发送（仅expiring_soon类型）
    
    # 关联关系
    user = db.relationship('User', backref='expiry_notifications')
    
    def __repr__(self):
        return f'<PlanetExpiryNotification {self.id} - {self.user.username} ({self.notification_type})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'days_before_expiry': self.days_before_expiry,
            'user': {'username': self.user.username, 'email': self.user.email} if self.user else None
        }