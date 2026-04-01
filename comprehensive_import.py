#!/usr/bin/env python3
"""
全面扫描并导入所有可能的数据集MD文件
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

def is_valid_dataset_file(file_path):
    """检查文件是否是有效的数据集文件"""
    # 排除的文件（文档类文件）
    exclude_files = [
        'README.md', 'DEPLOYMENT.md', 'IMAGE_FEATURES.md', 
        'COLOR_IMPROVEMENTS.md', 'CODE_BLOCK_FIX.md',
        'USER_SYSTEM_README.md', 'KNOWLEDGE_PLANET_DESIGN.md',
        'database_design.md', 'CLAUDE.md', 'manual_dataset_template.md'
    ]
    
    filename = os.path.basename(file_path)
    
    # 排除文档类文件
    if filename in exclude_files:
        return False
    
    # 检查文件内容是否包含数据集信息
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 基本检查：是否包含数据集相关关键词
        dataset_keywords = ['数据集', 'dataset', '维度', '模态', '任务类型', 'modality', 'task_type']
        has_keywords = any(keyword in content.lower() for keyword in dataset_keywords)
        
        # 检查是否有表格或结构化信息
        has_structure = '|' in content or '```' in content
        
        # 排除明显的模板或提取失败的文件
        is_template = '待填写' in content or '待确认' in content
        is_empty_extraction = content.strip() == '' or len(content) < 100
        
        return has_keywords and has_structure and not is_template and not is_empty_extraction
        
    except Exception:
        return False

def comprehensive_import():
    """全面导入所有数据集文件"""
    
    base_path = '/Users/chenziqiang/Desktop/数据集md样例'
    
    # 收集所有可能的数据集文件
    potential_files = []
    
    # 扫描所有MD文件
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                if is_valid_dataset_file(file_path):
                    potential_files.append(file_path)
    
    print(f"发现 {len(potential_files)} 个可能的数据集文件:")
    for i, file_path in enumerate(potential_files, 1):
        relative_path = os.path.relpath(file_path, base_path)
        print(f"{i:2d}. {relative_path}")
    
    app = create_app('development')
    
    with app.app_context():
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for file_path in potential_files:
            relative_path = os.path.relpath(file_path, base_path)
            print(f"\n正在处理: {relative_path}")
            
            try:
                # 尝试解析文件
                dataset_data = parse_markdown_file(file_path)
                
                # 检查是否有足够的数据
                if not dataset_data.get('name') or dataset_data.get('name').strip() == '':
                    # 尝试从文件名生成名称
                    filename = os.path.basename(file_path)
                    dataset_data['name'] = filename.replace('.md', '').replace('_数据集介绍', '').replace('_', ' ')
                
                # 检查是否已存在同名数据集
                existing = Dataset.query.filter_by(name=dataset_data['name']).first()
                if existing:
                    print(f"  -> 数据集 '{dataset_data['name']}' 已存在，跳过")
                    skipped_count += 1
                    continue
                
                # 创建数据集
                dataset = Dataset()
                
                # 设置基本信息
                for field, value in dataset_data.items():
                    if hasattr(dataset, field) and value is not None:
                        if field == 'publication_date' and isinstance(value, str) and value.strip():
                            try:
                                # 处理日期格式
                                if len(value.strip()) == 4 and value.strip().isdigit():
                                    value = f"{value.strip()}-01-01"
                                dataset.publication_date = datetime.strptime(value, '%Y-%m-%d').date()
                            except:
                                dataset.publication_date = None
                        else:
                            setattr(dataset, field, value)
                
                # 确保必填字段有值
                if not dataset.description:
                    dataset.description = f"从文件 {relative_path} 导入的数据集"
                
                if not dataset.organ_category:
                    # 根据文件路径推断器官分类
                    if 'fubu' in file_path:
                        dataset.organ_category = 'fubu'
                    elif 'gutou' in file_path:
                        dataset.organ_category = 'gutou'
                    elif 'neikuijing' in file_path:
                        dataset.organ_category = 'neikuijing'
                    elif 'quanshen' in file_path:
                        dataset.organ_category = 'quanshen'
                    else:
                        dataset.organ_category = 'quanshen'  # 默认
                
                db.session.add(dataset)
                db.session.commit()
                
                imported_count += 1
                print(f"  -> ✓ 成功导入: {dataset.name} (ID: {dataset.id})")
                
            except Exception as e:
                db.session.rollback()
                error_count += 1
                print(f"  -> ✗ 导入失败: {str(e)}")
        
        print(f"\n{'='*60}")
        print(f"导入完成统计:")
        print(f"  成功导入: {imported_count} 个")
        print(f"  已存在跳过: {skipped_count} 个") 
        print(f"  导入失败: {error_count} 个")
        
        # 显示最终数据集总数
        total_count = Dataset.query.count()
        print(f"  数据库总数: {total_count} 个数据集")
        
        # 列出所有数据集
        print(f"\n所有数据集列表:")
        datasets = Dataset.query.order_by(Dataset.name).all()
        for i, dataset in enumerate(datasets, 1):
            print(f"{i:2d}. {dataset.name} ({dataset.organ_category})")

if __name__ == '__main__':
    comprehensive_import()