#!/usr/bin/env python3
"""
删除刚才添加的8个虚假数据集，恢复真实数据
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, Dataset

def delete_fake_datasets():
    """删除刚才添加的8个虚假数据集"""
    
    # 需要删除的虚假数据集名称列表
    fake_datasets = [
        "BRATS2021 脑肿瘤分割挑战数据集",
        "LUNA16 肺结节检测数据集",
        "ISIC2020 皮肤病变分类数据集",
        "DRIVE 视网膜血管分割数据集",
        "COVID-19 CT分割数据集",
        "OASIS 大脑MRI纵向研究数据集",
        "LIDC-IDRI 肺部影像数据库",
        "NIH 胸部X光数据集"
    ]
    
    app = create_app('development')
    
    with app.app_context():
        deleted_count = 0
        
        for dataset_name in fake_datasets:
            dataset = Dataset.query.filter_by(name=dataset_name).first()
            if dataset:
                try:
                    db.session.delete(dataset)
                    db.session.commit()
                    deleted_count += 1
                    print(f"✓ 已删除虚假数据集: {dataset_name}")
                except Exception as e:
                    db.session.rollback()
                    print(f"✗ 删除失败 '{dataset_name}': {str(e)}")
            else:
                print(f"- 未找到数据集: {dataset_name}")
        
        print(f"\n=== 删除完成 ===")
        print(f"已删除 {deleted_count} 个虚假数据集")
        
        # 显示当前剩余的真实数据集
        remaining_datasets = Dataset.query.order_by(Dataset.name).all()
        print(f"数据库中剩余的真实数据集总数: {len(remaining_datasets)}")
        
        print("\n剩余的真实数据集:")
        for i, dataset in enumerate(remaining_datasets, 1):
            print(f"{i:2d}. {dataset.name}")

if __name__ == '__main__':
    delete_fake_datasets()