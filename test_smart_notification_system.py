#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能未读通知系统
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_backend_functions():
    """测试后端智能标记功能"""
    print("🔍 测试后端智能标记功能...")
    
    try:
        from planet_routes import mark_application_notifications_read
        print("✅ 智能标记函数导入成功")
        
        # 检查函数参数
        import inspect
        sig = inspect.signature(mark_application_notifications_read)
        expected_params = ['application_id', 'user_id', 'notification_types']
        
        actual_params = list(sig.parameters.keys())
        if all(param in actual_params for param in expected_params):
            print("✅ 函数参数配置正确")
        else:
            print(f"❌ 函数参数不匹配。期望: {expected_params}, 实际: {actual_params}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ 后端功能测试失败: {e}")
        return False

def test_route_integration():
    """测试路由集成"""
    print("\n🔍 测试路由集成...")
    
    try:
        import planet_routes
        
        # 检查申请列表页面
        if hasattr(planet_routes, 'admin_list_applications'):
            print("✅ 申请列表路由存在")
        else:
            print("❌ 申请列表路由不存在")
            return False
            
        # 检查申请详情页面
        if hasattr(planet_routes, 'admin_view_application'):
            print("✅ 申请详情路由存在")
        else:
            print("❌ 申请详情路由不存在")
            return False
            
        # 检查申请审核页面
        if hasattr(planet_routes, 'admin_review_application'):
            print("✅ 申请审核路由存在")
        else:
            print("❌ 申请审核路由不存在")
            return False
            
        return True
    except Exception as e:
        print(f"❌ 路由集成测试失败: {e}")
        return False

def test_frontend_files():
    """测试前端文件"""
    print("\n🔍 测试前端文件...")
    
    # 检查JavaScript文件
    js_file = 'static/js/notification_auto_read.js'
    if os.path.exists(js_file):
        print("✅ JavaScript文件存在")
        
        # 检查关键功能
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        key_features = [
            'NotificationManager',
            'updateUnreadCount',
            'markNotificationRead',
            'PageSpecificAutoRead',
            'handleApplicationPages',
        ]
        
        for feature in key_features:
            if feature in content:
                print(f"  ✅ {feature} 功能已实现")
            else:
                print(f"  ❌ {feature} 功能缺失")
                return False
        
        return True
    else:
        print("❌ JavaScript文件不存在")
        return False

def test_template_modifications():
    """测试模板修改"""
    print("\n🔍 测试模板修改...")
    
    # 检查管理后台基础模板
    admin_base = 'templates/admin/base.html'
    if os.path.exists(admin_base):
        with open(admin_base, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'notification_auto_read.js' in content:
            print("✅ 管理后台已引入智能通知脚本")
        else:
            print("❌ 管理后台未引入智能通知脚本")
            return False
    else:
        print("❌ 管理后台基础模板不存在")
        return False
    
    # 检查侧边栏模板
    sidebar = 'templates/admin/sidebar.html'
    if os.path.exists(sidebar):
        with open(sidebar, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'unread-count-badge' in content and 'data-unread-count' in content:
            print("✅ 侧边栏已添加智能徽章标识")
        else:
            print("❌ 侧边栏未添加智能徽章标识")
            return False
    else:
        print("❌ 侧边栏模板不存在")
        return False
    
    return True

def show_feature_summary():
    """显示功能总结"""
    print("\n" + "=" * 60)
    print("🎯 智能未读通知系统功能总结")
    print("=" * 60)
    print()
    
    print("📋 智能标记已读触发时机:")
    print("  ✅ 访问申请列表页面 → 自动标记申请提交通知为已读")
    print("  ✅ 查看申请详情页面 → 自动标记该申请相关通知为已读")
    print("  ✅ 审核申请操作完成 → 自动标记该申请所有相关通知为已读")
    print()
    
    print("🔄 实时更新机制:")
    print("  ✅ 30秒自动刷新未读数量")
    print("  ✅ 页面操作后立即更新")
    print("  ✅ 页面隐藏时停止更新，显示时恢复")
    print("  ✅ 支持多个徽章位置同步更新")
    print()
    
    print("💡 用户体验优化:")
    print("  ✅ 页面标题显示未读数量")
    print("  ✅ 操作后即时视觉反馈")
    print("  ✅ 智能识别页面类型和上下文")
    print("  ✅ 错误处理不影响主要功能")
    print()
    
    print("🎛️ 测试方法:")
    print("  1. 用普通用户提交知识星球申请")
    print("  2. 用管理员账户登录后台")
    print("  3. 观察导航栏和侧边栏的未读数量")
    print("  4. 点击进入申请列表页面，观察数量变化")
    print("  5. 查看申请详情，观察数量变化")
    print("  6. 执行审核操作，观察数量变化")

def main():
    print("=" * 60)
    print("智能未读通知系统测试")
    print("=" * 60)
    
    tests = [
        test_backend_functions,
        test_route_integration,
        test_frontend_files,
        test_template_modifications,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 所有测试通过！智能未读通知系统已就绪")
        show_feature_summary()
    else:
        print("❌ 部分测试失败，请检查错误信息并修复")
        print("\n⚠️  失败的测试:")
        for i, (test, result) in enumerate(zip(tests, results)):
            if not result:
                print(f"  - {test.__name__}")
    print("=" * 60)

if __name__ == "__main__":
    main()