#!/usr/bin/env python3
"""
知识星球系统启动脚本
"""

import os
import sys

def main():
    print("🌟 启动知识星球系统...")
    print("=" * 50)
    
    # 检查工作目录
    if not os.path.exists("app_enhanced.py"):
        print("❌ 请在dataset_website目录下运行此脚本")
        return
    
    # 检查数据库是否存在
    if not os.path.exists("instance/database.db"):
        print("⚠️  数据库不存在，请先运行: python create_database.py")
        return
    
    print("🚀 正在启动Flask应用...")
    print("\n📍 访问地址: http://localhost:5003")
    print("👤 登录信息:")
    print("   管理员: admin / admin123") 
    print("   普通用户: user / admin123")
    print("\n🌟 功能说明:")
    print("   - 管理员可以审核知识星球申请")
    print("   - 普通用户可以申请知识星球权限")
    print("   - 知识星球用户可以下载数据集")
    print("   - 实时通知系统")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 启动应用
    try:
        from app_enhanced import create_app
        
        app = create_app('development')
        app.run(debug=True, host='0.0.0.0', port=5003)
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"\n❌ 应用启动失败: {e}")
        print("\n🔧 可能的解决方案:")
        print("   1. 检查端口5003是否被占用")
        print("   2. 重新创建数据库: python create_database.py")
        print("   3. 检查Python环境和依赖")

if __name__ == '__main__':
    main()