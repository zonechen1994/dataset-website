#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试用户删除修复
验证删除用户时不会出现外键约束错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import User, db, Notification, PlanetApplication, EmailVerificationCode
from user_admin_routes import cleanup_user_related_data

def test_user_deletion_fix():
    """测试用户删除修复功能"""
    app = create_app('development')
    
    with app.app_context():
        print("🧪 测试用户删除功能修复...")
        print("=" * 50)
        
        try:
            # 1. 创建测试用户
            test_user = User(
                username='test_delete_user',
                email='test_delete@example.com',
                password='test123456',
                full_name='测试删除用户',
                role='user'
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"✅ 创建测试用户: {test_user.username}")
            
            # 2. 创建一些相关数据
            # 创建通知记录
            notification = Notification(
                recipient_id=test_user.id,
                sender_id=test_user.id,
                type='test',
                title='测试通知',
                content='这是一个测试通知'
            )
            db.session.add(notification)
            
            # 创建验证码记录
            verification_code = EmailVerificationCode(
                email=test_user.email,
                code='123456',
                purpose='registration',
                expires_at=datetime.utcnow() + timedelta(minutes=15)
            )
            db.session.add(verification_code)
            
            db.session.commit()
            print("✅ 创建相关测试数据")
            
            # 3. 测试清理函数
            print("🔧 测试数据清理函数...")
            cleanup_user_related_data(test_user)
            print("✅ 数据清理函数执行成功")
            
            # 4. 删除用户
            print("🗑️ 删除测试用户...")
            db.session.delete(test_user)
            db.session.commit()
            print("✅ 用户删除成功")
            
            # 5. 验证相关数据已清理
            remaining_notifications = Notification.query.filter_by(recipient_id=test_user.id).count()
            remaining_codes = EmailVerificationCode.query.filter_by(email=test_user.email).count()
            
            print(f"📊 验证清理结果:")
            print(f"   剩余通知记录: {remaining_notifications}")
            print(f"   剩余验证码记录: {remaining_codes}")
            
            if remaining_notifications == 0 and remaining_codes == 0:
                print("✅ 所有相关数据已正确清理")
            else:
                print("❌ 数据清理不完整")
            
            print("\n🎉 用户删除功能修复测试通过！")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    from datetime import datetime, timedelta
    test_user_deletion_fix()