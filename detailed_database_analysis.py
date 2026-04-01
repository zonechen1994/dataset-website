#!/usr/bin/env python3
"""
详细分析数据库问题 - 检查备份和当前数据库差异
"""

import sqlite3
import os
from datetime import datetime

def analyze_backup_database(backup_db="dataset.db.backup"):
    """详细分析备份数据库"""
    print(f"🔍 分析备份数据库: {backup_db}")
    print("=" * 50)
    
    if not os.path.exists(backup_db):
        print(f"❌ 备份文件不存在: {backup_db}")
        return
    
    conn = sqlite3.connect(backup_db)
    cursor = conn.cursor()
    
    try:
        # 检查备份数据库的数据集
        cursor.execute("SELECT COUNT(*) FROM datasets")
        backup_count = cursor.fetchone()[0]
        print(f"📈 备份数据库数据集总数: {backup_count}")
        
        # 检查备份数据库的表结构
        cursor.execute("PRAGMA table_info(datasets)")
        columns = cursor.fetchall()
        print(f"\n📋 备份数据库表结构:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 显示备份数据库中的所有数据集
        cursor.execute("SELECT id, name, organ_category FROM datasets ORDER BY id")
        datasets = cursor.fetchall()
        print(f"\n📋 备份数据库中的数据集:")
        for dataset in datasets:
            print(f"  ID:{dataset[0]} - {dataset[1]} ({dataset[2]})")
            
        # 检查文件修改时间
        backup_stat = os.stat(backup_db)
        backup_time = datetime.fromtimestamp(backup_stat.st_mtime)
        print(f"\n⏰ 备份文件修改时间: {backup_time}")
        
    except Exception as e:
        print(f"❌ 分析备份数据库失败: {str(e)}")
    finally:
        conn.close()

def compare_databases_detailed(main_db="dataset.db", backup_db="dataset.db.backup"):
    """详细对比两个数据库"""
    print(f"\n" + "=" * 50)
    print(f"🔍 详细对比数据库")
    
    # 分析主数据库
    main_datasets = get_datasets_info(main_db)
    backup_datasets = get_datasets_info(backup_db)
    
    print(f"\n📊 对比结果:")
    print(f"主数据库: {len(main_datasets)} 个数据集")
    print(f"备份数据库: {len(backup_datasets)} 个数据集")
    
    # 找出差异
    main_ids = set(d[0] for d in main_datasets)
    backup_ids = set(d[0] for d in backup_datasets)
    
    # 主数据库独有的
    only_in_main = main_ids - backup_ids
    # 备份数据库独有的
    only_in_backup = backup_ids - main_ids
    
    if only_in_main:
        print(f"\n✅ 只在主数据库中存在的数据集 (ID): {sorted(only_in_main)}")
        for dataset in main_datasets:
            if dataset[0] in only_in_main:
                print(f"   ID:{dataset[0]} - {dataset[1]}")
    
    if only_in_backup:
        print(f"\n⚠️  只在备份数据库中存在的数据集 (ID): {sorted(only_in_backup)}")
        for dataset in backup_datasets:
            if dataset[0] in only_in_backup:
                print(f"   ID:{dataset[0]} - {dataset[1]}")
    
    # 检查可能的ID重用
    if main_datasets and backup_datasets:
        max_backup_id = max(d[0] for d in backup_datasets)
        min_main_id = min(d[0] for d in main_datasets)
        print(f"\n📈 备份数据库最大ID: {max_backup_id}")
        print(f"📈 主数据库最小ID: {min_main_id}")
        
        if min_main_id > max_backup_id:
            print(f"✅ 主数据库的数据集是在备份之后添加的")
        else:
            print(f"⚠️  可能存在数据覆盖或删除情况")

def get_datasets_info(db_path):
    """获取数据库中的数据集信息"""
    if not os.path.exists(db_path):
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, organ_category FROM datasets ORDER BY id")
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ 获取数据集信息失败 ({db_path}): {str(e)}")
        return []
    finally:
        conn.close()

def check_recent_changes(main_db="dataset.db"):
    """检查最近的数据变化"""
    print(f"\n" + "=" * 50)
    print(f"📅 检查最近的数据变化")
    
    conn = sqlite3.connect(main_db)
    cursor = conn.cursor()
    
    try:
        # 按创建时间排序
        cursor.execute("""
        SELECT id, name, created_at, updated_at 
        FROM datasets 
        ORDER BY created_at DESC
        """)
        datasets = cursor.fetchall()
        
        print(f"\n📋 按创建时间排序的数据集:")
        for dataset in datasets:
            print(f"  ID:{dataset[0]} - {dataset[1]}")
            print(f"    创建时间: {dataset[2]}")
            print(f"    更新时间: {dataset[3]}")
            print()
            
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
    finally:
        conn.close()

def export_current_data(main_db="dataset.db"):
    """导出当前数据为JSON备份"""
    print(f"\n" + "=" * 50)
    print(f"💾 导出当前数据")
    
    import json
    
    conn = sqlite3.connect(main_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    export_data = {
        "export_time": datetime.now().isoformat(),
        "datasets": [],
        "users": [],
        "planet_applications": [],
        "notifications": []
    }
    
    try:
        # 导出数据集
        cursor.execute("SELECT * FROM datasets ORDER BY id")
        datasets = cursor.fetchall()
        export_data["datasets"] = [dict(row) for row in datasets]
        
        # 导出用户
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        export_data["users"] = [dict(row) for row in users]
        
        # 导出知识星球申请
        cursor.execute("SELECT * FROM planet_applications")
        applications = cursor.fetchall()
        export_data["planet_applications"] = [dict(row) for row in applications]
        
        # 导出通知
        cursor.execute("SELECT * FROM notifications")
        notifications = cursor.fetchall()
        export_data["notifications"] = [dict(row) for row in notifications]
        
        # 保存到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"database_backup_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 数据已导出到: {filename}")
        print(f"   数据集: {len(export_data['datasets'])}")
        print(f"   用户: {len(export_data['users'])}")
        print(f"   知识星球申请: {len(export_data['planet_applications'])}")
        print(f"   通知: {len(export_data['notifications'])}")
        
        return filename
        
    except Exception as e:
        print(f"❌ 导出失败: {str(e)}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_backup_database()
    compare_databases_detailed()
    check_recent_changes()
    export_current_data()