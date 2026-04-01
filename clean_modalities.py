#!/usr/bin/env python3
"""
清理和标准化数据库中的模态类型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Dataset

def clean_modalities():
    """清理和标准化模态类型"""
    app = create_app('development')
    
    # 模态类型映射规则
    modality_mapping = {
        'X Ray': 'X光',           # 统一X射线相关
        'MR': 'MRI',              # 统一磁共振
        '下肢': '医学影像',         # 下肢不是模态，改为通用医学影像
    }
    
    with app.app_context():
        print("🧹 开始清理模态类型...")
        
        updated_count = 0
        
        for old_modality, new_modality in modality_mapping.items():
            # 查找需要更新的数据集
            datasets = Dataset.query.filter_by(modality=old_modality).all()
            
            if datasets:
                print(f"\n📝 更新 '{old_modality}' → '{new_modality}'")
                for dataset in datasets:
                    print(f"   • {dataset.name}")
                    dataset.modality = new_modality
                    updated_count += 1
        
        # 提交更改
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ 成功更新 {updated_count} 个数据集的模态类型")
        else:
            print("\n✅ 所有模态类型已经是标准格式")
        
        # 显示清理后的结果
        print("\n📊 清理后的模态类型统计:")
        modalities = db.session.query(Dataset.modality, db.func.count(Dataset.id)).filter(Dataset.modality.isnot(None)).group_by(Dataset.modality).order_by(Dataset.modality).all()
        
        for modality, count in modalities:
            print(f"   • {modality}: {count} 个数据集")

if __name__ == "__main__":
    clean_modalities()