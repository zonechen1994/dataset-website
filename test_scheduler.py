"""
定时任务手动测试脚本

用途：
1. 手动触发定时任务函数，验证其功能
2. 无需等待实际调度时间即可测试
3. 检查任务执行逻辑和数据库操作

测试内容：
- check_and_revoke_expired_permissions(): 权限到期检查
- send_expiry_reminders(): 到期提醒发送

使用方法：
    python test_scheduler.py
"""

import sys
import os
from datetime import datetime, timedelta

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_check_expired_permissions():
    """测试权限到期检查任务"""
    print("\n" + "="*60)
    print("测试1: 权限到期检查任务")
    print("="*60)
    
    from scheduler_tasks import check_and_revoke_expired_permissions
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        from models import User, PlanetExpiryNotification, db
        from timezone_utils import get_china_datetime
        
        # 查询当前状态
        current_time = get_china_datetime()
        print(f"\n当前时间: {current_time}")
        
        # 统计过期用户
        expired_users = User.query.filter(
            User.is_planet_user == True,
            User.planet_expiry_date < current_time,
            User.planet_expiry_date.isnot(None)
        ).all()
        
        print(f"找到 {len(expired_users)} 个过期用户（权限仍开启）:")
        for user in expired_users:
            print(f"  - 用户: {user.username} (ID: {user.id})")
            print(f"    到期时间: {user.planet_expiry_date}")
            print(f"    当前状态: is_planet_user = {user.is_planet_user}")
        
        if len(expired_users) == 0:
            print("  ℹ️ 提示: 当前没有过期用户。可以手动创建测试数据：")
            print("     1. 在数据库中找到一个 is_planet_user=True 的用户")
            print("     2. 将其 planet_expiry_date 设置为过去的日期")
            print("     3. 重新运行此测试")
        
        # 执行任务
        print("\n正在执行权限到期检查任务...")
        revoked_count = check_and_revoke_expired_permissions()
        
        print(f"\n✅ 任务执行完成！撤销了 {revoked_count} 个用户的权限")
        
        # 验证结果
        if revoked_count > 0:
            print("\n查询已撤销权限的用户:")
            for user in expired_users[:revoked_count]:
                user_check = User.query.get(user.id)
                print(f"  - 用户: {user_check.username}")
                print(f"    is_planet_user: {user_check.is_planet_user} (应为 False)")
                
                # 检查通知记录
                notification = PlanetExpiryNotification.query.filter_by(
                    user_id=user.id,
                    notification_type='expired'
                ).order_by(PlanetExpiryNotification.sent_at.desc()).first()
                
                if notification:
                    print(f"    通知记录: ✅ 已创建 (发送时间: {notification.sent_at})")
                else:
                    print(f"    通知记录: ❌ 未找到")


def test_expiry_reminders():
    """测试到期提醒任务"""
    print("\n" + "="*60)
    print("测试2: 到期提醒任务")
    print("="*60)
    
    from scheduler_tasks import send_expiry_reminders
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        from models import User, PlanetExpiryNotification, db
        from timezone_utils import get_china_datetime
        
        current_time = get_china_datetime()
        print(f"\n当前时间: {current_time}")
        
        # 检查各个提醒时间点的用户
        reminder_days = [7, 3, 1]
        
        for days in reminder_days:
            target_date = current_time + timedelta(days=days)
            target_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            target_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            expiring_users = User.query.filter(
                User.is_planet_user == True,
                User.planet_expiry_date >= target_start,
                User.planet_expiry_date <= target_end
            ).all()
            
            print(f"\n{days}天后到期的用户 ({target_date.strftime('%Y-%m-%d')}): {len(expiring_users)} 个")
            
            for user in expiring_users:
                # 检查是否已发送过提醒
                existing = PlanetExpiryNotification.query.filter_by(
                    user_id=user.id,
                    notification_type='expiring_soon',
                    days_before_expiry=days
                ).first()
                
                status = "已发送" if existing else "待发送"
                print(f"  - {user.username} (ID: {user.id}) - 到期: {user.planet_expiry_date} [{status}]")
        
        # 统计总体情况
        total_users = User.query.filter(User.is_planet_user == True).count()
        print(f"\n当前知识星球用户总数: {total_users}")
        
        if total_users == 0:
            print("  ℹ️ 提示: 当前没有知识星球用户。可以：")
            print("     1. 通过申请流程创建用户")
            print("     2. 手动设置用户的 planet_expiry_date 为未来日期")
        
        # 执行任务
        print("\n正在执行到期提醒任务...")
        reminders_sent = send_expiry_reminders()
        
        print(f"\n✅ 任务执行完成！发送了 {reminders_sent} 条提醒")
        
        # 验证结果
        if reminders_sent > 0:
            print("\n最近发送的提醒记录:")
            recent_notifications = PlanetExpiryNotification.query.filter_by(
                notification_type='expiring_soon'
            ).order_by(PlanetExpiryNotification.sent_at.desc()).limit(5).all()
            
            for notif in recent_notifications:
                user = User.query.get(notif.user_id)
                print(f"  - 用户: {user.username}, 提前{notif.days_before_expiry}天, 发送时间: {notif.sent_at}")


def main():
    """主测试入口"""
    print("\n🧪 知识星球定时任务手动测试")
    print("=" * 60)
    print("注意: 此脚本将直接操作数据库，请确保在开发环境运行！")
    print("=" * 60)
    
    try:
        # 测试1: 权限到期检查
        test_check_expired_permissions()
        
        # 测试2: 到期提醒
        test_expiry_reminders()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        
        print("\n💡 提示:")
        print("1. 如果没有测试数据，可以手动在数据库中创建：")
        print("   - 设置用户的 is_planet_user=True")
        print("   - 设置 planet_expiry_date 为过去日期（测试过期检查）")
        print("   - 设置 planet_expiry_date 为未来7天/3天/1天（测试提醒）")
        print("\n2. Phase 4 实现邮件服务后，邮件将自动发送")
        print("   当前阶段邮件发送代码已被注释（TODO标记）")
        print("\n3. 定时任务将在应用启动时自动运行：")
        print("   - 权限检查: 每天凌晨 02:00")
        print("   - 到期提醒: 每天上午 10:00")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
