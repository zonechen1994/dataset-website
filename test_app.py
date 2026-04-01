#!/usr/bin/env python3
"""
测试Flask应用是否能正常启动和运行
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Dataset, Category

def test_app():
    """测试应用功能"""
    print("创建Flask应用...")
    app = create_app('development')
    
    print("测试应用上下文...")
    with app.app_context():
        # 测试数据库连接
        print(f"数据集总数: {Dataset.query.count()}")
        print(f"分类总数: {Category.query.count()}")
        
        # 测试获取前几个数据集
        datasets = Dataset.query.limit(3).all()
        print(f"\n前3个数据集:")
        for dataset in datasets:
            print(f"  - {dataset.name} ({dataset.organ_category})")
    
    print("\n测试客户端请求...")
    with app.test_client() as client:
        # 测试首页
        response = client.get('/')
        print(f"首页状态: {response.status_code}")
        
        # 测试API
        response = client.get('/api/datasets')
        print(f"API状态: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"API返回数据集数量: {len(data)}")
        
        # 测试数据集详情页
        if Dataset.query.first():
            first_dataset = Dataset.query.first()
            response = client.get(f'/dataset/{first_dataset.id}')
            print(f"数据集详情页状态: {response.status_code}")
    
    print("\n✅ Flask应用测试完成，功能正常！")

if __name__ == '__main__':
    test_app()