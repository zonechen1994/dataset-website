#!/usr/bin/env python3
"""
更新分类选项：
1. 骨头 -> 骨科
2. 添加病理模态
3. 删除网格模型
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, Category, Modality

def update_classifications():
    """更新分类选项"""
    
    app = create_app('development')
    
    with app.app_context():
        # 1. 修改器官分类：骨头 -> 骨科
        print("=== 修改器官分类 ===")
        bone_category = Category.query.filter_by(code='gutou').first()
        if bone_category:
            bone_category.name = '骨科'
            bone_category.description = '骨科、骨骼、关节等'
            print(f"✓ 已修改: {bone_category.code} -> {bone_category.name}")
        else:
            print("- 未找到骨头分类")
        
        # 2. 添加病理模态
        print("\n=== 添加病理模态 ===")
        existing_pathology = Modality.query.filter_by(code='pathology').first()
        if not existing_pathology:
            pathology_modality = Modality(
                code='pathology',
                name='病理',
                category='病理',
                description='病理切片、组织病理学'
            )
            db.session.add(pathology_modality)
            print("✓ 已添加病理模态")
        else:
            print("- 病理模态已存在")
        
        # 3. 删除网格模型
        print("\n=== 删除网格模型 ===")
        mesh_modality = Modality.query.filter_by(code='mesh').first()
        if mesh_modality:
            db.session.delete(mesh_modality)
            print("✓ 已删除网格模型")
        else:
            print("- 网格模型不存在")
        
        try:
            db.session.commit()
            print("\n=== 更新完成 ===")
            
            # 显示最终的分类选项
            print("\n=== 当前器官分类 ===")
            categories = Category.query.order_by(Category.name).all()
            for c in categories:
                print(f"- {c.name}")
            
            print(f"\n=== 当前模态类型 ({Modality.query.count()}个) ===")
            modalities = Modality.query.order_by(Modality.name).all()
            for m in modalities:
                print(f"- {m.name}")
                
        except Exception as e:
            db.session.rollback()
            print(f"更新失败: {str(e)}")

if __name__ == '__main__':
    update_classifications()