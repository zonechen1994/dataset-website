#!/usr/bin/env python3
"""
全量增量数据导出工具
导出服务器上所有可能产生的新数据：数据集、用户、审核信息、通知、文件等
"""

import sqlite3
import json
import os
import shutil
import glob
from datetime import datetime, timedelta

def export_all_new_data(since_date=None, db_path="dataset.db", include_files=True):
    """导出指定日期后所有新增/更新的数据"""
    if since_date is None:
        # 默认导出最近7天的数据
        since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    export_data = {
        "export_time": datetime.now().isoformat(),
        "since_date": since_date,
        "datasets": [],
        "authors": [],
        "dataset_authors": [],
        "categories": [],
        "modalities": [],
        "task_types": [],
        "users": [],
        "planet_applications": [],
        "notifications": [],
        "email_verification_codes": [],
        "files": {
            "screenshots": [],
            "dataset_images": []
        },
        "stats": {}
    }
    
    # 1. 导出数据集 (新增和更新的)
    cursor.execute("""
    SELECT * FROM datasets 
    WHERE created_at >= ? OR updated_at >= ?
    ORDER BY created_at DESC
    """, (since_date, since_date))
    datasets = cursor.fetchall()
    export_data["datasets"] = [dict(row) for row in datasets]
    
    # 2. 导出相关作者信息
    if datasets:
        dataset_ids = [d['id'] for d in datasets]
        placeholders = ','.join(['?' for _ in dataset_ids])
        
        # 获取数据集对应的作者关联
        cursor.execute(f"""
        SELECT * FROM dataset_authors 
        WHERE dataset_id IN ({placeholders})
        """, dataset_ids)
        dataset_authors = cursor.fetchall()
        export_data["dataset_authors"] = [dict(row) for row in dataset_authors]
        
        # 获取作者详细信息
        if dataset_authors:
            author_ids = list(set([da['author_id'] for da in dataset_authors]))
            author_placeholders = ','.join(['?' for _ in author_ids])
            cursor.execute(f"""
            SELECT * FROM authors 
            WHERE id IN ({author_placeholders})
            """, author_ids)
            authors = cursor.fetchall()
            export_data["authors"] = [dict(row) for row in authors]
    
    # 3. 导出新增/更新的分类、模态、任务类型
    for table in ['categories', 'modalities', 'task_types']:
        try:
            cursor.execute(f"""
            SELECT * FROM {table} 
            WHERE created_at >= ? OR updated_at >= ?
            ORDER BY created_at DESC
            """, (since_date, since_date))
        except:
            # 如果没有时间戳字段，导出所有数据
            cursor.execute(f"SELECT * FROM {table}")
        
        rows = cursor.fetchall()
        export_data[table] = [dict(row) for row in rows]
    
    # 4. 导出新用户
    cursor.execute("""
    SELECT id, username, email, full_name, role, is_active, 
           created_at, updated_at, last_login, is_planet_user,
           planet_approved_at, planet_approved_by
    FROM users 
    WHERE created_at >= ? OR updated_at >= ?
    ORDER BY created_at DESC
    """, (since_date, since_date))
    users = cursor.fetchall()
    export_data["users"] = [dict(row) for row in users]
    
    # 5. 导出知识星球申请
    cursor.execute("""
    SELECT * FROM planet_applications 
    WHERE created_at >= ? OR updated_at >= ?
    ORDER BY created_at DESC
    """, (since_date, since_date))
    applications = cursor.fetchall()
    export_data["planet_applications"] = [dict(row) for row in applications]
    
    # 6. 导出通知
    cursor.execute("""
    SELECT * FROM notifications 
    WHERE created_at >= ?
    ORDER BY created_at DESC
    """, (since_date,))
    notifications = cursor.fetchall()
    export_data["notifications"] = [dict(row) for row in notifications]
    
    # 7. 导出邮箱验证码 (最近的)
    cursor.execute("""
    SELECT * FROM email_verification_codes 
    WHERE created_at >= ?
    ORDER BY created_at DESC
    """, (since_date,))
    codes = cursor.fetchall()
    export_data["email_verification_codes"] = [dict(row) for row in codes]
    
    conn.close()
    
    # 8. 导出相关文件
    if include_files:
        export_data["files"] = export_files(since_date, export_data)
    
    # 9. 统计信息
    export_data["stats"] = {
        "datasets": len(export_data["datasets"]),
        "authors": len(export_data["authors"]),
        "users": len(export_data["users"]),
        "applications": len(export_data["planet_applications"]),
        "notifications": len(export_data["notifications"]),
        "screenshots": len(export_data["files"]["screenshots"]),
        "dataset_images": len(export_data["files"]["dataset_images"])
    }
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"server_full_increment_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
    
    print_export_summary(filename, export_data)
    return filename

