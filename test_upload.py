#!/usr/bin/env python3
"""
测试MD文件上传和解析功能
"""

import sys
import os
import tempfile
import shutil

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Dataset

def test_upload():
    """测试文件上传功能"""
    print("创建Flask应用...")
    app = create_app('development')
    
    # 获取现有数据集数量
    with app.app_context():
        initial_count = Dataset.query.count()
        print(f"初始数据集数量: {initial_count}")
    
    print("\n测试文件上传...")
    with app.test_client() as client:
        # 测试上传页面
        response = client.get('/upload')
        print(f"上传页面状态: {response.status_code}")
        
        # 创建一个测试MD文件
        test_md_content = """# 测试数据集介绍

## 数据集信息

这是一个测试数据集，用于验证上传和解析功能。

### 数据集元信息

| 维度 | 模态 | 任务类型 | 解剖结构 | 解剖区域 | 类别数 | 数据量 | 文件格式 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2D | X光 | 分类 | 骨骼 | 手部 | 5 | 100 | jpg |

## 来源信息

| 官方网站 | https://test.example.com |
| --- | --- |
| 下载链接 | https://test.example.com/download |
| 文章地址 | https://test.example.com/paper |
| 数据公开日期 | 2024 |

## 作者及机构

- 张三 (测试大学)
- 李四 (测试研究所)

## 引用

```text
@article{test2024,
  title={Test Dataset},
  author={Zhang, San and Li, Si},
  year={2024}
}
```
"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_md_content)
            temp_file = f.name
        
        try:
            # 模拟文件上传
            with open(temp_file, 'rb') as f:
                response = client.post('/upload', 
                                     data={'file': (f, 'test_dataset.md')},
                                     content_type='multipart/form-data')
            
            print(f"上传响应状态: {response.status_code}")
            
            # 检查是否成功创建了新数据集
            with app.app_context():
                final_count = Dataset.query.count()
                print(f"上传后数据集数量: {final_count}")
                
                if final_count > initial_count:
                    # 获取最新的数据集
                    latest_dataset = Dataset.query.order_by(Dataset.created_at.desc()).first()
                    print(f"新创建的数据集: {latest_dataset.name}")
                    print(f"  - 维度: {latest_dataset.dimension}")
                    print(f"  - 模态: {latest_dataset.modality}")
                    print(f"  - 任务类型: {latest_dataset.task_type}")
                    print(f"  - 作者数量: {len(latest_dataset.authors)}")
                    
                    print("\n✅ MD文件上传和解析功能正常！")
                else:
                    print("\n❌ 文件上传失败，没有创建新数据集")
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == '__main__':
    test_upload()