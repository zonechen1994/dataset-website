from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
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
    
    @property
    def is_planet_user(self):
        """知识星球用户属性 - 管理员默认拥有权限"""
        if self.role == 'admin':
            return True
        # 这里可以添加从数据库字段读取的逻辑
        # 暂时返回False，等数据库字段添加后再启用
        return False
    
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
            'is_planet_user': self.is_planet_user,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'