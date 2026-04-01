#!/usr/bin/env python3
"""
恢复完整的器官分类、模态类型和任务类型
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_enhanced import create_app
from models import db, Category, Modality, TaskType

def restore_full_classifications():
    """恢复完整的医疗数据集分类系统"""
    
    # 完整的器官分类
    categories_data = [
        {'code': 'nabu', 'name': '脑部', 'description': '脑部、头部相关器官'},
        {'code': 'yanjing', 'name': '眼部', 'description': '眼部、视网膜等'},
        {'code': 'xiongbu', 'name': '胸部', 'description': '肺部、心脏、胸腔等'},
        {'code': 'fubu', 'name': '腹部', 'description': '肝脏、胃、肠道等腹部器官'},
        {'code': 'pifu', 'name': '皮肤', 'description': '皮肤病变、皮肤镜等'},
        {'code': 'gutou', 'name': '骨头', 'description': '骨骼、关节等'},
        {'code': 'qianliexian', 'name': '前列腺', 'description': '前列腺相关'},
        {'code': 'ruxian', 'name': '乳腺', 'description': '乳腺相关'},
        {'code': 'shenzang', 'name': '肾脏', 'description': '肾脏相关'},
        {'code': 'zigong', 'name': '子宫', 'description': '子宫、妇科相关'},
        {'code': 'neikuijing', 'name': '内窥镜', 'description': '内窥镜检查相关'},
        {'code': 'quanshen', 'name': '全身', 'description': '全身、多器官或整体数据集'},
        {'code': 'other', 'name': '其他', 'description': '其他未分类器官'},
    ]
    
    # 完整的模态类型
    modalities_data = [
        {'code': 'ct', 'name': 'CT', 'category': '影像', 'description': '计算机断层扫描'},
        {'code': 'mri', 'name': 'MRI', 'category': '影像', 'description': '磁共振成像'},
        {'code': 'xray', 'name': 'X光', 'category': '影像', 'description': 'X射线成像'},
        {'code': 'ultrasound', 'name': '超声', 'category': '影像', 'description': '超声成像'},
        {'code': 'pet', 'name': 'PET', 'category': '影像', 'description': '正电子发射断层扫描'},
        {'code': 'petct', 'name': 'PET/CT', 'category': '影像', 'description': 'PET和CT融合成像'},
        {'code': 'spect', 'name': 'SPECT', 'category': '影像', 'description': '单光子发射计算机断层成像'},
        {'code': 'endoscopy', 'name': '内窥镜', 'category': '内窥镜', 'description': '内窥镜成像'},
        {'code': 'microscopy', 'name': '显微镜', 'category': '病理', 'description': '显微镜成像'},
        {'code': 'dermoscopy', 'name': '皮肤镜', 'category': '皮肤', 'description': '皮肤镜检查'},
        {'code': 'fundus', 'name': '眼底照相', 'category': '眼科', 'description': '眼底摄影'},
        {'code': 'oct', 'name': 'OCT', 'category': '眼科', 'description': '光学相干断层扫描'},
        {'code': 'mammography', 'name': '乳腺X光', 'category': '影像', 'description': '乳腺X光摄影'},
        {'code': 'video', 'name': '视频', 'category': '视频', 'description': '视频数据'},
        {'code': 'mesh', 'name': '网格模型', 'category': '三维', 'description': '三维网格模型'},
        {'code': 'pointcloud', 'name': '点云', 'category': '三维', 'description': '三维点云数据'},
        {'code': 'multimodal', 'name': '多模态', 'category': '综合', 'description': '多种模态融合'},
        {'code': 'other', 'name': '其他', 'category': '其他', 'description': '其他模态类型'},
    ]
    
    # 完整的任务类型
    task_types_data = [
        {'code': 'segmentation', 'name': '分割', 'description': '图像分割任务'},
        {'code': 'classification', 'name': '分类', 'description': '图像分类任务'},
        {'code': 'detection', 'name': '检测', 'description': '目标检测任务'},
        {'code': 'registration', 'name': '配准', 'description': '图像配准任务'},
        {'code': 'reconstruction', 'name': '重建', 'description': '三维重建任务'},
        {'code': 'phase_recognition', 'name': '阶段识别', 'description': '手术阶段识别'},
        {'code': 'prognosis', 'name': '预后预测', 'description': '疾病预后预测'},
        {'code': 'diagnosis', 'name': '诊断', 'description': '疾病诊断'},
        {'code': 'screening', 'name': '筛查', 'description': '疾病筛查'},
        {'code': 'tracking', 'name': '追踪', 'description': '目标追踪'},
        {'code': 'synthesis', 'name': '合成', 'description': '图像合成'},
        {'code': 'enhancement', 'name': '增强', 'description': '图像增强'},
        {'code': 'denoising', 'name': '去噪', 'description': '图像去噪'},
        {'code': 'super_resolution', 'name': '超分辨率', 'description': '图像超分辨率'},
        {'code': 'annotation', 'name': '标注', 'description': '数据标注'},
        {'code': 'other', 'name': '其他', 'description': '其他任务类型'},
    ]
    
    app = create_app('development')
    
    with app.app_context():
        added_categories = 0
        added_modalities = 0
        added_task_types = 0
        
        # 添加器官分类
        print("=== 添加器官分类 ===")
        for cat_data in categories_data:
            existing = Category.query.filter_by(code=cat_data['code']).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
                added_categories += 1
                print(f"✓ 添加器官分类: {cat_data['name']} ({cat_data['code']})")
            else:
                print(f"- 器官分类已存在: {cat_data['name']}")
        
        # 添加模态类型
        print(f"\n=== 添加模态类型 ===")
        for mod_data in modalities_data:
            existing = Modality.query.filter_by(code=mod_data['code']).first()
            if not existing:
                modality = Modality(**mod_data)
                db.session.add(modality)
                added_modalities += 1
                print(f"✓ 添加模态类型: {mod_data['name']} ({mod_data['code']})")
            else:
                print(f"- 模态类型已存在: {mod_data['name']}")
        
        # 添加任务类型
        print(f"\n=== 添加任务类型 ===")
        for task_data in task_types_data:
            existing = TaskType.query.filter_by(code=task_data['code']).first()
            if not existing:
                task_type = TaskType(**task_data)
                db.session.add(task_type)
                added_task_types += 1
                print(f"✓ 添加任务类型: {task_data['name']} ({task_data['code']})")
            else:
                print(f"- 任务类型已存在: {task_data['name']}")
        
        try:
            db.session.commit()
            print(f"\n=== 恢复完成 ===")
            print(f"新增器官分类: {added_categories} 个")
            print(f"新增模态类型: {added_modalities} 个") 
            print(f"新增任务类型: {added_task_types} 个")
            
            # 显示最终统计
            total_categories = Category.query.count()
            total_modalities = Modality.query.count()
            total_task_types = TaskType.query.count()
            
            print(f"\n=== 最终统计 ===")
            print(f"器官分类总数: {total_categories} 个")
            print(f"模态类型总数: {total_modalities} 个")
            print(f"任务类型总数: {total_task_types} 个")
            
        except Exception as e:
            db.session.rollback()
            print(f"恢复失败: {str(e)}")

if __name__ == '__main__':
    restore_full_classifications()