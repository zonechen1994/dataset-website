#!/usr/bin/env python3
"""
数据库迁移脚本：为datasets表添加百度网盘链接字段

使用方法：
python dataset_website/migrate_baidu_pan.py
"""

import sqlite3
import os
import sys

def migrate_database():
    """为数据库添加百度网盘相关字段"""
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'dataset.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(datasets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations_needed = []
        
        # 检查baidu_pan_link字段
        if 'baidu_pan_link' not in columns:
            migrations_needed.append('baidu_pan_link')
        
        # 检查baidu_pan_password字段
        if 'baidu_pan_password' not in columns:
            migrations_needed.append('baidu_pan_password')
        
        if not migrations_needed:
            print("数据库字段已是最新版本，无需迁移。")
            return True
        
        print(f"需要添加字段: {', '.join(migrations_needed)}")
        
        # 执行迁移
        if 'baidu_pan_link' in migrations_needed:
            print("添加 baidu_pan_link 字段...")
            cursor.execute("""
                ALTER TABLE datasets 
                ADD COLUMN baidu_pan_link TEXT
            """)
        
        if 'baidu_pan_password' in migrations_needed:
            print("添加 baidu_pan_password 字段...")
            cursor.execute("""
                ALTER TABLE datasets 
                ADD COLUMN baidu_pan_password VARCHAR(20)
            """)
        
        # 提交更改
        conn.commit()
        print("数据库迁移成功完成！")
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(datasets)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"当前数据表字段: {columns}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"数据库操作失败: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

def rollback_migration():
    """回滚迁移（SQLite不支持DROP COLUMN，仅显示警告）"""
    print("警告：SQLite数据库不支持删除列操作。")
    print("如需回滚，请使用数据库备份恢复。")
    print("建议在迁移前先备份数据库文件。")

def backup_database():
    """备份数据库"""
    db_path = os.path.join(os.path.dirname(__file__), 'dataset.db')
    backup_path = db_path + '.backup'
    
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
        return True
    else:
        print(f"数据库文件不存在: {db_path}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='百度网盘字段数据库迁移脚本')
    parser.add_argument('--backup', action='store_true', help='备份数据库')
    parser.add_argument('--rollback', action='store_true', help='回滚迁移（仅显示说明）')
    
    args = parser.parse_args()
    
    if args.backup:
        backup_database()
        return
    
    if args.rollback:
        rollback_migration()
        return
    
    # 默认执行迁移
    print("开始数据库迁移...")
    print("=" * 50)
    
    # 建议备份
    print("建议先备份数据库：")
    print("python migrate_baidu_pan.py --backup")
    
    confirm = input("是否继续迁移？(y/N): ")
    if confirm.lower() != 'y':
        print("迁移已取消。")
        return
    
    success = migrate_database()
    
    if success:
        print("=" * 50)
        print("迁移完成！现在可以使用百度网盘链接功能。")
    else:
        print("=" * 50)
        print("迁移失败！请检查错误信息。")

if __name__ == '__main__':
    main()