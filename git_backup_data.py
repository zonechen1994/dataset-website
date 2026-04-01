#!/usr/bin/env python3
"""
Git 数据备份工具
全量导出数据库为 JSON 文本格式，以便提交到 Git。
解决二进制数据库无法进行版本控制的问题。
"""

import os
import sys
import shutil

# 确保能导入同目录下的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from export_new_data import export_all_new_data
except ImportError:
    print("❌ 错误: 无法导入 export_new_data.py")
    print("请确保此脚本位于 dataset_website 目录下")
    sys.exit(1)

def backup_for_git():
    # 切换到脚本所在目录
    os.chdir(current_dir)
    
    backup_dir = "data_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    print("🚀 [1/3] 开始全量导出数据 (自 2000-01-01 起)...")
    # 导出全量数据，不包含文件（文件太大，不适合放Git，且已有 uploads 目录管理）
    try:
        filename = export_all_new_data(since_date="2000-01-01", include_files=False)
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return

    print("📦 [2/3] 处理备份文件...")
    target_file = os.path.join(backup_dir, "full_dump.json")
    
    if os.path.exists(filename):
        # 如果目标存在，先删除
        if os.path.exists(target_file):
            os.remove(target_file)
        
        # 重命名生成的临时文件为固定文件名
        os.rename(filename, target_file)
        print(f"✅ 数据快照已保存: {target_file}")
    else:
        print("❌ 未找到生成的导出文件")
        return

    print("💾 [3/3] 准备提交...")
    print("\n✅ 成功! 现在你可以安全地执行:")
    print("  git add data_backups/full_dump.json")
    print("  git commit -m 'update data snapshot'")

if __name__ == "__main__":
    backup_for_git()
