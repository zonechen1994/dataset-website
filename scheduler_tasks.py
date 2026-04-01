"""
知识星球权限到期管理 - 定时任务模块

功能：
1. 每日检查并撤销过期用户权限
2. 发送权限到期提醒（提前7天、3天、1天）
3. 调度器初始化和配置

依赖：
- APScheduler: 定时任务调度
- timezone_utils: 中国时区时间处理
- models: 数据库模型（User, PlanetExpiryNotification）
- email_service: 邮件发送（Phase 4实现）

调度时间：
- 权限检查：每天凌晨2:00
- 到期提醒：每天上午10:00
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging

# 配置日志
logger = logging.getLogger(__name__)


def check_and_revoke_expired_permissions():
    """
    检查并撤销过期用户的知识星球权限
    
    执行频率：每天凌晨2:00
    
    执行逻辑：
    1. 查找所有已过期但权限仍开启的用户（排除永久会员）
    2. 撤销权限（is_planet_user = False）
    3. 发送到期通知邮件
    4. 记录通知发送历史到 planet_expiry_notifications 表
    
    Returns:
        int: 撤销权限的用户数量
    """
    try:
        from models import User, PlanetExpiryNotification, db
        from timezone_utils import get_china_datetime
        
        current_time = get_china_datetime()
        
        # 查找所有已过期但权限仍开启的用户
        # 条件：is_planet_user=True 且 planet_expiry_date < 当前时间 且 expiry_date 非空（排除永久会员）
        expired_users = User.query.filter(
            User.is_planet_user == True,
            User.planet_expiry_date < current_time,
            User.planet_expiry_date.isnot(None)  # 排除永久会员（永久会员的expiry_date为NULL）
        ).all()
        
        revoked_count = 0
        
        for user in expired_users:
            logger.info(f"撤销过期用户权限: {user.username} (ID: {user.id}), 到期时间: {user.planet_expiry_date}")
            
            # 撤销权限
            user.is_planet_user = False
            
            # Phase 4: 发送权限到期通知邮件
            try:
                from email_service import send_permission_expired_email
                send_permission_expired_email(user)
            except Exception as e:
                logger.error(f"发送到期通知邮件失败 (用户ID: {user.id}): {str(e)}")
            
            # 记录通知发送（即使邮件发送失败也记录，避免重复处理）
            notification = PlanetExpiryNotification(
                user_id=user.id,
                notification_type='expired',
                expiry_date=user.planet_expiry_date,
                days_before_expiry=None  # 到期当天，不需要提前天数
            )
            db.session.add(notification)
            
            revoked_count += 1
        
        # 提交所有更改
        db.session.commit()
        
        if revoked_count > 0:
            logger.info(f"✅ 权限到期检查完成: 已撤销 {revoked_count} 个过期用户的权限")
        else:
            logger.info("✅ 权限到期检查完成: 无过期用户")
        
        return revoked_count
        
    except Exception as e:
        logger.error(f"❌ 权限到期检查任务执行失败: {str(e)}", exc_info=True)
        try:
            from models import db
            db.session.rollback()
        except:
            pass
        return 0


def send_expiry_reminders():
    """
    发送权限到期提醒邮件
    
    执行频率：每天上午10:00
    
    提醒时间点：到期前7天、3天、1天
    
    执行逻辑：
    1. 对于每个时间点（7天、3天、1天）：
       - 查找对应时间点即将到期的用户
       - 检查是否已发送过该时间点的提醒（避免重复）
       - 发送提醒邮件
       - 记录发送历史
    
    Returns:
        int: 发送提醒的总数
    """
    try:
        from models import User, PlanetExpiryNotification, db
        from timezone_utils import get_china_datetime
        
        current_time = get_china_datetime()
        reminder_days = [7, 3, 1]  # 提前7天、3天、1天提醒
        total_reminders_sent = 0
        
        for days in reminder_days:
            # 计算目标日期范围
            target_date = current_time + timedelta(days=days)
            target_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            target_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # 查找即将到期的用户
            # 条件：is_planet_user=True 且 到期日期在目标日期范围内
            expiring_users = User.query.filter(
                User.is_planet_user == True,
                User.planet_expiry_date >= target_start,
                User.planet_expiry_date <= target_end
            ).all()
            
            logger.info(f"检查{days}天后到期的用户: 找到 {len(expiring_users)} 个用户")
            
            for user in expiring_users:
                # 检查是否已发送过该时间点的提醒
                existing_notification = PlanetExpiryNotification.query.filter_by(
                    user_id=user.id,
                    notification_type='expiring_soon',
                    days_before_expiry=days
                ).first()
                
                if existing_notification:
                    logger.debug(f"用户 {user.username} (ID: {user.id}) 的{days}天提醒已发送，跳过")
                    continue
                
                logger.info(f"发送{days}天到期提醒: {user.username} (ID: {user.id}), 到期时间: {user.planet_expiry_date}")
                
                # Phase 4: 发送权限即将到期提醒邮件
                try:
                    from email_service import send_permission_expiring_soon_email
                    send_permission_expiring_soon_email(user, days)
                except Exception as e:
                    logger.error(f"发送到期提醒邮件失败 (用户ID: {user.id}, 提前{days}天): {str(e)}")
                
                # 记录通知发送
                notification = PlanetExpiryNotification(
                    user_id=user.id,
                    notification_type='expiring_soon',
                    expiry_date=user.planet_expiry_date,
                    days_before_expiry=days
                )
                db.session.add(notification)
                total_reminders_sent += 1
        
        # 提交所有更改
        db.session.commit()
        
        if total_reminders_sent > 0:
            logger.info(f"✅ 到期提醒发送完成: 共发送 {total_reminders_sent} 条提醒")
        else:
            logger.info("✅ 到期提醒检查完成: 无需发送提醒")
        
        return total_reminders_sent
        
    except Exception as e:
        logger.error(f"❌ 到期提醒任务执行失败: {str(e)}", exc_info=True)
        try:
            from models import db
            db.session.rollback()
        except:
            pass
        return 0


def init_scheduler(app):
    """
    初始化定时任务调度器
    
    Args:
        app: Flask应用实例
    
    Returns:
        BackgroundScheduler: 调度器实例
    
    调度计划：
    - check_and_revoke_expired_permissions: 每天凌晨2:00执行
    - send_expiry_reminders: 每天上午10:00执行
    
    注意事项：
    1. 使用 Asia/Shanghai 时区确保时间准确
    2. 调度器在Flask应用启动时自动启动
    3. 如果需要立即测试，可以手动调用任务函数
    """
    try:
        # 创建后台调度器（使用上海时区）
        scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        
        # 任务1: 每天凌晨2:00检查并撤销过期权限
        scheduler.add_job(
            func=check_and_revoke_expired_permissions,
            trigger='cron',
            hour=2,
            minute=0,
            id='check_expired_permissions',
            name='检查并撤销过期权限',
            replace_existing=True  # 如果任务已存在则替换
        )
        logger.info("✅ 定时任务已注册: 检查并撤销过期权限 (每天 02:00)")
        
        # 任务2: 每天上午10:00发送到期提醒
        scheduler.add_job(
            func=send_expiry_reminders,
            trigger='cron',
            hour=10,
            minute=0,
            id='send_expiry_reminders',
            name='发送权限到期提醒',
            replace_existing=True
        )
        logger.info("✅ 定时任务已注册: 发送权限到期提醒 (每天 10:00)")
        
        # 启动调度器
        scheduler.start()
        logger.info("🚀 定时任务调度器已启动")
        
        # 注册应用关闭时的清理函数
        import atexit
        atexit.register(lambda: scheduler.shutdown())
        
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ 定时任务调度器初始化失败: {str(e)}", exc_info=True)
        return None