def export_files(since_date, export_data):
    """导出相关文件信息"""
    files_info = {
        "screenshots": [],
        "dataset_images": []
    }
    
    # 导出截图文件
    screenshots_dir = "uploads/screenshots"
    if os.path.exists(screenshots_dir):
        for screenshot_file in glob.glob(f"{screenshots_dir}/*"):
            file_stat = os.stat(screenshot_file)
            file_date = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d')
            if file_date >= since_date:
                files_info["screenshots"].append({
                    "filename": os.path.basename(screenshot_file),
                    "path": screenshot_file,
                    "size": file_stat.st_size,
                    "modified": file_date
                })
    
    # 导出数据集图片
    dataset_images_dir = "static/images/datasets"
    if os.path.exists(dataset_images_dir):
        for img_file in glob.glob(f"{dataset_images_dir}/*"):
            if os.path.isfile(img_file):
                file_stat = os.stat(img_file)
                file_date = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d')
                if file_date >= since_date:
                    files_info["dataset_images"].append({
                        "filename": os.path.basename(img_file),
                        "path": img_file,
                        "size": file_stat.st_size,
                        "modified": file_date
                    })
    
    return files_info

def create_files_archive(export_data, archive_name=None):
    """创建文件压缩包"""
    if archive_name is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        archive_name = f"server_files_{timestamp}"
    
    files_to_copy = []
    
    # 收集需要复制的文件
    for screenshot in export_data["files"]["screenshots"]:
        if os.path.exists(screenshot["path"]):
            files_to_copy.append(screenshot["path"])
    
    for img in export_data["files"]["dataset_images"]:
        if os.path.exists(img["path"]):
            files_to_copy.append(img["path"])
    
    if files_to_copy:
        # 创建临时目录结构
        temp_dir = f"temp_{archive_name}"
        os.makedirs(temp_dir, exist_ok=True)
        
        for file_path in files_to_copy:
            # 保持目录结构
            rel_path = os.path.relpath(file_path, ".")
            dest_path = os.path.join(temp_dir, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file_path, dest_path)
        
        # 创建压缩包
        shutil.make_archive(archive_name, 'zip', temp_dir)
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        print(f"📁 文件压缩包已创建: {archive_name}.zip")
        return f"{archive_name}.zip"
    
    return None

def print_export_summary(filename, export_data):
    """打印导出摘要"""
    print(f"\n✅ 全量增量数据导出完成: {filename}")
    print(f"📅 导出时间范围: {export_data['since_date']} 至今")
    print(f"\n📊 导出统计:")
    
    stats = export_data["stats"]
    for key, count in stats.items():
        emoji = {
            "datasets": "📋",
            "authors": "👤", 
            "users": "👥",
            "applications": "📝",
            "notifications": "🔔",
            "screenshots": "📷",
            "dataset_images": "🖼️"
        }.get(key, "📄")
        
        print(f"  {emoji} {key}: {count}")
    
    if export_data["datasets"]:
        print(f"\n📋 新增/更新数据集:")
        for i, dataset in enumerate(export_data["datasets"][:5], 1):
            print(f"  {i}. {dataset['name']} ({dataset.get('organ_category', 'unknown')})")
        if len(export_data["datasets"]) > 5:
            print(f"  ... 还有 {len(export_data['datasets']) - 5} 个")
    
    print(f"\n💡 使用方法:")
    print(f"  python merge_server_data.py {filename}")
    
    return export_data["stats"]

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("用法:")
        print("  python export_new_data.py [日期] [选项]")
        print("  python export_new_data.py 2024-08-15")
        print("  python export_new_data.py --no-files   # 不包含文件")
        print("  python export_new_data.py --files-only # 只创建文件压缩包")
        sys.exit(0)
    
    # 参数解析
    since_date = None
    include_files = True
    files_only = False
    
    for arg in sys.argv[1:]:
        if arg == '--no-files':
            include_files = False
        elif arg == '--files-only':
            files_only = True
        elif arg.startswith('-'):
            continue
        else:
            since_date = arg
    
    if files_only:
        # 只创建文件压缩包
        temp_data = {"files": export_files(since_date or (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'), {})}
        create_files_archive(temp_data)
    else:
        # 导出数据
        filename = export_all_new_data(since_date, include_files=include_files)
        
        # 如果有文件，询问是否创建压缩包
        if include_files:
            with open(filename, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
            
            total_files = export_data["stats"]["screenshots"] + export_data["stats"]["dataset_images"]
            if total_files > 0:
                response = input(f"\n发现 {total_files} 个文件，是否创建文件压缩包? (y/n): ")
                if response.lower() in ['y', 'yes', '是']:
                    create_files_archive(export_data)