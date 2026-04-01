#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
初始化样例数据
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app_enhanced import create_app
from models import db, Category, Modality, TaskType
from md_parser import parse_markdown_file, extract_authors_from_content
from models import Dataset, Author

def init_basic_data():
    """初始化基础分类数据"""
    
    # 器官分类
    categories = [
        {'code': 'fubu', 'name': '腹部', 'description': '腹部器官相关数据集'},
        {'code': 'gutou', 'name': '骨头', 'description': '骨骼系统相关数据集'},
        {'code': 'neikuijing', 'name': '内窥镜', 'description': '内窥镜检查相关数据集'},
        {'code': 'quanshen', 'name': '全身', 'description': '全身或多器官系统数据集'}
    ]
    
    for cat_data in categories:
        existing = Category.query.filter_by(code=cat_data['code']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    
    # 模态类型
    modalities = [
        {'code': 'ct', 'name': 'CT', 'description': '计算机断层扫描', 'category': '医学影像'},
        {'code': 'mri', 'name': 'MRI', 'description': '磁共振成像', 'category': '医学影像'},
        {'code': 'xray', 'name': 'X光', 'description': 'X射线影像', 'category': '医学影像'},
        {'code': 'ultrasound', 'name': '超声', 'description': '超声波影像', 'category': '医学影像'},
        {'code': 'endoscopy', 'name': '内窥镜', 'description': '内窥镜影像', 'category': '医学影像'},
        {'code': 'video', 'name': '视频', 'description': '视频数据', 'category': '多媒体'},
        {'code': 'mesh', 'name': '网格模型', 'description': '三维网格数据', 'category': '几何数据'}
    ]
    
    for mod_data in modalities:
        existing = Modality.query.filter_by(code=mod_data['code']).first()
        if not existing:
            modality = Modality(**mod_data)
            db.session.add(modality)
    
    # 任务类型
    task_types = [
        {'code': 'segmentation', 'name': '分割', 'description': '图像分割任务'},
        {'code': 'classification', 'name': '分类', 'description': '图像分类任务'},
        {'code': 'detection', 'name': '检测', 'description': '目标检测任务'},
        {'code': 'phase_recognition', 'name': '阶段识别', 'description': '手术阶段识别'},
        {'code': 'registration', 'name': '配准', 'description': '图像配准任务'},
        {'code': 'reconstruction', 'name': '重建', 'description': '三维重建任务'}
    ]
    
    for task_data in task_types:
        existing = TaskType.query.filter_by(code=task_data['code']).first()
        if not existing:
            task_type = TaskType(**task_data)
            db.session.add(task_type)
    
    db.session.commit()
    print("✅ 基础数据初始化完成")

def import_md_files():
    """导入MD文件"""
    
    # MD文件路径映射
    md_files = [
        # 内窥镜类别
        ('../neikuijing/Cholec80.md', 'neikuijing'),
        ('../neikuijing/AIDA-E2.md', 'neikuijing'),
        ('../neikuijing/C3VD.md', 'neikuijing'),
        
        # 腹部类别
        ('../fubu/3D-IRCADB.md', 'fubu'),
        ('../fubu/PROMISE12.md', 'fubu'),
        
        # 骨头类别
        ('../gutou/X光手部小关节分类_数据集介绍.md', 'gutou'),
        ('../gutou/腰骶脊柱MRI_数据集介绍.md', 'gutou'),
        
        # 全身类别
        ('../quanshen/AutoPET.md', 'quanshen'),
        ('../quanshen/ULS.md', 'quanshen'),
        ('../quanshen/三维下肢肌肉骨骼几何结构.md', 'quanshen'),
    ]
    
    success_count = 0
    error_count = 0
    
    for md_file_path, category_code in md_files:
        full_path = project_root / md_file_path
        
        if not full_path.exists():
            print(f"⚠️  文件不存在: {full_path}")
            error_count += 1
            continue
            
        try:
            # 解析MD文件
            dataset_data = parse_markdown_file(str(full_path))
            
            # 设置器官分类
            dataset_data['organ_category'] = category_code
            
            # 读取文件内容以提取作者信息
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建数据集
            dataset = Dataset()
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
            success_count += 1
            print(f"✅ 导入成功: {dataset.name}")
            
        except Exception as e:
            db.session.rollback()
            error_count += 1
            print(f"❌ 导入失败: {full_path} - {str(e)}")
    
    print(f"\n📊 导入完成: 成功 {success_count} 个，失败 {error_count} 个")

def main():
    """主函数"""
    app = create_app('development')
    
    with app.app_context():
        print("🚀 开始初始化样例数据...")
        
        # 初始化基础数据
        init_basic_data()
        
        # 导入MD文件
        import_md_files()
        
        print("🎉 样例数据初始化完成！")

if __name__ == '__main__':
    main()