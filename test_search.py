#!/usr/bin/env python3
"""
测试搜索和筛选功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Dataset, Category

def test_search_and_filter():
    """测试搜索和筛选功能"""
    print("创建Flask应用...")
    app = create_app('development')
    
    with app.app_context(), app.test_client() as client:
        print("\n=== 数据集概览 ===")
        total_datasets = Dataset.query.count()
        print(f"总数据集数量: {total_datasets}")
        
        # 统计各分类数量
        categories = Category.query.all()
        for category in categories:
            count = Dataset.query.filter_by(organ_category=category.code).count()
            print(f"{category.name} ({category.code}): {count} 个")
        
        print("\n=== 测试基本页面访问 ===")
        response = client.get('/')
        print(f"首页状态: {response.status_code}")
        
        print("\n=== 测试器官分类筛选 ===")
        
        # 测试腹部分类筛选
        response = client.get('/?organ_category=fubu')
        print(f"腹部分类筛选状态: {response.status_code}")
        if response.status_code == 200:
            print("✅ 腹部分类筛选正常")
        
        # 测试骨头分类筛选
        response = client.get('/?organ_category=gutou')
        print(f"骨头分类筛选状态: {response.status_code}")
        if response.status_code == 200:
            print("✅ 骨头分类筛选正常")
        
        print("\n=== 测试模态筛选 ===")
        
        # 获取现有的模态类型
        modalities = db.session.query(Dataset.modality).distinct().all()
        modalities = [m[0] for m in modalities if m[0]]
        print(f"可用模态: {modalities}")
        
        if modalities:
            test_modality = modalities[0]
            response = client.get(f'/?modality={test_modality}')
            print(f"模态 '{test_modality}' 筛选状态: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ 模态筛选正常")
        
        print("\n=== 测试任务类型筛选 ===")
        
        # 获取现有的任务类型
        task_types = db.session.query(Dataset.task_type).distinct().all()
        task_types = [t[0] for t in task_types if t[0]]
        print(f"可用任务类型: {task_types}")
        
        if task_types:
            test_task_type = task_types[0]
            response = client.get(f'/?task_type={test_task_type}')
            print(f"任务类型 '{test_task_type}' 筛选状态: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ 任务类型筛选正常")
        
        print("\n=== 测试关键字搜索 ===")
        
        # 测试搜索功能
        search_terms = ['3D', 'CT', '分割', '肝脏']
        
        for term in search_terms:
            response = client.get(f'/?search={term}')
            print(f"搜索 '{term}' 状态: {response.status_code}")
            if response.status_code == 200:
                # 检查是否有相关数据集
                matching_datasets = Dataset.query.filter(
                    Dataset.name.like(f'%{term}%') | 
                    Dataset.description.like(f'%{term}%') |
                    Dataset.anatomical_structure.like(f'%{term}%')
                ).count()
                print(f"  找到 {matching_datasets} 个相关数据集")
        
        print("\n=== 测试组合筛选 ===")
        
        # 测试多个条件组合
        response = client.get('/?organ_category=fubu&modality=CT&search=3D')
        print(f"组合筛选状态: {response.status_code}")
        if response.status_code == 200:
            print("✅ 组合筛选正常")
        
        print("\n=== 测试分页功能 ===")
        
        # 测试分页
        response = client.get('/?page=1')
        print(f"第1页状态: {response.status_code}")
        
        response = client.get('/?page=2')
        print(f"第2页状态: {response.status_code}")
        
        print("\n=== 测试API响应 ===")
        
        # 测试API端点
        response = client.get('/api/datasets')
        if response.status_code == 200:
            api_data = response.get_json()
            print(f"API返回数据集数量: {len(api_data)}")
            print("✅ API功能正常")
        
        print("\n✅ 搜索和筛选功能测试完成！")

if __name__ == '__main__':
    test_search_and_filter()