#!/usr/bin/env python3
"""
数据库初始化脚本
遍历现有MD文件，解析并导入数据库
"""

import os
import sys
from pathlib import Path
from flask import Flask

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, Dataset, Author, Category
from md_parser import parse_markdown_file, extract_authors_from_content

def init_database():
    """初始化数据库并导入MD文件数据"""
    app = create_app('development')
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成")
        
        # 初始化分类数据
        init_categories()
        
        # 导入MD文件数据
        import_md_files()
        
        print("数据库初始化完成")

def init_categories():
    """初始化器官分类数据"""
    categories_data = [
        # 原有分类
        {'code': 'fubu', 'name': '腹部', 'description': '腹部相关器官数据集'},
        {'code': 'gutou', 'name': '骨头', 'description': '骨骼系统相关数据集'},
        {'code': 'neikuijing', 'name': '内窥镜', 'description': '内窥镜检查相关数据集'},
        {'code': 'quanshen', 'name': '全身', 'description': '全身扫描相关数据集'},
        
        # 扩展的器官分类
        {'code': 'nabu', 'name': '脑部', 'description': '脑部神经系统数据集'},
        {'code': 'xinzang', 'name': '心脏', 'description': '心脏血管系统数据集'},
        {'code': 'fei', 'name': '肺部', 'description': '肺部呼吸系统数据集'},
        {'code': 'gan', 'name': '肝脏', 'description': '肝脏消化系统数据集'},
        {'code': 'shen', 'name': '肾脏', 'description': '肾脏泌尿系统数据集'},
        {'code': 'yan', 'name': '眼部', 'description': '眼部视觉系统数据集'},
        {'code': 'ruxian', 'name': '乳腺', 'description': '乳腺相关数据集'},
        {'code': 'qianliexian', 'name': '前列腺', 'description': '前列腺相关数据集'},
        {'code': 'zigong', 'name': '子宫', 'description': '子宫妇科系统数据集'}
    ]
    
    for cat_data in categories_data:
        existing = Category.query.filter_by(code=cat_data['code']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    
    db.session.commit()
    print("分类数据初始化完成")

def import_md_files():
    """导入MD文件数据"""
    base_path = Path(__file__).parent.parent  # 回到数据集md样例目录
    md_files = []
    
    # 遍历各个器官分类目录
    for category_dir in ['fubu', 'gutou', 'neikuijing', 'quanshen']:
        category_path = base_path / category_dir
        if category_path.exists():
            for md_file in category_path.glob('*.md'):
                md_files.append(md_file)
    
    print(f"找到 {len(md_files)} 个MD文件")
    
    imported_count = 0
    error_count = 0
    
    for md_file in md_files:
        try:
            print(f"正在处理: {md_file.name}")
            
            # 检查是否已经导入
            existing = Dataset.query.filter_by(name=md_file.stem).first()
            if existing:
                print(f"  跳过：{md_file.name} 已存在")
                continue
            
            # 解析MD文件
            dataset_data = parse_markdown_file(str(md_file))
            
            # 读取文件内容以提取作者信息
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建数据集记录
            dataset = Dataset()
            
            # 设置基本字段
            for field, value in dataset_data.items():
                if hasattr(dataset, field) and value is not None:
                    setattr(dataset, field, value)
            
            db.session.add(dataset)
            db.session.flush()  # 获取数据集ID
            
            # 处理作者信息
            authors_data = extract_authors_from_content(content)
            for author_data in authors_data:
                # 查找或创建作者
                author = Author.query.filter_by(
                    name=author_data['name'],
                    institution=author_data['institution']
                ).first()
                
                if not author:
                    author = Author(**author_data)
                    db.session.add(author)
                    db.session.flush()
                
                # 建立关联
                if author not in dataset.authors:
                    dataset.authors.append(author)
            
            db.session.commit()
            imported_count += 1
            print(f"  成功导入: {dataset.name}")
            
        except Exception as e:
            db.session.rollback()
            error_count += 1
            print(f"  错误: {md_file.name} - {str(e)}")
    
    print(f"\n导入完成:")
    print(f"  成功: {imported_count} 个")
    print(f"  失败: {error_count} 个")

def clear_database():
    """清空数据库"""
    app = create_app('development')
    
    with app.app_context():
        # 删除所有数据
        Dataset.query.delete()
        Author.query.delete()
        Category.query.delete()
        db.session.commit()
        print("数据库已清空")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库初始化工具')
    parser.add_argument('--clear', action='store_true', help='清空数据库')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_database()
    elif args.init:
        init_database()
    else:
        # 默认执行初始化
        init_database()