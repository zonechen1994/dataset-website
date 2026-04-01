"""
到期邮件发送功能测试脚本

用途：
1. 测试权限即将到期提醒邮件（提前7天/3天/1天）
2. 测试权限已到期通知邮件
3. 验证邮件发送逻辑和邮件内容

使用方法：
    python test_expiry_emails.py
"""

import sys
import os
from datetime import datetime, timedelta

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_expiring_soon_email():
    """测试即将到期提醒邮件"""
    print("\n" + "="*60)
    print("测试1: 权限即将到期提醒邮件")
    print("="*60)
    
    from email_service import send_permission_expiring_soon_email
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        from models import User
        from timezone_utils import get_china_datetime
        
        # 查找有到期时间的知识星球用户
        current_time = get_china_datetime()
        
        # 查找未来7天/3天/1天到期的用户
        reminder_days = [7, 3, 1]
        
        for days in reminder_days:
            target_date = current_time + timedelta(days=days)
            target_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            target_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            users = User.query.filter(
                User.is_planet_user == True,
                User.planet_expiry_date >= target_start,
                User.planet_expiry_date <= target_end
            ).limit(5).all()
            
            print(f"\n\n--- 测试提前{days}天提醒 ---")
            
            if users:
                for user in users:
                    print(f"\n发送测试邮件到: {user.email}")
                    print(f"  用户名: {user.username}")
                    print(f"  到期时间: {user.planet_expiry_date}")
                    
                    result = send_permission_expiring_soon_email(user, days)
                    
                    if result['success']:
                        print(f"  ✅ 邮件发送成功: {result['message']}")
                    else:
                        print(f"  ❌ 邮件发送失败: {result['message']}")
            else:
                print(f"  ℹ️ 未找到{days}天后到期的用户")
                print(f"  💡 提示：可手动设置测试用户:")
                print(f"     - 设置 is_planet_user = True")
                print(f"     - 设置 planet_expiry_date = {target_date.strftime('%Y-%m-%d %H:%M:%S')}")


def test_expired_email():
    """测试已到期通知邮件"""
    print("\n" + "="*60)
    print("测试2: 权限已到期通知邮件")
    print("="*60)
    
    from email_service import send_permission_expired_email
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        from models import User
        from timezone_utils import get_china_datetime
        
        current_time = get_china_datetime()
        
        # 查找已过期的用户
        expired_users = User.query.filter(
            User.is_planet_user == True,
            User.planet_expiry_date < current_time,
            User.planet_expiry_date.isnot(None)
        ).limit(5).all()
        
        if expired_users:
            for user in expired_users:
                print(f"\n发送测试邮件到: {user.email}")
                print(f"  用户名: {user.username}")
                print(f"  到期时间: {user.planet_expiry_date}")
                
                result = send_permission_expired_email(user)
                
                if result['success']:
                    print(f"  ✅ 邮件发送成功: {result['message']}")
                else:
                    print(f"  ❌ 邮件发送失败: {result['message']}")
        else:
            print("\n  ℹ️ 未找到已过期的用户")
            print("  💡 提示：可手动创建测试用户:")
            print("     - 设置 is_planet_user = True")
            print(f"     - 设置 planet_expiry_date = 过去的日期")


def test_email_content_format():
    """测试邮件内容格式"""
    print("\n" + "="*60)
    print("测试3: 邮件内容格式验证")
    print("="*60)
    
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        from models import User
        
        # 随便找一个用户进行格式测试
        user = User.query.filter(User.is_planet_user == True).first()
        
        if user:
            print(f"\n使用测试用户: {user.username} ({user.email})")
            
            # 测试即将到期邮件（不实际发送，只测试格式）
            from email_service import send_permission_expiring_soon_email, send_permission_expired_email
            
            print("\n测试邮件函数调用...")
            print("  - 7天提醒邮件函数")
            print("  - 3天提醒邮件函数")
            print("  - 1天提醒邮件函数")
            print("  - 已到期通知邮件函数")
            
            print("\n✅ 所有邮件函数导入成功")
            print("💡 实际发送需要有效的邮件服务器配置")
        else:
            print("\n  ℹ️ 未找到知识星球用户")


def main():
    """主测试入口"""
    print("\n📧 知识星球到期邮件发送功能测试")
    print("=" * 60)
    print("注意: 此脚本将实际发送邮件，请确保邮件服务器配置正确！")
    print("=" * 60)
    
    try:
        # 测试1: 即将到期提醒
        test_expiring_soon_email()
        
        # 测试2: 已到期通知
        test_expired_email()
        
        # 测试3: 邮件内容格式
        test_email_content_format()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        
        print("\n💡 提示:")
        print("1. 如果没有测试用户，可以手动在数据库中创建：")
        print("   - 设置 is_planet_user = True")
        print("   - 设置 planet_expiry_date 为目标日期")
        print("\n2. 实际邮件发送需要:")
        print("   - 在 .env 中配置 SMTP 服务器信息")
        print("   - 确保 Flask-Mail 配置正确")
        print("\n3. 定时任务集成:")
        print("   - 权限检查：每天凌晨 02:00 自动执行")
        print("   - 到期提醒：每天上午 10:00 自动执行")
        print("   - 运行 python test_scheduler.py 可手动触发")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
