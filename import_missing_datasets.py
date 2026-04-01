#!/usr/bin/env python3
"""
导入缺失的数据集文件
"""

import os
import sys
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, Dataset
from md_parser import parse_markdown_file

def import_missing_datasets():
    """导入缺失的数据集文件"""
    
    # 需要导入的额外文件列表
    additional_files = [
        '/Users/chenziqiang/Desktop/数据集md样例/Cholec80_corrected.md',
        # 可以添加其他完整的数据集文件
    ]
    
    app = create_app('development')
    
    with app.app_context():
        imported_count = 0
        
        for file_path in additional_files:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                continue
                
            try:
                print(f"正在导入: {file_path}")
                
                # 解析MD文件
                dataset_data = parse_markdown_file(file_path)
                
                # 检查是否已存在同名数据集
                existing = None
                if dataset_data.get('name'):
                    existing = Dataset.query.filter_by(name=dataset_data['name']).first()
                
                if existing:
                    print(f"  -> 数据集 '{dataset_data.get('name')}' 已存在，跳过")
                    continue
                
                # 创建新数据集
                dataset = Dataset()
                
                # 设置基本信息
                for field, value in dataset_data.items():
                    if hasattr(dataset, field) and value is not None:
                        if field == 'publication_date' and isinstance(value, str):
                            # 处理日期格式
                            try:
                                if value:
                                    # 如果是年份格式，转换为完整日期
                                    if len(value) == 4 and value.isdigit():
                                        value = f"{value}-01-01"
                                    dataset.publication_date = datetime.strptime(value, '%Y-%m-%d').date()
                            except:
                                dataset.publication_date = None
                        else:
                            setattr(dataset, field, value)
                
                # 确保必填字段有默认值
                if not dataset.name:
                    filename = os.path.basename(file_path)
                    dataset.name = filename.replace('.md', '').replace('_', ' ')
                
                if not dataset.description:
                    dataset.description = f"从文件 {os.path.basename(file_path)} 导入的数据集"
                
                if not dataset.organ_category:
                    dataset.organ_category = 'neikuijing'  # 默认分类
                
                db.session.add(dataset)
                db.session.commit()
                
                imported_count += 1
                print(f"  -> 成功导入数据集: {dataset.name} (ID: {dataset.id})")
                
            except Exception as e:
                db.session.rollback()
                print(f"  -> 导入失败: {str(e)}")
        
        print(f"\n导入完成! 成功导入 {imported_count} 个数据集")
        
        # 显示当前数据集总数
        total_count = Dataset.query.count()
        print(f"数据库中现有数据集总数: {total_count}")

if __name__ == '__main__':
    import_missing_datasets()