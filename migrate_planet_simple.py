#!/usr/bin/env python3
"""
简化的知识星球功能数据库迁移脚本

此脚本直接操作SQLite数据库，避免模型加载问题
"""

import os
import sqlite3
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    print("🚀 开始知识星球功能数据库迁移...")
    
    # 数据库文件路径
    db_path = "instance/database.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在，请先启动应用创建数据库")
        return False
    
    # 备份数据库
    backup_path = f"instance/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ 数据库已备份到: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📋 检查并添加users表字段...")
        
        # 检查users表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 添加知识星球相关字段
        new_columns = [
            ('is_planet_user', 'BOOLEAN DEFAULT FALSE'),
            ('planet_approved_at', 'DATETIME'),
            ('planet_approved_by', 'INTEGER')
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                    print(f"✅ 添加字段: {column_name}")
                except Exception as e:
                    print(f"❌ 添加字段 {column_name} 失败: {e}")
                    return False
            else:
                print(f"⚠️  字段 {column_name} 已存在")
        
        print("\n📋 创建planet_applications表...")
        
        # 创建planet_applications表
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
        print("✅ planet_applications表创建成功")
        
        print("\n📋 创建notifications表...")
        
        # 创建notifications表
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
        print("✅ notifications表创建成功")
        
        # 提交更改
        conn.commit()
        
        # 验证迁移结果
        print("\n🔍 验证迁移结果...")
        
        # 检查users表新字段
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = ['is_planet_user', 'planet_approved_at', 'planet_approved_by']
        missing_columns = [col for col in required_columns if col not in user_columns]
        
        if missing_columns:
            print(f"❌ users表缺少字段: {missing_columns}")
            return False
        else:
            print("✅ users表字段验证成功")
        
        # 检查新表是否存在
        tables_to_check = ['planet_applications', 'notifications']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables_to_check:
            if table in existing_tables:
                print(f"✅ 表 {table} 验证成功")
            else:
                print(f"❌ 表 {table} 不存在")
                return False
        
        # 创建示例通知（如果有管理员用户）
        print("\n🎯 创建示例通知...")
        cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
        admin = cursor.fetchone()
        
        if admin:
            cursor.execute('''
            INSERT INTO notifications (recipient_id, type, title, content)
            VALUES (?, 'system', '知识星球系统已启用', 
                   '知识星球用户审核系统已成功部署。现在用户可以申请知识星球权限来下载数据集。')
            ''', (admin[0],))
            print("✅ 示例通知创建成功")
        else:
            print("⚠️  未找到管理员用户，跳过示例通知创建")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 数据库迁移完成！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📋 迁移总结:")
        print("   ✅ users表添加知识星球字段")
        print("   ✅ 创建planet_applications表")
        print("   ✅ 创建notifications表")
        print("   ✅ 数据库完整性验证")
        print("\n🚀 知识星球功能现已可用！")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移过程中发生错误: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    print("🌟 知识星球功能数据库迁移工具（简化版）")
    print("=" * 60)
    
    # 检查工作目录
    if not os.path.exists("app_enhanced.py"):
        print("❌ 请在dataset_website目录下运行此脚本")
        return
    
    # 执行迁移
    if migrate_database():
        print("\n🎊 迁移完成！现在可以启动应用了：")
        print("\n📖 启动应用:")
        print("   python app_enhanced.py")
        print("\n📖 访问地址:")
        print("   http://localhost:5003")
        print("\n📖 功能说明:")
        print("   1. 普通用户可以在数据集详情页申请知识星球权限")
        print("   2. 管理员可以在管理后台审核申请")
        print("   3. 只有知识星球用户才能下载数据集")
    else:
        print("\n❌ 迁移失败，请检查错误信息")

if __name__ == '__main__':
    main()