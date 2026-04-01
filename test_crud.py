#!/usr/bin/env python3
"""
测试CRUD操作的完整性
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Dataset

def test_crud():
    """测试完整的CRUD操作"""
    print("创建Flask应用...")
    app = create_app('development')
    
    with app.app_context(), app.test_client() as client:
        print("\n=== 测试创建 (Create) ===")
        
        # 获取初始数据集数量
        initial_count = Dataset.query.count()
        print(f"初始数据集数量: {initial_count}")
        
        # 测试新建数据集页面
        response = client.get('/dataset/new')
        print(f"新建页面状态: {response.status_code}")
        
        # 提交新数据集
        new_dataset_data = {
            'name': 'CRUD测试数据集',
            'organ_category': 'fubu',
            'dimension': '3D',
            'modality': 'CT',
            'task_type': '分割',
            'anatomical_structure': '肝脏',
            'anatomical_region': '腹部',
            'num_classes': '3',
            'data_volume': '100',
            'file_format': 'DICOM',
            'publication_date': '2024',
            'description': '这是一个用于测试CRUD操作的数据集',
            'official_website': 'https://test.example.com',
            'download_link': 'https://test.example.com/download',
            'paper_link': 'https://test.example.com/paper'
        }
        
        response = client.post('/dataset/new', data=new_dataset_data)
        print(f"创建数据集响应状态: {response.status_code}")
        
        # 验证创建成功
        new_count = Dataset.query.count()
        print(f"创建后数据集数量: {new_count}")
        
        if new_count > initial_count:
            test_dataset = Dataset.query.filter_by(name='CRUD测试数据集').first()
            if test_dataset:
                dataset_id = test_dataset.id
                print(f"✅ 创建成功，ID: {dataset_id}")
                
                print("\n=== 测试读取 (Read) ===")
                
                # 测试详情页
                response = client.get(f'/dataset/{dataset_id}')
                print(f"详情页状态: {response.status_code}")
                
                # 测试API
                response = client.get('/api/datasets')
                if response.status_code == 200:
                    datasets = response.get_json()
                    found = any(d['id'] == dataset_id for d in datasets)
                    print(f"✅ API读取成功: {found}")
                
                print("\n=== 测试更新 (Update) ===")
                
                # 测试编辑页面
                response = client.get(f'/dataset/{dataset_id}/edit')
                print(f"编辑页面状态: {response.status_code}")
                
                # 更新数据集
                update_data = new_dataset_data.copy()
                update_data['name'] = 'CRUD测试数据集-已更新'
                update_data['description'] = '这是更新后的描述'
                
                response = client.post(f'/dataset/{dataset_id}/edit', data=update_data)
                print(f"更新响应状态: {response.status_code}")
                
                # 验证更新
                updated_dataset = Dataset.query.get(dataset_id)
                if updated_dataset and updated_dataset.name == 'CRUD测试数据集-已更新':
                    print("✅ 更新成功")
                else:
                    print("❌ 更新失败")
                
                print("\n=== 测试删除 (Delete) ===")
                
                # 删除数据集
                response = client.post(f'/dataset/{dataset_id}/delete')
                print(f"删除响应状态: {response.status_code}")
                
                # 验证删除
                deleted_dataset = Dataset.query.get(dataset_id)
                if deleted_dataset is None:
                    print("✅ 删除成功")
                    final_count = Dataset.query.count()
                    print(f"删除后数据集数量: {final_count}")
                else:
                    print("❌ 删除失败")
                
                print("\n✅ CRUD操作测试完成！")
            else:
                print("❌ 未找到创建的数据集")
        else:
            print("❌ 数据集创建失败")

if __name__ == '__main__':
    test_crud()