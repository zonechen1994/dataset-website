#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版数据集管理系统启动脚本
支持完整的用户注册登录和管理员用户管理功能
"""

from app_enhanced import create_app

def main():
    print("🚀 启动增强版数据集管理系统...")
    print("=" * 60)
    
    # 创建应用
    app = create_app('development')
    
    print("✅ 系统功能：")
    print("  📊 数据集浏览和管理")
    print("  👥 用户注册和登录系统")
    print("  🔐 管理员用户管理")
    print("  📝 权限控制和路由保护")
    print("  🔧 系统配置管理")
    print()
    
    print("🔑 默认管理员账户：")
    print("  用户名：admin")
    print("  密码：admin123")
    print()
    
    print("🌐 访问地址：")
    print("  网站首页：http://localhost:5002/")
    print("  用户登录：http://localhost:5002/login")
    print("  用户注册：http://localhost:5002/register")
    print("  管理后台：http://localhost:5002/admin")
    print("  用户管理：http://localhost:5002/admin/users")
    print()
    
    print("📋 主要功能：")
    print("  1. 普通用户可以注册账户、浏览数据集")
    print("  2. 管理员可以管理数据集、用户和系统配置")  
    print("  3. 支持用户权限控制和角色管理")
    print("  4. 提供完整的用户个人资料管理")
    print()
    
    print("=" * 60)
    print("🎉 系统启动中，请稍候...")
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5002)
    
if __name__ == '__main__':
    main()
