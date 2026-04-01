#!/usr/bin/env python3
"""
知识星球功能数据库迁移脚本

此脚本将现有数据库升级以支持知识星球用户审核系统:
1. 在users表中添加知识星球相关字段
2. 创建planet_applications表
3. 创建notifications表

使用方法:
python migrate_planet_features.py
"""

import os
import sys
from datetime import datetime

# 添加应用目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, User, PlanetApplication, Notification
from config import config

def migrate_database():
    """执行数据库迁移"""
    print("🚀 开始知识星球功能数据库迁移...")
    
    # 创建应用实例
    app = create_app('development')
    
    with app.app_context():
        try:
            # 备份提示
            print("⚠️  强烈建议在迁移前备份数据库！")
            confirm = input("是否继续执行迁移？(y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("❌ 迁移已取消")
                return False
            
            print("\n📊 检查当前数据库状态...")
            
            # 检查是否已经迁移过
            try:
                # 尝试查询新字段，如果不存在会抛出异常
                db.session.execute("SELECT is_planet_user FROM users LIMIT 1")
                print("✅ 检测到users表已包含知识星球字段")
            except Exception:
                print("📋 正在为users表添加知识星球字段...")
                
                # 添加字段的SQL语句
                alter_statements = [
                    "ALTER TABLE users ADD COLUMN is_planet_user BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE users ADD COLUMN planet_approved_at DATETIME NULL",
                    "ALTER TABLE users ADD COLUMN planet_approved_by INTEGER NULL"
                ]
                
                for statement in alter_statements:
                    try:
                        db.session.execute(statement)
                        print(f"✅ 执行: {statement}")
                    except Exception as e:
                        print(f"⚠️  跳过（可能已存在）: {statement} - {e}")
                
                # 添加外键约束
                try:
                    db.session.execute(
                        "ALTER TABLE users ADD CONSTRAINT fk_users_planet_approved_by "
                        "FOREIGN KEY (planet_approved_by) REFERENCES users (id)"
                    )
                    print("✅ 添加外键约束: fk_users_planet_approved_by")
                except Exception as e:
                    print(f"⚠️  外键约束可能已存在: {e}")
            
            # 创建新表
            print("\n📋 创建新表...")
            db.create_all()
            
            # 验证表结构
            print("\n🔍 验证数据库表结构...")
            
            # 检查users表的新字段
            users_columns = db.session.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'users' AND column_name IN "
                "('is_planet_user', 'planet_approved_at', 'planet_approved_by')"
            ).fetchall()
            
            if len(users_columns) >= 3:
                print("✅ users表知识星球字段验证成功")
            else:
                print("❌ users表字段验证失败")
                return False
            
            # 检查新表
            tables_to_check = ['planet_applications', 'notifications']
            for table_name in tables_to_check:
                try:
                    result = db.session.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                    print(f"✅ 表 {table_name} 创建成功")
                except Exception as e:
                    print(f"❌ 表 {table_name} 验证失败: {e}")
                    return False
            
            # 提交所有更改
            db.session.commit()
            
            # 创建示例数据（可选）
            print("\n🎯 创建示例通知...")
            try:
                admin_users = User.query.filter_by(role='admin').all()
                if admin_users:
                    admin = admin_users[0]
                    
                    sample_notification = Notification(
                        recipient_id=admin.id,
                        type='system',
                        title='知识星球系统已启用',
                        content='知识星球用户审核系统已成功部署。现在用户可以申请知识星球权限来下载数据集。'
                    )
                    
                    db.session.add(sample_notification)
                    db.session.commit()
                    print("✅ 示例通知创建成功")
                else:
                    print("⚠️  未找到管理员用户，跳过示例通知创建")
            
            except Exception as e:
                print(f"⚠️  示例通知创建失败: {e}")
            
            print(f"\n🎉 数据库迁移完成！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n📋 迁移总结:")
            print("   ✅ users表添加知识星球字段")
            print("   ✅ 创建planet_applications表")
            print("   ✅ 创建notifications表")
            print("   ✅ 添加外键约束")
            print("\n🚀 知识星球功能现已可用！")
            
            return True
            
        except Exception as e:
            print(f"❌ 迁移过程中发生错误: {e}")
            db.session.rollback()
            return False

def verify_migration():
    """验证迁移结果"""
    print("\n🔍 执行迁移验证...")
    
    app = create_app('development')
    with app.app_context():
        try:
            # 测试User模型的新字段
            user_count = User.query.count()
            print(f"📊 用户总数: {user_count}")
            
            # 测试新字段查询
            planet_users = User.query.filter_by(is_planet_user=True).count()
            print(f"📊 知识星球用户数: {planet_users}")
            
            # 测试新表
            applications_count = PlanetApplication.query.count()
            notifications_count = Notification.query.count()
            
            print(f"📊 知识星球申请数: {applications_count}")
            print(f"📊 通知消息数: {notifications_count}")
            
            print("✅ 迁移验证成功！")
            return True
            
        except Exception as e:
            print(f"❌ 迁移验证失败: {e}")
            return False

def main():
    """主函数"""
    print("🌟 知识星球功能数据库迁移工具")
    print("=" * 50)
    
    # 执行迁移
    if migrate_database():
        # 验证迁移
        if verify_migration():
            print("\n🎊 所有操作完成！您现在可以使用知识星球功能了。")
            print("\n📖 使用说明:")
            print("   1. 普通用户可以在数据集详情页申请知识星球权限")
            print("   2. 管理员可以在管理后台审核申请")
            print("   3. 只有知识星球用户才能下载数据集")
            print("   4. 管理员会收到新申请的通知")
        else:
            print("\n❌ 验证失败，请检查数据库状态")
            sys.exit(1)
    else:
        print("\n❌ 迁移失败，请检查错误信息")
        sys.exit(1)

if __name__ == '__main__':
    main()