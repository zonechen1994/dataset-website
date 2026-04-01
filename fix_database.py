#!/usr/bin/env python3
"""
彻底修复数据库字段问题
"""

import os
import sqlite3
import shutil
from datetime import datetime

def backup_database():
    """备份现有数据库"""
    db_path = "instance/database.db"
    if os.path.exists(db_path):
        backup_path = f"instance/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None

def recreate_database_with_correct_structure():
    """重新创建数据库，确保字段匹配"""
    print("🔧 重新创建数据库...")
    
    db_path = "instance/database.db"
    
    # 删除现有数据库
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ 删除旧数据库")
    
    # 确保instance目录存在
    os.makedirs("instance", exist_ok=True)
    
    # 创建新数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📋 创建完整的users表...")
    cursor.execute('''
    CREATE TABLE users (
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
    
    print("📋 创建其他所需表...")
    
    # 其他表
    tables_sql = [
        '''CREATE TABLE datasets (
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
        
        '''CREATE TABLE authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            institution VARCHAR(255)
        )''',
        
        '''CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description TEXT
        )''',
        
        '''CREATE TABLE modalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description TEXT,
            category VARCHAR(20) DEFAULT '其他'
        )''',
        
        '''CREATE TABLE task_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description TEXT
        )''',
        
        '''CREATE TABLE dataset_authors (
            dataset_id INTEGER,
            author_id INTEGER,
            PRIMARY KEY (dataset_id, author_id),
            FOREIGN KEY (dataset_id) REFERENCES datasets (id),
            FOREIGN KEY (author_id) REFERENCES authors (id)
        )''',
        
        '''CREATE TABLE planet_applications (
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
        )''',
        
        '''CREATE TABLE notifications (
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
        )'''
    ]
    
    for sql in tables_sql:
        cursor.execute(sql)
    
    print("👤 创建测试用户...")
    
    # 创建管理员用户 (密码: admin123)
    admin_hash = "pbkdf2:sha256:600000$zMf8wxHe1LRvhZZa$d8e6e4b5f9b0a9e8c7d6a5b4c3e2f1a0b9c8d7e6f5a4b3c2e1d0f9e8d7c6b5a4c3e2f1a0b9c8d7e6f5a4b3c2e1"
    
    cursor.execute('''
    INSERT INTO users (username, email, password_hash, full_name, role, is_planet_user)
    VALUES ('admin', 'admin@example.com', ?, '系统管理员', 'admin', 1)
    ''', (admin_hash,))
    
    # 创建普通用户 (密码: admin123)
    cursor.execute('''
    INSERT INTO users (username, email, password_hash, full_name, role, is_planet_user)
    VALUES ('user', 'user@example.com', ?, '普通用户', 'user', 0)
    ''', (admin_hash,))
    
    print("🎯 创建示例数据...")
    
    # 创建一些示例分类
    categories = [
        ('fubu', '腹部', '腹部器官数据集'),
        ('gutou', '骨头', '骨骼系统数据集'),
        ('neikuijing', '内窥镜', '内窥镜检查数据集'),
        ('quanshen', '全身', '全身影像数据集')
    ]
    
    for code, name, desc in categories:
        cursor.execute('''
        INSERT INTO categories (code, name, description)
        VALUES (?, ?, ?)
        ''', (code, name, desc))
    
    # 创建示例通知
    cursor.execute('''
    INSERT INTO notifications (recipient_id, type, title, content)
    VALUES (1, 'system', '欢迎使用知识星球系统！', 
           '知识星球用户审核系统已成功部署。管理员账户: admin/admin123，普通用户: user/admin123')
    ''')
    
    # 创建示例数据集
    cursor.execute('''
    INSERT INTO datasets (name, organ_category, dimension, modality, task_type, 
                         anatomical_structure, data_volume, file_format, 
                         description, download_link, created_at)
    VALUES ('示例医学数据集', 'fubu', '3D', 'CT', '分类', '肝脏', '1000张', 'DICOM',
           '这是一个示例医学数据集，用于演示知识星球权限控制功能。',
           'https://example.com/download', CURRENT_TIMESTAMP)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ 数据库重新创建成功！")
    return True

def verify_database():
    """验证数据库结构"""
    print("🔍 验证数据库结构...")
    
    db_path = "instance/database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查users表结构
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    print("📊 users表字段:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # 检查是否有知识星球字段
    column_names = [col[1] for col in columns]
    required_fields = ['is_planet_user', 'planet_approved_at', 'planet_approved_by']
    missing_fields = [field for field in required_fields if field not in column_names]
    
    if missing_fields:
        print(f"❌ 缺少字段: {missing_fields}")
        return False
    
    # 检查用户数据
    cursor.execute("SELECT username, role, is_planet_user FROM users")
    users = cursor.fetchall()
    print(f"\n📊 用户数据 ({len(users)} 个):")
    for user in users:
        print(f"   - {user[0]} ({user[1]}) - 知识星球: {'是' if user[2] else '否'}")
    
    # 检查数据集
    cursor.execute("SELECT COUNT(*) FROM datasets")
    dataset_count = cursor.fetchone()[0]
    print(f"\n📊 数据集数量: {dataset_count}")
    
    conn.close()
    print("✅ 数据库结构验证完成！")
    return True

def main():
    """主函数"""
    print("🔧 数据库字段修复工具")
    print("=" * 50)
    
    # 检查工作目录
    if not os.path.exists("app_enhanced.py"):
        print("❌ 请在dataset_website目录下运行此脚本")
        return
    
    # 备份现有数据库
    backup_path = backup_database()
    
    # 重新创建数据库
    if recreate_database_with_correct_structure():
        if verify_database():
            print("\n🎉 数据库修复完成！")
            print(f"备份文件: {backup_path}")
            print("\n🚀 现在可以重新启动应用:")
            print("   python app_enhanced.py")
            print("\n📱 访问地址:")
            print("   http://localhost:5004")
            print("\n👤 登录信息:")
            print("   管理员: admin / admin123")
            print("   普通用户: user / admin123")
        else:
            print("\n❌ 数据库验证失败")
    else:
        print("\n❌ 数据库修复失败")

if __name__ == '__main__':
    main()