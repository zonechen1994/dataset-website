#!/usr/bin/env python3
"""
全量服务器数据合并工具
合并服务器导出的所有增量数据：数据集、用户、审核信息、通知、图片等
"""

import json
import os
import shutil
import shutil
import zipfile
import glob
from datetime import datetime
from models import db, Dataset, Author, Category, Modality, TaskType, User, PlanetApplication, Notification, EmailVerificationCode
from timezone_utils import get_china_datetime
from werkzeug.security import generate_password_hash

def parse_datetime(date_str):
    """将字符串转换为datetime对象"""
    if isinstance(date_str, str):
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
    return date_str

def merge_all_server_data(json_file, merge_files=True):
    """合并服务器所有增量数据到本地数据库"""
    from app_enhanced import create_app
    app = create_app('development')
    
    if not os.path.exists(json_file):
        print(f"❌ 文件不存在: {json_file}")
        return False
    
    with open(json_file, 'r', encoding='utf-8') as f:
        server_data = json.load(f)
    
    print(f"📥 开始合并服务器全量数据: {json_file}")
    print(f"📅 服务器导出时间: {server_data.get('export_time', 'unknown')}")
    print(f"📊 数据概览: {server_data.get('stats', {})}")
    
    merge_stats = {
        "datasets": {"new": 0, "updated": 0},
        "authors": {"new": 0, "updated": 0},
        "users": {"new": 0, "updated": 0},
        "applications": {"new": 0, "updated": 0},
        "notifications": {"new": 0},
        "categories": {"new": 0, "updated": 0},
        "modalities": {"new": 0, "updated": 0},
        "task_types": {"new": 0, "updated": 0},
        "files": {"screenshots": 0, "images": 0}
    }
    
    with app.app_context():
        try:
            # 1. 合并数据集
            merge_stats["datasets"] = merge_datasets(server_data.get("datasets", []))
            
            # 2. 合并作者
            merge_stats["authors"] = merge_authors(server_data.get("authors", []))
            
            # 3. 合并数据集-作者关联
            merge_dataset_authors(server_data.get("dataset_authors", []))
            
            # 4. 合并分类信息
            merge_stats["categories"] = merge_table_data(server_data.get("categories", []), Category, "code")
            merge_stats["modalities"] = merge_table_data(server_data.get("modalities", []), Modality, "code")
            merge_stats["task_types"] = merge_table_data(server_data.get("task_types", []), TaskType, "code")
            
            # 5. 合并用户 (不包含密码)
            merge_stats["users"] = merge_users(server_data.get("users", []))
            
            # 6. 合并知识星球申请
            merge_stats["applications"] = merge_planet_applications(server_data.get("planet_applications", []))
            
            # 7. 合并通知
            merge_stats["notifications"] = merge_notifications(server_data.get("notifications", []))
            
            # 8. 合并邮箱验证码
            merge_email_codes(server_data.get("email_verification_codes", []))
            
            # 提交数据库更改
            db.session.commit()
            
            # 9. 合并文件
            if merge_files and server_data.get("files"):
                merge_stats["files"] = merge_files_data(server_data["files"], json_file)
            
            print_merge_summary(merge_stats)
            
            # 备份原JSON文件
            backup_name = f"merged_{os.path.basename(json_file)}"
            os.rename(json_file, backup_name)
            print(f"📁 原文件已重命名为: {backup_name}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 合并失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def merge_datasets(datasets_data):
    """合并数据集数据"""
    existing_datasets = {d.name: d for d in Dataset.query.all()}
    new_count = updated_count = 0
    
    for dataset_data in datasets_data:
        dataset_name = dataset_data["name"]
        
        if dataset_name in existing_datasets:
            # 更新现有数据集
            dataset = existing_datasets[dataset_name]
            for key, value in dataset_data.items():
                if key not in ['id'] and hasattr(dataset, key):
                    if key in ['created_at', 'updated_at']:
                        value = parse_datetime(value)
                    setattr(dataset, key, value)
            dataset.updated_at = get_china_datetime()
            updated_count += 1
            print(f"🔄 更新数据集: {dataset_name}")
        else:
            # 添加新数据集
            dataset_data_clean = {}
            dataset_data_clean = {}
            for k, v in dataset_data.items():
                # Allow ID to be imported
                if k in ['created_at', 'updated_at']:
                    v = parse_datetime(v)
                dataset_data_clean[k] = v
            dataset = Dataset(**dataset_data_clean)
            db.session.add(dataset)
            new_count += 1
            print(f"➕ 新增数据集: {dataset_name}")
    
    return {"new": new_count, "updated": updated_count}

def merge_authors(authors_data):
    """合并作者数据"""
    existing_authors = {a.name: a for a in Author.query.all()}
    new_count = updated_count = 0
    
    for author_data in authors_data:
        author_name = author_data["name"]
        
        if author_name in existing_authors:
            # 更新现有作者
            author = existing_authors[author_name]
            for key, value in author_data.items():
                if key not in ['id'] and hasattr(author, key):
                    if key in ['created_at', 'updated_at']:
                        value = parse_datetime(value)
                    setattr(author, key, value)
            updated_count += 1
        else:
            # 添加新作者
            author_data_clean = {}
            author_data_clean = {}
            for k, v in author_data.items():
                # Allow ID
                if k in ['created_at', 'updated_at']:
                    v = parse_datetime(v)
                author_data_clean[k] = v
            author = Author(**author_data_clean)
            db.session.add(author)
            new_count += 1
    
    return {"new": new_count, "updated": updated_count}

def merge_dataset_authors(dataset_authors_data):
    """合并数据集-作者关联"""
    for da_data in dataset_authors_data:
        # 通过名称找到对应的数据集和作者
        dataset = Dataset.query.filter_by(name=da_data.get("dataset_name")).first()
        author = Author.query.filter_by(name=da_data.get("author_name")).first()
        
        if dataset and author and author not in dataset.authors:
            dataset.authors.append(author)

def merge_table_data(data_list, model_class, unique_field):
    """合并表数据 (分类、模态、任务类型)"""
    existing_items = {getattr(item, unique_field): item for item in model_class.query.all()}
    new_count = updated_count = 0
    
    for item_data in data_list:
        unique_value = item_data[unique_field]
        
        if unique_value in existing_items:
            # 更新现有项
            item = existing_items[unique_value]
            for key, value in item_data.items():
                if key not in ['id'] and hasattr(item, key):
                    if key in ['created_at', 'updated_at']:
                        value = parse_datetime(value)
                    setattr(item, key, value)
            updated_count += 1
        else:
            # 添加新项
            item_data_clean = {}
            item_data_clean = {}
            for k, v in item_data.items():
                # Allow ID
                if k in ['created_at', 'updated_at']:
                    v = parse_datetime(v)
                item_data_clean[k] = v
            item = model_class(**item_data_clean)
            db.session.add(item)
            new_count += 1
    
    return {"new": new_count, "updated": updated_count}

def merge_users(users_data):
    """合并用户数据 (不包含密码)"""
    existing_users = {u.username: u for u in User.query.all()}
    new_count = updated_count = 0
    
    for user_data in users_data:
        username = user_data["username"]
        print(f"DEBUG: Processing User {username}, JSON ID: {user_data.get('id')}")
        
        if username in existing_users:
            # 更新现有用户信息 (除了密码)
            user = existing_users[username]
            for key, value in user_data.items():
                if key not in ['id', 'password_hash'] and hasattr(user, key):
                    if key in ['created_at', 'updated_at', 'last_login', 'planet_approved_at']:
                        value = parse_datetime(value)
                    setattr(user, key, value)
            updated_count += 1
            print(f"🔄 更新用户: {username}")
        else:
            # 新用户需要设置默认密码，稍后需要用户重置
            user_data_clean = {}
            for k, v in user_data.items():
                # Allow ID
                if k in ['created_at', 'updated_at', 'last_login', 'planet_approved_at']:
                    v = parse_datetime(v)
                user_data_clean[k] = v
            
            # Force ID using Raw SQL to bypass ORM auto-increment behavior
            from sqlalchemy import text
            
            # Prepare data dict
            insert_data = {
                'id': user_data['id'] if 'id' in user_data else None,
                'username': user_data_clean['username'],
                'email': user_data_clean['email'],
                'password_hash': generate_password_hash('placeholder_will_need_reset'),
                'full_name': user_data_clean.get('full_name') or user_data_clean['username'],
                'role': user_data_clean.get('role', 'user'),
                'is_active': True,
                'created_at': user_data_clean.get('created_at', get_china_datetime()),
                'updated_at': user_data_clean.get('updated_at', get_china_datetime()),
                'last_login': user_data_clean.get('last_login'),
                'is_planet_user': user_data_clean.get('is_planet_user', False),
                'planet_approved_at': user_data_clean.get('planet_approved_at'),
                'planet_approved_by': user_data_clean.get('planet_approved_by'),
                'planet_expiry_date': user_data_clean.get('planet_expiry_date'),
                'planet_membership_duration': user_data_clean.get('planet_membership_duration')
            }
            
            # Make sure we have an ID
            if insert_data['id'] is None:
                # Should not happen with server data, but fallback
                print(f"⚠️ Warning: No ID for user {username}, skipping raw insert")
                continue

            # Execute Raw Insert
            sql = text("""
                INSERT INTO users (
                    id, username, email, password_hash, full_name, role, is_active, 
                    created_at, updated_at, last_login, 
                    is_planet_user, planet_approved_at, planet_approved_by, 
                    planet_expiry_date, planet_membership_duration
                ) VALUES (
                    :id, :username, :email, :password_hash, :full_name, :role, :is_active,
                    :created_at, :updated_at, :last_login,
                    :is_planet_user, :planet_approved_at, :planet_approved_by,
                    :planet_expiry_date, :planet_membership_duration
                )
            """)
            
            db.session.execute(sql, insert_data)
            new_count += 1
            print(f"➕ 新增用户 (Raw SQL): {username} (ID: {insert_data['id']})")
    
    return {"new": new_count, "updated": updated_count}

def merge_planet_applications(applications_data):
    """合并知识星球申请"""
    new_count = updated_count = 0
    
    for app_data in applications_data:
        # 根据用户ID和创建时间查找是否已存在
        existing = PlanetApplication.query.filter_by(
            user_id=app_data.get("user_id"),
            created_at=app_data.get("created_at")
        ).first()
        
        if existing:
            # 更新现有申请
            for key, value in app_data.items():
                if key not in ['id'] and hasattr(existing, key):
                    if key in ['created_at', 'updated_at', 'processed_at', 'reviewed_at']:
                        value = parse_datetime(value)
                    setattr(existing, key, value)
            updated_count += 1
            print(f"🔄 更新申请: {app_data.get('user_id')}")
        else:
            # 添加新申请
            app_data_clean = {}
            for k, v in app_data.items():
                # Allow ID
                if k in ['created_at', 'updated_at', 'processed_at', 'reviewed_at']:
                    v = parse_datetime(v)
                app_data_clean[k] = v
            app_data = app_data_clean
            application = PlanetApplication(**app_data)
            db.session.add(application)
            new_count += 1
            print(f"📝 新增申请: {app_data.get('user_id')}")
    
    return {"new": new_count, "updated": updated_count}

def merge_notifications(notifications_data):
    """合并通知（跳过已存在的记录）"""
    new_count = 0
    skip_count = 0

    for notif_data in notifications_data:
        # 检查是否已存在
        notif_id = notif_data.get('id')
        if notif_id:
            existing = Notification.query.get(notif_id)
            if existing:
                skip_count += 1
                continue

        notif_data_clean = {}
        for k, v in notif_data.items():
            if k in ['created_at', 'updated_at']:
                v = parse_datetime(v)
            notif_data_clean[k] = v
        notification = Notification(**notif_data_clean)
        db.session.add(notification)
        new_count += 1

    print(f"  Notifications: new={new_count}, skipped={skip_count}")
    return {"new": new_count}

def merge_email_codes(codes_data):
    """合并邮箱验证码（跳过已存在的记录）"""
    new_count = 0
    skip_count = 0
    for code_data in codes_data:
        # 检查是否已存在
        code_id = code_data.get('id')
        if code_id:
            existing = EmailVerificationCode.query.get(code_id)
            if existing:
                skip_count += 1
                continue

        code_data_clean = {}
        for k, v in code_data.items():
            if k in ['created_at', 'expires_at', 'used_at']:
                v = parse_datetime(v)
            code_data_clean[k] = v
        code = EmailVerificationCode(**code_data_clean)
        db.session.add(code)
        new_count += 1

    print(f"  Email codes: new={new_count}, skipped={skip_count}")

def merge_files_data(files_data, json_file):
    """合并文件数据"""
    files_stats = {"screenshots": 0, "images": 0}
    
    # 查找对应的zip文件
    zip_file = json_file.replace('.json', '_files.zip')
    if not os.path.exists(zip_file):
        # 尝试其他可能的zip文件名
        base_name = os.path.splitext(json_file)[0]
        zip_candidates = glob.glob(f"{base_name}*.zip") + glob.glob("server_files_*.zip")
        if zip_candidates:
            zip_file = zip_candidates[0]
            print(f"📁 找到文件压缩包: {zip_file}")
    
    if os.path.exists(zip_file):
        print(f"📁 正在解压文件: {zip_file}")
        
        # 解压文件
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.is_dir():
                    # 保持目录结构解压
                    zip_ref.extract(file_info, '.')
                    
                    if 'screenshots' in file_info.filename:
                        files_stats["screenshots"] += 1
                    elif 'images' in file_info.filename:
                        files_stats["images"] += 1
        
        print(f"📁 文件解压完成，备份zip文件")
        backup_zip = f"merged_{os.path.basename(zip_file)}"
        os.rename(zip_file, backup_zip)
    else:
        print("📁 未找到对应的文件压缩包")
    
    return files_stats

def print_merge_summary(stats):
    """打印合并统计摘要"""
    print(f"\n✅ 全量数据合并完成!")
    print(f"\n📊 合并统计:")
    
    for category, counts in stats.items():
        if category == "files":
            print(f"  📁 文件:")
            print(f"    📷 截图: {counts['screenshots']} 个")
            print(f"    🖼️ 图片: {counts['images']} 个")
        else:
            if isinstance(counts, dict):
                if counts.get("new", 0) > 0 or counts.get("updated", 0) > 0:
                    print(f"  📄 {category}:")
                    if counts.get("new", 0) > 0:
                        print(f"    ➕ 新增: {counts['new']} 个")
                    if counts.get("updated", 0) > 0:
                        print(f"    🔄 更新: {counts['updated']} 个")

def list_increment_files():
    """列出所有增量数据文件"""
    json_files = [f for f in os.listdir('.') if 
                  (f.startswith('server_increment_') or f.startswith('server_full_increment_')) 
                  and f.endswith('.json')]
    zip_files = [f for f in os.listdir('.') if f.startswith('server_files_') and f.endswith('.zip')]
    
    if json_files or zip_files:
        print("📂 发现的服务器数据文件:")
        if json_files:
            print("  📄 JSON数据文件:")
            for i, file in enumerate(json_files, 1):
                print(f"    {i}. {file}")
        if zip_files:
            print("  📁 文件压缩包:")
            for i, file in enumerate(zip_files, 1):
                print(f"    {i}. {file}")
    else:
        print("❌ 未发现服务器数据文件")
    
    return {"json_files": json_files, "zip_files": zip_files}

if __name__ == "__main__":
    import sys
    import glob
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python merge_server_data.py <json文件> [--no-files]")
        print("  python merge_server_data.py --list")
        print("  python merge_server_data.py --auto  # 自动合并最新文件")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        list_increment_files()
    elif sys.argv[1] == '--auto':
        # 自动查找最新的增量文件
        json_files = glob.glob('server_*increment_*.json')
        if json_files:
            latest_file = max(json_files, key=os.path.getmtime)
            print(f"🔍 找到最新文件: {latest_file}")
            merge_files = '--no-files' not in sys.argv
            merge_all_server_data(latest_file, merge_files=merge_files)
        else:
            print("❌ 未找到增量数据文件")
    else:
        json_file = sys.argv[1]
        merge_files = '--no-files' not in sys.argv
        merge_all_server_data(json_file, merge_files=merge_files)