import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Session配置 - 重要：确保线上环境session正常工作
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7天
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login配置
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 30  # 30天
    
    # 数据库配置
    BASE_DIR = Path(__file__).parent
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR}/dataset.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '1684447052@qq.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'suwszetkzymdeadc'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or '1684447052@qq.com'
    MAIL_SUPPRESS_SEND = False  # 在测试环境中可设为True禁用邮件发送
    
    # 管理员邮箱列表
    ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', '1684447052@qq.com').split(',')
    
    # 邮件模板配置
    MAIL_SUBJECT_PREFIX = '[数据集网站] '
    
    # 智谱AI GLM-4V配置
    GLM_API_KEY = os.environ.get('GLM_API_KEY', '')
    
    # 文件上传配置
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'md', 'txt'}
    
    # 分页配置
    DATASETS_PER_PAGE = 6
    
    # 器官分类映射 - 完整的医学器官系统
    ORGAN_CATEGORIES = {
        # 原有分类
        'fubu': '腹部',
        'gutou': '骨头', 
        'neikuijing': '内窥镜',
        'quanshen': '全身',
        
        # 神经系统
        'nabu': '脑部',
        'jisui': '脊髓',
        'shenjing': '周围神经',
        
        # 循环系统
        'xinzang': '心脏',
        'xieguan': '血管',
        'xuexun': '血液循环',
        
        # 呼吸系统
        'fei': '肺部',
        'qiguan': '气管',
        'xiongbu': '胸部',
        
        # 消化系统
        'wei': '胃',
        'gan': '肝脏',
        'dan': '胆囊',
        'yi': '胰腺',
        'chang': '肠道',
        'shidao': '食道',
        
        # 泌尿生殖系统
        'shen': '肾脏',
        'bangguang': '膀胱',
        'qianliexian': '前列腺',
        'zigong': '子宫',
        'luanchao': '卵巢',
        
        # 内分泌系统
        'jiazhuangxian': '甲状腺',
        'shenshangxian': '肾上腺',
        'xiachuitit': '下垂体',
        
        # 感觉器官
        'yan': '眼部',
        'er': '耳部',
        'bi': '鼻部',
        
        # 皮肤及软组织
        'pifu': '皮肤',
        'ruanzhizu': '软组织',
        'ruxian': '乳腺',
        
        # 骨骼肌肉系统
        'gugelei': '骨骼',
        'jirou': '肌肉',
        'guanjie': '关节',
        'jizhu': '脊柱',
        
        # 血液淋巴系统
        'xuexitong': '血液系统',
        'linbajie': '淋巴结',
        'pizang': '脾脏',
        
        # 多器官/系统
        'duoqiguan': '多器官',
        'xitong': '系统性'
    }
    
    # 数据模态分类 - 按大类划分，简化版本
    DATA_MODALITIES = {
        # 医学影像大类
        '医学影像': '医学影像',  # 通用医学影像类型
        'CT': 'CT扫描',
        'MRI': 'MRI磁共振',
        'PET': 'PET扫描',
        'PET/CT': 'PET/CT',
        'X光': 'X射线摄影',  # 统一X光和X Ray
        '超声': '超声检查',
        
        # 内窥镜大类
        '内窥镜': '内窥镜检查',
        
        # 病理学大类（合并所有病理相关）
        '病理学': '病理学检查',
        
        # 实验室检查大类
        '实验室检查': '实验室检查',
        '基因检测': '基因检测',
        
        # 功能检查大类
        '功能检查': '功能检查',
        '心电图': '心电图',
        '脑电图': '脑电图',
        
        # 电子病历大类
        '电子病历': '电子病历',
        
        # 多模态
        '多模态': '多模态数据'
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # 线上环境强制使用安全cookie
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}