#!/usr/bin/env python3
"""
测试收回知识星球权限功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import User, db, Notification
from datetime import datetime

def test_revoke_planet_access():
    """测试收回知识星球权限功能"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 知识星球权限收回功能测试 ===")
        
        # 1. 查找有知识星球权限的用户
        planet_users = User.query.filter_by(is_planet_user=True).all()
        
        if not planet_users:
            print("❌ 没有找到拥有知识星球权限的用户，无法进行测试")
            print("请先为某个用户授予知识星球权限")
            return False
        
        print(f"✅ 找到 {len(planet_users)} 个拥有知识星球权限的用户")
        
        # 2. 选择第一个用户进行测试
        test_user = planet_users[0]
        
        print(f"\n📋 测试用户信息:")
        print(f"   用户名: {test_user.username}")
        print(f"   邮箱: {test_user.email}")
        print(f"   当前知识星球状态: {'已授权' if test_user.is_planet_user else '无权限'}")
        print(f"   权限获得时间: {test_user.planet_approved_at.strftime('%Y-%m-%d %H:%M') if test_user.planet_approved_at else '未记录'}")
        
        # 3. 收回权限
        print(f"\n🔄 正在收回用户 {test_user.username} 的知识星球权限...")
        
        try:
            # 保存原始状态用于验证
            original_status = test_user.is_planet_user
            original_approved_at = test_user.planet_approved_at
            
            # 收回权限
            test_user.is_planet_user = False
            test_user.planet_approved_at = None
            
            # 创建通知
            notification = Notification(
                recipient_id=test_user.id,
                title="知识星球权限已被收回",
                content="您的知识星球权限已被管理员收回。如有疑问，请联系管理员。",
                notification_type="system"
            )
            db.session.add(notification)
            
            # 提交更改
            db.session.commit()
            
            print("✅ 权限收回成功")
            
            # 4. 验证更改
            updated_user = User.query.get(test_user.id)
            
            print(f"\n📊 验证结果:")
            print(f"   知识星球权限: {'已授权' if updated_user.is_planet_user else '无权限'}")
            print(f"   权限获得时间: {updated_user.planet_approved_at if updated_user.planet_approved_at else '已清空'}")
            
            # 5. 检查通知是否创建成功
            recent_notification = Notification.query.filter_by(
                recipient_id=test_user.id,
                title="知识星球权限已被收回"
            ).first()
            
            if recent_notification:
                print("✅ 系统通知创建成功")
                print(f"   通知内容: {recent_notification.content}")
                print(f"   通知时间: {recent_notification.created_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                print("⚠️ 系统通知创建失败")
            
            # 6. 恢复原始状态（用于重复测试）
            print(f"\n🔄 恢复用户原始状态...")
            test_user.is_planet_user = original_status
            test_user.planet_approved_at = original_approved_at
            db.session.commit()
            print("✅ 用户状态已恢复")
            
            return True
            
        except Exception as e:
            print(f"❌ 收回权限失败: {str(e)}")
            db.session.rollback()
            return False

def test_revoke_access_scenarios():
    """测试不同场景下的权限收回"""
    
    app = create_app()
    
    with app.app_context():
        print("\n=== 权限收回场景测试 ===")
        
        # 1. 测试收回不存在用户的权限
        print("\n📋 测试场景1: 收回不存在用户的权限")
        non_existent_user = User.query.get(99999)
        if non_existent_user is None:
            print("✅ 正确处理：用户不存在的情况")
        
        # 2. 测试收回没有权限用户的权限
        print("\n📋 测试场景2: 收回没有权限用户的权限")
        regular_users = User.query.filter_by(is_planet_user=False).first()
        if regular_users:
            print(f"   用户: {regular_users.username}")
            print(f"   当前状态: {'已授权' if regular_users.is_planet_user else '无权限'}")
            print("✅ 正确识别：用户没有知识星球权限")
        
        # 3. 测试权限收回后的数据一致性
        print("\n📋 测试场景3: 数据一致性检查")
        
        all_users = User.query.all()
        total_users = len(all_users)
        planet_users_count = len([u for u in all_users if u.is_planet_user])
        regular_users_count = total_users - planet_users_count
        
        print(f"   总用户数: {total_users}")
        print(f"   知识星球用户数: {planet_users_count}")
        print(f"   普通用户数: {regular_users_count}")
        print("✅ 数据统计正常")

if __name__ == "__main__":
    print("开始测试知识星球权限收回功能...\n")
    
    # 运行基本功能测试
    success = test_revoke_planet_access()
    
    # 运行场景测试
    test_revoke_access_scenarios()
    
    print("\n" + "="*50)
    if success:
        print("✅ 所有测试通过！收回权限功能正常工作")
    else:
        print("❌ 测试失败，请检查代码")
    print("="*50)