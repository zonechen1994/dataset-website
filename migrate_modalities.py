#!/usr/bin/env python3
"""
将配置文件中的模态类型迁移到数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Modality
from config import config

def migrate_modalities():
    """将配置文件中的模态类型迁移到数据库"""
    app = create_app('development')
    
    with app.app_context():
        print("🔄 开始迁移模态类型到数据库...")
        
        # 创建模态表
        db.create_all()
        
        # 获取配置中的模态类型
        modalities_config = config['default'].DATA_MODALITIES
        
        # 分组映射
        category_mapping = {
            '医学影像': '医学影像',
            'CT': '医学影像',
            'MRI': '医学影像',
            'PET': '医学影像',
            'PET/CT': '医学影像',
            'X光': '医学影像',
            '超声': '医学影像',
            '内窥镜': '其他检查',
            '病理学': '其他检查',
            '实验室检查': '实验室检查',
            '基因检测': '实验室检查',
            '功能检查': '功能检查',
            '心电图': '功能检查',
            '脑电图': '功能检查',
            '电子病历': '其他检查',
            '多模态': '其他检查'
        }
        
        created_count = 0
        updated_count = 0
        
        for code, name in modalities_config.items():
            # 检查是否已存在
            existing = Modality.query.filter_by(code=code).first()
            
            if existing:
                # 更新现有记录
                existing.name = name
                existing.category = category_mapping.get(code, '其他检查')
                existing.description = f"{name}相关的医学数据"
                updated_count += 1
                print(f"   ✏️  更新: {code} -> {name}")
            else:
                # 创建新记录
                modality = Modality(
                    code=code,
                    name=name,
                    category=category_mapping.get(code, '其他检查'),
                    description=f"{name}相关的医学数据"
                )
                db.session.add(modality)
                created_count += 1
                print(f"   ✅ 创建: {code} -> {name}")
        
        # 提交更改
        db.session.commit()
        
        print(f"\n🎉 迁移完成！")
        print(f"   📝 创建: {created_count} 个模态类型")
        print(f"   ✏️  更新: {updated_count} 个模态类型")
        
        # 显示最终统计
        total_modalities = Modality.query.count()
        print(f"   📊 数据库中总计: {total_modalities} 个模态类型")
        
        # 按分组显示
        print(f"\n📋 按分组统计:")
        categories = db.session.query(Modality.category, db.func.count(Modality.id)).group_by(Modality.category).all()
        for category, count in categories:
            print(f"   • {category}: {count} 个")

if __name__ == "__main__":
    migrate_modalities()