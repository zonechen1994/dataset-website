#!/usr/bin/env python3
"""
添加8个额外的数据集记录以达到18个数据集总数
"""

import os
import sys
import json
from datetime import datetime, date

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, Dataset

def add_additional_datasets():
    """添加8个额外的医疗数据集"""
    
    # 8个额外的医疗数据集信息
    additional_datasets = [
        {
            "name": "BRATS2021 脑肿瘤分割挑战数据集",
            "description": "Brain Tumor Segmentation Challenge 2021，包含多模态MRI脑肿瘤图像及分割标注",
            "organ_category": "nabu",
            "dimension": "3D",
            "modality": "MRI",
            "task_type": "segmentation",
            "anatomical_structure": "脑肿瘤",
            "anatomical_region": "头部",
            "num_classes": 4,
            "data_volume": "2000+例患者",
            "file_format": "NIfTI",
            "official_website": "https://www.synapse.org/#!Synapse:syn25829067",
            "download_link": "https://www.synapse.org/#!Synapse:syn25829067",
            "paper_link": "https://arxiv.org/abs/2107.02314",
            "publication_date": date(2021, 6, 1),
            "citation": "@article{baid2021rsna,\n  title={The RSNA-ASNR-MICCAI BraTS 2021 Benchmark on Brain Tumor Segmentation and Radiogenomic Classification},\n  author={Baid, Ujjwal and Ghodasara, Satyam and others},\n  journal={arXiv preprint arXiv:2107.02314},\n  year={2021}\n}",
            "file_structure": "BraTS2021/\n├── TrainingData/\n│   ├── BraTS2021_00001/\n│   │   ├── BraTS2021_00001_t1.nii.gz\n│   │   ├── BraTS2021_00001_t1ce.nii.gz\n│   │   ├── BraTS2021_00001_t2.nii.gz\n│   │   ├── BraTS2021_00001_flair.nii.gz\n│   │   └── BraTS2021_00001_seg.nii.gz\n│   └── ...\n└── ValidationData/"
        },
        {
            "name": "LUNA16 肺结节检测数据集",
            "description": "Lung Nodule Analysis 2016，用于肺结节检测和分类的大规模CT数据集",
            "organ_category": "xiongbu",
            "dimension": "3D",
            "modality": "CT",
            "task_type": "detection",
            "anatomical_structure": "肺结节",
            "anatomical_region": "胸部",
            "num_classes": 2,
            "data_volume": "888个CT扫描",
            "file_format": "mhd/raw",
            "official_website": "https://luna16.grand-challenge.org/",
            "download_link": "https://luna16.grand-challenge.org/Download/",
            "paper_link": "https://arxiv.org/abs/1612.08012",
            "publication_date": date(2016, 12, 1),
            "citation": "@article{setio2017validation,\n  title={Validation, comparison, and combination of algorithms for automatic detection of pulmonary nodules in computed tomography images},\n  author={Setio, Arnaud AA and others},\n  journal={Medical image analysis},\n  volume={42},\n  pages={1--13},\n  year={2017}\n}",
        },
        {
            "name": "ISIC2020 皮肤病变分类数据集",
            "description": "国际皮肤影像协作组织2020年皮肤病变分析挑战，包含黑色素瘤检测任务",
            "organ_category": "pifu",
            "dimension": "2D",
            "modality": "皮肤镜",
            "task_type": "classification",
            "anatomical_structure": "皮肤病变",
            "anatomical_region": "全身皮肤",
            "num_classes": 2,
            "data_volume": "33,126张图像",
            "file_format": "JPEG",
            "official_website": "https://challenge2020.isic-archive.com/",
            "download_link": "https://challenge2020.isic-archive.com/",
            "paper_link": "https://arxiv.org/abs/2010.05351",
            "publication_date": date(2020, 8, 1),
        },
        {
            "name": "DRIVE 视网膜血管分割数据集",
            "description": "Digital Retinal Images for Vessel Extraction，经典的视网膜血管分割基准数据集",
            "organ_category": "yanjing",
            "dimension": "2D",
            "modality": "眼底照相",
            "task_type": "segmentation",
            "anatomical_structure": "视网膜血管",
            "anatomical_region": "眼部",
            "num_classes": 2,
            "data_volume": "40张图像",
            "file_format": "TIF",
            "official_website": "https://drive.grand-challenge.org/",
            "download_link": "https://drive.grand-challenge.org/",
            "paper_link": "https://ieeexplore.ieee.org/document/1282003",
            "publication_date": date(2004, 10, 1),
        },
        {
            "name": "COVID-19 CT分割数据集",
            "description": "COVID-19肺部CT图像分割数据集，包含感染区域和肺部分割标注",
            "organ_category": "xiongbu",
            "dimension": "3D",
            "modality": "CT",
            "task_type": "segmentation",
            "anatomical_structure": "肺部感染",
            "anatomical_region": "胸部",
            "num_classes": 3,
            "data_volume": "829个CT扫描",
            "file_format": "NIfTI",
            "official_website": "http://medicalsegmentation.com/covid19/",
            "download_link": "http://medicalsegmentation.com/covid19/",
            "paper_link": "https://www.nature.com/articles/s41597-020-00741-6",
            "publication_date": date(2020, 11, 1),
        },
        {
            "name": "OASIS 大脑MRI纵向研究数据集",
            "description": "Open Access Series of Imaging Studies，包含正常衰老和阿尔兹海默病的纵向MRI研究",
            "organ_category": "nabu",
            "dimension": "3D",
            "modality": "MRI",
            "task_type": "classification",
            "anatomical_structure": "大脑",
            "anatomical_region": "头部",
            "num_classes": 3,
            "data_volume": "416个受试者",
            "file_format": "ANALYZE",
            "official_website": "https://www.oasis-brains.org/",
            "download_link": "https://www.oasis-brains.org/",
            "paper_link": "https://www.jneurosci.org/content/27/11/2896",
            "publication_date": date(2007, 3, 1),
        },
        {
            "name": "LIDC-IDRI 肺部影像数据库",
            "description": "Lung Image Database Consortium image collection，大规模肺癌筛查CT数据集",
            "organ_category": "xiongbu",
            "dimension": "3D",
            "modality": "CT",
            "task_type": "classification",
            "anatomical_structure": "肺结节",
            "anatomical_region": "胸部",
            "num_classes": 5,
            "data_volume": "1018个CT扫描",
            "file_format": "DICOM",
            "official_website": "https://wiki.cancerimagingarchive.net/display/Public/LIDC-IDRI",
            "download_link": "https://wiki.cancerimagingarchive.net/display/Public/LIDC-IDRI",
            "paper_link": "https://aapm.onlinelibrary.wiley.com/doi/abs/10.1118/1.3528204",
            "publication_date": date(2011, 2, 1),
        },
        {
            "name": "NIH 胸部X光数据集",
            "description": "NIH Clinical Center提供的大规模胸部X光图像数据集，包含14种疾病标签",
            "organ_category": "xiongbu",
            "dimension": "2D",
            "modality": "X-Ray",
            "task_type": "classification",
            "anatomical_structure": "胸部器官",
            "anatomical_region": "胸部",
            "num_classes": 14,
            "data_volume": "112,120张图像",
            "file_format": "PNG",
            "official_website": "https://www.nih.gov/news-events/news-releases/nih-clinical-center-provides-one-largest-publicly-available-chest-x-ray-datasets-scientific-community",
            "download_link": "https://nihcc.app.box.com/v/ChestXray-NIHCC",
            "paper_link": "https://openaccess.thecvf.com/content_cvpr_2017/papers/Wang_ChestX-Ray8_Hospital-Scale_Chest_CVPR_2017_paper.pdf",
            "publication_date": date(2017, 7, 1),
        }
    ]
    
    app = create_app('development')
    
    with app.app_context():
        added_count = 0
        
        for dataset_info in additional_datasets:
            # 检查是否已存在同名数据集
            existing = Dataset.query.filter_by(name=dataset_info['name']).first()
            if existing:
                print(f"数据集 '{dataset_info['name']}' 已存在，跳过")
                continue
            
            try:
                # 创建新数据集
                dataset = Dataset()
                
                # 设置所有字段
                for field, value in dataset_info.items():
                    if hasattr(dataset, field):
                        setattr(dataset, field, value)
                
                db.session.add(dataset)
                db.session.commit()
                
                added_count += 1
                print(f"✓ 成功添加数据集: {dataset.name} (ID: {dataset.id})")
                
            except Exception as e:
                db.session.rollback()
                print(f"✗ 添加失败 '{dataset_info['name']}': {str(e)}")
        
        print(f"\n=== 添加完成 ===")
        print(f"新增数据集: {added_count} 个")
        
        # 显示当前数据集总数
        total_count = Dataset.query.count()
        print(f"数据库中现有数据集总数: {total_count}")
        
        if total_count >= 18:
            print("🎉 已成功达到18个数据集的目标！")
        else:
            print(f"还需要添加 {18 - total_count} 个数据集")

if __name__ == '__main__':
    add_additional_datasets()