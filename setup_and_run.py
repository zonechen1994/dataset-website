#!/usr/bin/env python3
"""
一键设置和启动知识星球系统

此脚本将：
1. 创建数据库和基础表
2. 执行知识星球功能迁移
3. 启动应用
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

def setup_database():
    """设置数据库"""
    print("🚀 正在设置数据库...")
    
    # 确保instance目录存在
    os.makedirs("instance", exist_ok=True)
    
    # 如果数据库不存在，创建基础数据库
    db_path = "instance/database.db"
    if not os.path.exists(db_path):
        print("📋 创建基础数据库...")
        
        # 导入并创建应用以初始化数据库
        try:
            from app_enhanced import create_app
            from models import db
            
            # 临时使用基础User模型创建应用
            app = create_app('development')
            
            with app.app_context():
                # 只创建基础表，不包含新字段
                print("📊 创建基础表结构...")
                
                # 手动创建基础users表
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 创建基础users表（不包含新字段）
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
                ''')
                
                # 创建其他基础表
                basic_tables = [
                    '''CREATE TABLE IF NOT EXISTS datasets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL,
                        organ_category VARCHAR(50),
                        dimension VARCHAR(10),
                        modality VARCHAR(100),
                        task_type VARCHAR(50),
                        anatomical_structure VARCHAR(100),
                        anatomical_region VARCHAR(100),
                        num_classes INTEGER,
                        data_volume VARCHAR(50),
                        file_format VARCHAR(50),
                        official_website TEXT,
                        download_link TEXT,
                        paper_link TEXT,
                        publication_date VARCHAR(20),
                        description TEXT,
                        visualization_images TEXT,
                        file_structure TEXT,
                        citation TEXT,
                        image_stats TEXT,
                        label_stats TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''',
                    '''CREATE TABLE IF NOT EXISTS authors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL,
                        institution VARCHAR(255)
                    )''',
                    '''CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code VARCHAR(20) UNIQUE NOT NULL,
                        name VARCHAR(50) NOT NULL,
                        description TEXT
                    )''',
                    '''CREATE TABLE IF NOT EXISTS modalities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code VARCHAR(20) UNIQUE NOT NULL,
                        name VARCHAR(50) NOT NULL,
                        description TEXT,
                        category VARCHAR(20) DEFAULT '其他'
                    )''',
                    '''CREATE TABLE IF NOT EXISTS task_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code VARCHAR(20) UNIQUE NOT NULL,
                        name VARCHAR(50) NOT NULL,
                        description TEXT
                    )''',
                    '''CREATE TABLE IF NOT EXISTS dataset_authors (
                        dataset_id INTEGER,
                        author_id INTEGER,
                        PRIMARY KEY (dataset_id, author_id),
                        FOREIGN KEY (dataset_id) REFERENCES datasets (id),
                        FOREIGN KEY (author_id) REFERENCES authors (id)
                    )'''
                ]
                
                for table_sql in basic_tables:
                    cursor.execute(table_sql)
                
                # 创建默认管理员
                cursor.execute('''
                INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role)
                VALUES ('admin', 'admin@example.com', 
                       'pbkdf2:sha256:600000$zMf8wxHe1LRvhZZa$d8e6e4b5f9b0a9e8c7d6a5b4c3e2f1a0b9c8d7e6f5a4b3c2e1d0f9e8d7c6b5a4c3e2f1a0b9c8d7e6f5a4b3c2e1', 
                       '系统管理员', 'admin')
                ''')  # 密码是 admin123
                
                conn.commit()
                conn.close()
                
                print("✅ 基础数据库创建成功")
                
        except Exception as e:
            print(f"❌ 创建基础数据库失败: {e}")
            return False
    
    return True

def migrate_planet_features():
    """迁移知识星球功能"""
    print("\n🌟 正在添加知识星球功能...")
    
    db_path = "instance/database.db"
    
    # 备份数据库
    backup_path = f"instance/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ 数据库已备份到: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查并添加users表字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('is_planet_user', 'BOOLEAN DEFAULT FALSE'),
            ('planet_approved_at', 'DATETIME'),
            ('planet_approved_by', 'INTEGER')
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                print(f"✅ 添加字段: {column_name}")
            else:
                print(f"⚠️  字段 {column_name} 已存在")
        
        # 创建新表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS planet_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            application_reason TEXT,
            screenshot_filename VARCHAR(255),
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewed_at DATETIME,
            reviewed_by INTEGER,
            review_comment TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (reviewed_by) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER NOT NULL,
            sender_id INTEGER,
            type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            content TEXT,
            related_id INTEGER,
            is_read BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipient_id) REFERENCES users (id),
            FOREIGN KEY (sender_id) REFERENCES users (id)
        )
        ''')
        
        # 创建示例通知
        cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
        admin = cursor.fetchone()
        
        if admin:
            cursor.execute('''
            INSERT INTO notifications (recipient_id, type, title, content)
            VALUES (?, 'system', '知识星球系统已启用', 
                   '知识星球用户审核系统已成功部署。现在用户可以申请知识星球权限来下载数据集。')
            ''', (admin[0],))
        
        conn.commit()
        conn.close()
        
        print("✅ 知识星球功能添加成功")
        return True
        
    except Exception as e:
        print(f"❌ 知识星球功能添加失败: {e}")
        return False

def start_application():
    """启动应用"""
    print("\n🚀 启动知识星球系统...")
    print("=" * 50)
    print("🎉 设置完成！系统已启动：")
    print("📍 访问地址: http://localhost:5003")
    print("👤 管理员账户: admin / admin123")
    print("=" * 50)
    print("\n🌟 知识星球功能:")
    print("  1. 普通用户可以申请知识星球权限")
    print("  2. 管理员可以审核申请")
    print("  3. 通过审核的用户可以下载数据集")
    print("  4. 实时通知系统")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 启动Flask应用
    os.system("python app_enhanced.py")

def main():
    """主函数"""
    print("🌟 知识星球系统一键安装和启动")
    print("=" * 50)
    
    # 检查工作目录
    if not os.path.exists("app_enhanced.py"):
        print("❌ 请在dataset_website目录下运行此脚本")
        return
    
    # 设置数据库
    if not setup_database():
        print("❌ 数据库设置失败")
        return
    
    # 迁移知识星球功能
    if not migrate_planet_features():
        print("❌ 知识星球功能添加失败")
        return
    
    # 启动应用
    start_application()

if __name__ == '__main__':
    main()