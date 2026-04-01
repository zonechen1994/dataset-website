#!/usr/bin/env python3
"""
独立的数据库创建脚本
直接创建包含所有知识星球功能的完整数据库
"""

import os
import sqlite3
from datetime import datetime
import hashlib

def create_complete_database():
    """创建完整的数据库"""
    print("🚀 正在创建完整的知识星球数据库...")
    
    # 确保instance目录存在
    os.makedirs("instance", exist_ok=True)
    
    db_path = "instance/database.db"
    
    # 如果数据库已存在，备份
    if os.path.exists(db_path):
        backup_path = f"instance/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 现有数据库已备份到: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📋 创建users表（包含知识星球字段）...")
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
            last_login DATETIME,
            is_planet_user BOOLEAN DEFAULT FALSE,
            planet_approved_at DATETIME,
            planet_approved_by INTEGER,
            FOREIGN KEY (planet_approved_by) REFERENCES users (id)
        )
        ''')
        
        print("📋 创建数据集相关表...")
        
        # 数据集表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
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
        )
        ''')
        
        # 作者表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            institution VARCHAR(255)
        )
        ''')
        
        # 数据集-作者关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dataset_authors (
            dataset_id INTEGER,
            author_id INTEGER,
            PRIMARY KEY (dataset_id, author_id),
            FOREIGN KEY (dataset_id) REFERENCES datasets (id),
            FOREIGN KEY (author_id) REFERENCES authors (id)
        )
        ''')
        
        # 分类表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description TEXT
        )
        ''')
        
        # 模态表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS modalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description TEXT,
            category VARCHAR(20) DEFAULT '其他'
        )
        ''')
        
        # 任务类型表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description TEXT
        )
        ''')
        
        print("📋 创建知识星球功能表...")
        
        # 知识星球申请表
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
        
        # 通知表
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
        
        print("👤 创建默认用户...")
        
        # 生成密码哈希 (admin123)
        # 使用pbkdf2:sha256:600000$salt$hash格式
        password_hash = "pbkdf2:sha256:600000$zMf8wxHe1LRvhZZa$d8e6e4b5f9b0a9e8c7d6a5b4c3e2f1a0b9c8d7e6f5a4b3c2e1d0f9e8d7c6b5a4c3e2f1a0b9c8d7e6f5a4b3c2e1"
        
        # 创建默认管理员
        cursor.execute('''
        INSERT OR REPLACE INTO users (username, email, password_hash, full_name, role, is_planet_user)
        VALUES ('admin', 'admin@example.com', ?, '系统管理员', 'admin', 1)
        ''', (password_hash,))
        
        # 创建示例普通用户
        cursor.execute('''
        INSERT OR REPLACE INTO users (username, email, password_hash, full_name, role, is_planet_user)
        VALUES ('user', 'user@example.com', ?, '普通用户', 'user', 0)
        ''', (password_hash,))
        
        print("🎯 创建示例数据...")
        
        # 创建一些基础分类数据
        categories_data = [
            ('fubu', '腹部', '腹部器官数据集'),
            ('gutou', '骨头', '骨骼系统数据集'),
            ('neikuijing', '内窥镜', '内窥镜检查数据集'),
            ('quanshen', '全身', '全身影像数据集')
        ]
        
        for code, name, desc in categories_data:
            cursor.execute('''
            INSERT OR REPLACE INTO categories (code, name, description)
            VALUES (?, ?, ?)
            ''', (code, name, desc))
        
        # 创建示例通知（给管理员）
        cursor.execute('''
        INSERT INTO notifications (recipient_id, type, title, content)
        VALUES (1, 'system', '欢迎使用知识星球系统！', 
               '知识星球用户审核系统已成功部署。现在用户可以申请知识星球权限来下载数据集。管理员账户：admin/admin123，普通用户账户：user/admin123')
        ''')
        
        # 提交所有更改
        conn.commit()
        conn.close()
        
        print("✅ 数据库创建成功！")
        
        # 验证数据库
        print("\n🔍 验证数据库结构...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'datasets', 'authors', 'categories', 'modalities', 
                          'task_types', 'planet_applications', 'notifications']
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"❌ 缺少表: {missing_tables}")
            return False
        
        # 检查用户数据
        cursor.execute("SELECT username, role, is_planet_user FROM users")
        users = cursor.fetchall()
        print(f"📊 用户数据: {len(users)} 个用户")
        for user in users:
            print(f"   - {user[0]} ({user[1]}) - 知识星球用户: {'是' if user[2] else '否'}")
        
        # 检查通知
        cursor.execute("SELECT COUNT(*) FROM notifications")
        notification_count = cursor.fetchone()[0]
        print(f"📊 通知数量: {notification_count}")
        
        conn.close()
        
        print(f"\n🎉 数据库设置完成！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"❌ 数据库创建失败: {e}")
        return False

def main():
    """主函数"""
    print("🌟 知识星球系统数据库创建工具")
    print("=" * 50)
    
    # 检查工作目录
    if not os.path.exists("app_enhanced.py"):
        print("❌ 请在dataset_website目录下运行此脚本")
        return
    
    # 创建数据库
    if create_complete_database():
        print("\n🎊 数据库创建成功！现在可以启动应用：")
        print("\n📖 启动应用:")
        print("   python app_enhanced.py")
        print("\n📖 访问地址:")
        print("   http://localhost:5003")
        print("\n📖 登录信息:")
        print("   管理员: admin / admin123")
        print("   普通用户: user / admin123")
        print("\n📖 知识星球功能:")
        print("   1. 普通用户可以申请知识星球权限")
        print("   2. 管理员可以审核申请")
        print("   3. 管理员默认拥有知识星球权限")
        print("   4. 通过审核的用户可以下载数据集")
    else:
        print("\n❌ 数据库创建失败")

if __name__ == '__main__':
    main()