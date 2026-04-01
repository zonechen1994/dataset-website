"""
知识星球OCR功能数据库迁移脚本
执行此脚本以扩展数据库表结构，添加OCR识别和权限到期管理相关字段
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db
from app import create_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def column_exists(table_name, column_name):
    """检查列是否已存在"""
    try:
        result = db.engine.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in result]
        return column_name in columns
    except Exception as e:
        logger.error(f"检查列是否存在时出错: {str(e)}")
        return False

def table_exists(table_name):
    """检查表是否已存在"""
    try:
        result = db.engine.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        )
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"检查表是否存在时出错: {str(e)}")
        return False

def migrate_database():
    """执行数据库迁移"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("开始数据库迁移...")
            
            # ========== 扩展 users 表 ==========
            logger.info("扩展 users 表...")
            
            # 添加 planet_expiry_date 字段
            if not column_exists('users', 'planet_expiry_date'):
                db.engine.execute(
                    "ALTER TABLE users ADD COLUMN planet_expiry_date DATETIME NULL"
                )
                logger.info("✓ 添加字段: users.planet_expiry_date")
            else:
                logger.info("⊙ 字段已存在: users.planet_expiry_date")
            
            # 添加 planet_membership_duration 字段
            if not column_exists('users', 'planet_membership_duration'):
                db.engine.execute(
                    "ALTER TABLE users ADD COLUMN planet_membership_duration INTEGER NULL"
                )
                logger.info("✓ 添加字段: users.planet_membership_duration")
            else:
                logger.info("⊙ 字段已存在: users.planet_membership_duration")
            
            # ========== 扩展 planet_applications 表 ==========
            logger.info("扩展 planet_applications 表...")
            
            # 添加 OCR 相关字段
            ocr_fields = [
                ('ocr_raw_text', 'TEXT'),
                ('ocr_extracted_date', 'DATETIME NULL'),
                ('ocr_confidence', 'FLOAT'),
                ('is_permanent_member', 'BOOLEAN DEFAULT 0'),
                ('date_confirmed_by_user', 'BOOLEAN DEFAULT 0'),
                ('membership_duration', 'INTEGER NULL')
            ]
            
            for field_name, field_type in ocr_fields:
                if not column_exists('planet_applications', field_name):
                    db.engine.execute(
                        f"ALTER TABLE planet_applications ADD COLUMN {field_name} {field_type}"
                    )
                    logger.info(f"✓ 添加字段: planet_applications.{field_name}")
                else:
                    logger.info(f"⊙ 字段已存在: planet_applications.{field_name}")
            
            # ========== 创建 planet_expiry_notifications 表 ==========
            logger.info("创建 planet_expiry_notifications 表...")
            
            if not table_exists('planet_expiry_notifications'):
                db.engine.execute("""
                    CREATE TABLE planet_expiry_notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        notification_type VARCHAR(20) NOT NULL,
                        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expiry_date DATETIME NOT NULL,
                        days_before_expiry INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                logger.info("✓ 创建表: planet_expiry_notifications")
            else:
                logger.info("⊙ 表已存在: planet_expiry_notifications")
            
            # ========== 创建索引 ==========
            logger.info("创建索引...")
            
            try:
                # 检查索引是否已存在
                result = db.engine.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_planet_expiry'"
                )
                if result.fetchone() is None:
                    db.engine.execute(
                        "CREATE INDEX idx_planet_expiry ON users(planet_expiry_date)"
                    )
                    logger.info("✓ 创建索引: idx_planet_expiry")
                else:
                    logger.info("⊙ 索引已存在: idx_planet_expiry")
            except Exception as e:
                logger.warning(f"创建索引 idx_planet_expiry 时出现警告: {str(e)}")
            
            try:
                result = db.engine.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_planet_user_active'"
                )
                if result.fetchone() is None:
                    db.engine.execute(
                        "CREATE INDEX idx_planet_user_active ON users(is_planet_user, planet_expiry_date)"
                    )
                    logger.info("✓ 创建索引: idx_planet_user_active")
                else:
                    logger.info("⊙ 索引已存在: idx_planet_user_active")
            except Exception as e:
                logger.warning(f"创建索引 idx_planet_user_active 时出现警告: {str(e)}")
            
            try:
                result = db.engine.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_expiry_notifications_user'"
                )
                if result.fetchone() is None:
                    db.engine.execute(
                        "CREATE INDEX idx_expiry_notifications_user ON planet_expiry_notifications(user_id, sent_at)"
                    )
                    logger.info("✓ 创建索引: idx_expiry_notifications_user")
                else:
                    logger.info("⊙ 索引已存在: idx_expiry_notifications_user")
            except Exception as e:
                logger.warning(f"创建索引 idx_expiry_notifications_user 时出现警告: {str(e)}")
            
            logger.info("="*60)
            logger.info("✅ 数据库迁移成功完成！")
            logger.info("="*60)
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
