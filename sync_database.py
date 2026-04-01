#!/usr/bin/env python3
"""
数据库同步工具 - 导出/导入数据集数据
用于解决本地和服务器数据不一致问题
"""

import sqlite3
import json
import os
from datetime import datetime
from models import db, Dataset, Author, Category, Modality, TaskType, User, PlanetApplication

def export_database(db_path="dataset.db", export_file="database_export.json"):
    """导出数据库数据到JSON文件"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    export_data = {
        "export_time": datetime.now().isoformat(),
        "datasets": [],
        "categories": [],
        "modalities": [],
        "task_types": [],
        "users": [],
        "planet_applications": []
    }
    
    # 导出数据集
    cursor.execute("SELECT * FROM datasets")
    datasets = cursor.fetchall()
    for dataset in datasets:
        export_data["datasets"].append(dict(dataset))
    
    # 导出分类
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    for category in categories:
        export_data["categories"].append(dict(category))
    
    # 导出模态
    cursor.execute("SELECT * FROM modalities")
    modalities = cursor.fetchall()
    for modality in modalities:
        export_data["modalities"].append(dict(modality))
    
    # 导出任务类型
    cursor.execute("SELECT * FROM task_types")
    task_types = cursor.fetchall()
    for task_type in task_types:
        export_data["task_types"].append(dict(task_type))
    
    # 导出用户 (排除密码)
    cursor.execute("SELECT id, username, email, is_admin, created_at, planet_access FROM users")
    users = cursor.fetchall()
    for user in users:
        export_data["users"].append(dict(user))
    
    # 导出知识星球申请
    cursor.execute("SELECT * FROM planet_applications")
    applications = cursor.fetchall()
    for app in applications:
        export_data["planet_applications"].append(dict(app))
    
    conn.close()
    
    with open(export_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"数据库已导出到: {export_file}")
    print(f"导出了 {len(export_data['datasets'])} 个数据集")
    return export_file

def import_database(import_file="database_export.json", merge=True):
    """从JSON文件导入数据库数据"""
    from app_enhanced import app
    
    if not os.path.exists(import_file):
        print(f"导入文件不存在: {import_file}")
        return False
    
    with open(import_file, 'r', encoding='utf-8') as f:
        import_data = json.load(f)
    
    with app.app_context():
        if merge:
            # 合并模式 - 只添加新数据
            existing_datasets = {d.name for d in Dataset.query.all()}
            new_count = 0
            
            for dataset_data in import_data.get("datasets", []):
                if dataset_data["name"] not in existing_datasets:
                    dataset = Dataset(**{k: v for k, v in dataset_data.items() if k != 'id'})
                    db.session.add(dataset)
                    new_count += 1
            
            db.session.commit()
            print(f"合并模式: 添加了 {new_count} 个新数据集")
        else:
            # 完全替换模式 (危险!)
            print("警告: 完全替换模式会删除现有数据!")
            response = input("确认继续? (yes/no): ")
            if response.lower() != 'yes':
                return False
            
            # 清空现有数据
            Dataset.query.delete()
            db.session.commit()
            
            # 导入新数据
            for dataset_data in import_data.get("datasets", []):
                dataset = Dataset(**{k: v for k, v in dataset_data.items() if k != 'id'})
                db.session.add(dataset)
            
            db.session.commit()
            print(f"完全替换: 导入了 {len(import_data['datasets'])} 个数据集")
    
    return True

def backup_database(backup_name=None):
    """备份当前数据库"""
    if backup_name is None:
        backup_name = f"dataset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    import shutil
    shutil.copy2("dataset.db", backup_name)
    print(f"数据库已备份到: {backup_name}")
    return backup_name

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python sync_database.py export [输出文件]")
        print("  python sync_database.py import [输入文件] [--replace]")
        print("  python sync_database.py backup [备份名称]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "export":
        export_file = sys.argv[2] if len(sys.argv) > 2 else "database_export.json"
        export_database(export_file=export_file)
    
    elif command == "import":
        import_file = sys.argv[2] if len(sys.argv) > 2 else "database_export.json"
        replace_mode = "--replace" in sys.argv
        import_database(import_file, merge=not replace_mode)
    
    elif command == "backup":
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        backup_database(backup_name)
    
    else:
        print(f"未知命令: {command}")