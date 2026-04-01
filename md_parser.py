import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

def parse_markdown_file(file_path: str) -> Dict[str, Any]:
    """
    解析Markdown文件，提取数据集关键信息
    
    Args:
        file_path: MD文件路径
        
    Returns:
        包含数据集信息的字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 从文件路径和内容推断器官分类
    path_obj = Path(file_path)
    organ_category = infer_organ_category(path_obj, content)
    
    # 提取各种信息
    dataset_info = {
        'name': extract_title(content),
        'organ_category': organ_category,
        'description': extract_description(content),
        'dimension': None,
        'modality': None,
        'task_type': None,
        'anatomical_structure': None,
        'anatomical_region': None,
        'num_classes': None,
        'data_volume': None,
        'file_format': None,
        'official_website': None,
        'download_link': None,
        'baidu_pan_link': None,
        'baidu_pan_password': None,
        'paper_link': None,
        'publication_date': None,
        'visualization_images': json.dumps([]),
        'file_structure': extract_file_structure(content),
        'citation': extract_citation(content),
        'image_stats': json.dumps({}),
        'label_stats': json.dumps({})
    }
    
    # 解析数据集元信息表格
    meta_info = extract_dataset_meta_table(content)
    dataset_info.update(meta_info)
    
    # 如果表格中没有模态信息，则自动推断
    if not dataset_info.get('modality'):
        dataset_info['modality'] = infer_modality(content)
    
    # 提取来源信息
    source_info = extract_source_info(content)
    dataset_info.update(source_info)
    
    # 提取可视化图片
    images = extract_visualization_images(content)
    dataset_info['visualization_images'] = json.dumps(images)
    
    # 提取统计信息
    image_stats = extract_image_stats(content)
    label_stats = extract_label_stats(content)
    dataset_info['image_stats'] = json.dumps(image_stats)
    dataset_info['label_stats'] = json.dumps(label_stats)
    
    return dataset_info

def infer_organ_category(file_path: Path, content: str = "") -> Optional[str]:
    """从文件路径和内容推断器官分类"""
    # 扩展的器官关键词映射
    organ_keywords = {
        # 神经系统
        'nabu': ['脑', '大脑', '脑部', '颅脑', '头部', '头颅', 'brain', 'head'],
        'jisui': ['脊髓', '脊柱', 'spine', 'spinal'],
        
        # 循环系统
        'xinzang': ['心脏', '心脏', '心血管', 'heart', 'cardiac'],
        'xieguan': ['血管', '动脉', '静脉', 'vessel', 'artery', 'vein'],
        
        # 呼吸系统
        'fei': ['肺', '肺部', '肺脏', 'lung', 'pulmonary'],
        'xiongbu': ['胸部', '胸腔', 'chest', 'thorax'],
        
        # 消化系统
        'fubu': ['腹部', '腹腔', 'abdomen', 'abdominal'],
        'gan': ['肝脏', '肝', 'liver'],
        'wei': ['胃', 'stomach'],
        'chang': ['肠', '结肠', '直肠', 'colon', 'rectum'],
        
        # 泌尿生殖系统
        'shen': ['肾脏', '肾', 'kidney'],
        'qianliexian': ['前列腺', 'prostate'],
        'zigong': ['子宫', 'uterus'],
        
        # 骨骼系统
        'gutou': ['骨', '骨头', '骨骼', '关节', 'bone', 'joint'],
        'jizhu': ['脊椎', '椎骨', 'vertebra'],
        
        # 感觉器官
        'yan': ['眼', '眼部', '眼睛', 'eye', 'ocular'],
        'er': ['耳', '耳部', 'ear'],
        
        # 其他
        'ruxian': ['乳腺', '乳房', 'breast'],
        'pifu': ['皮肤', 'skin'],
        
        # 原有分类
        'neikuijing': ['内窥镜', 'endoscopy'],
        'quanshen': ['全身', '全身', 'whole', 'body']
    }
    
    # 首先从文件路径推断
    path_parts = file_path.parts
    for part in path_parts:
        part_lower = part.lower()
        for organ_code, keywords in organ_keywords.items():
            if any(keyword in part_lower for keyword in keywords):
                return organ_code
    
    # 如果路径推断失败，从内容推断
    if content:
        content_lower = content.lower()
        for organ_code, keywords in organ_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return organ_code
    
    return 'quanshen'  # 默认返回全身

def infer_modality(content: str) -> Optional[str]:
    """从内容自动推断数据模态"""
    modality_keywords = {
        'CT': ['ct', 'computed tomography', '计算机断层', 'CT扫描'],
        'MRI': ['mri', 'mr', 'magnetic resonance', '磁共振', 'MRI扫描'],
        'PET': ['pet', 'positron emission', '正电子', 'PET扫描'],
        'PET/CT': ['pet/ct', 'pet-ct', 'petct'],
        'X光': ['x-ray', 'xray', 'x光', 'x射线', '射线', 'x ray'],
        '超声': ['ultrasound', '超声', 'us', 'ultrasonography'],
        '内窥镜': ['endoscopy', '内窥镜', '胃镜', '肠镜', '腹腔镜'],
        '病理学': ['pathology', '病理', '组织学', '细胞学', '组织病理', '细胞病理'],
        '实验室检查': ['laboratory', '实验室', '血液检验', '生化检验'],
        '基因检测': ['genetic', '基因', 'dna', 'rna', '基因检测'],
        '功能检查': ['functional', '功能检查'],
        '心电图': ['ecg', 'ekg', '心电图', 'electrocardiogram'],
        '脑电图': ['eeg', '脑电图', 'electroencephalogram'],
        '电子病历': ['ehr', 'electronic health', '电子病历', '病历'],
        '多模态': ['multimodal', '多模态', '多种']
    }
    
    content_lower = content.lower()
    
    # 计算每种模态的匹配分数
    scores = {}
    for modality, keywords in modality_keywords.items():
        score = sum(content_lower.count(keyword) for keyword in keywords)
        if score > 0:
            scores[modality] = score
    
    # 返回得分最高的模态
    if scores:
        return max(scores, key=scores.get)
    
    return 'CT'  # 默认返回CT（最常见的医学影像）

def extract_title(content: str) -> str:
    """提取标题（数据集名称）"""
    # 匹配第一个 # 标题
    title_match = re.search(r'^#\s+(.+?)(?:\s*数据集介绍)?$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        # 清理标题，移除"数据集介绍"等后缀
        title = re.sub(r'\s*数据集介绍\s*$', '', title)
        return title
    return "未知数据集"

def extract_description(content: str) -> str:
    """提取数据集描述"""
    # 寻找"数据集信息"章节下的内容
    info_pattern = r'##\s*数据集信息\s*\n(.*?)(?=\n##|\n$)'
    info_match = re.search(info_pattern, content, re.DOTALL)
    
    if info_match:
        info_content = info_match.group(1).strip()
        # 提取第一个实质性段落
        paragraphs = info_content.split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and not paragraph.startswith('|') and not paragraph.startswith('```') and len(paragraph) > 20:
                # 清理markdown语法
                paragraph = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', paragraph)  # 移除链接
                paragraph = re.sub(r'\*\*([^*]+)\*\*', r'\1', paragraph)  # 移除加粗
                paragraph = re.sub(r'\*([^*]+)\*', r'\1', paragraph)  # 移除斜体
                return paragraph[:500]  # 限制长度
    
    # 如果没找到"数据集信息"章节，尝试获取第一个段落
    sections = re.split(r'\n#{1,6}\s+', content)
    if len(sections) > 1:
        for section in sections[1:]:  # 跳过标题部分
            paragraphs = section.split('\n\n')
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if paragraph and not paragraph.startswith('|') and not paragraph.startswith('```') and len(paragraph) > 20:
                    # 清理markdown语法
                    paragraph = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', paragraph)  # 移除链接
                    paragraph = re.sub(r'\*\*([^*]+)\*\*', r'\1', paragraph)  # 移除加粗
                    paragraph = re.sub(r'\*([^*]+)\*', r'\1', paragraph)  # 移除斜体
                    return paragraph[:500]  # 限制长度
    return ""

def extract_dataset_meta_table(content: str) -> Dict[str, Any]:
    """提取数据集元信息表格"""
    meta_info = {}
    
    # 寻找包含 "维度", "模态", "任务类型" 等关键字的表格
    # 首先尝试匹配完整格式（包含解剖区域）
    table_pattern_full = r'\|\s*维度\s*\|\s*模态\s*\|\s*任务类型\s*\|\s*解剖结构\s*\|\s*解剖区域\s*\|\s*类别数\s*\|\s*数据量\s*\|\s*文件格式\s*\|\n\|[\s\-|]+\|\n\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
    table_match = re.search(table_pattern_full, content, re.MULTILINE)
    
    if table_match:
        # 提取各个字段（完整格式）
        groups = table_match.groups()
        meta_info.update({
            'dimension': groups[0].strip() if groups[0] and groups[0].strip() else None,
            'modality': groups[1].strip() if groups[1] and groups[1].strip() else None,
            'task_type': groups[2].strip() if groups[2] and groups[2].strip() else None,
            'anatomical_structure': groups[3].strip() if groups[3] and groups[3].strip() else None,
            'anatomical_region': groups[4].strip() if groups[4] and groups[4].strip() else None,
            'num_classes': parse_int(groups[5]) if groups[5] else None,
            'data_volume': groups[6].strip() if groups[6] and groups[6].strip() else None,
            'file_format': groups[7].strip() if groups[7] and groups[7].strip() else None
        })
    else:
        # 尝试匹配简化格式（不包含解剖区域）
        table_pattern_simple = r'\|\s*维度\s*\|\s*模态\s*\|\s*任务类型\s*\|\s*解剖结构\s*\|\s*类别数\s*\|\s*数据量\s*\|\s*文件格式\s*\|\n\|[\s\-|]+\|\n\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        table_match_simple = re.search(table_pattern_simple, content, re.MULTILINE)
        
        if table_match_simple:
            # 提取各个字段（简化格式）
            groups = table_match_simple.groups()
            meta_info.update({
                'dimension': groups[0].strip() if groups[0] and groups[0].strip() else None,
                'modality': groups[1].strip() if groups[1] and groups[1].strip() else None,
                'task_type': groups[2].strip() if groups[2] and groups[2].strip() else None,
                'anatomical_structure': groups[3].strip() if groups[3] and groups[3].strip() else None,
                'anatomical_region': None,  # 简化格式中没有此字段
                'num_classes': parse_int(groups[4]) if groups[4] else None,
                'data_volume': groups[5].strip() if groups[5] and groups[5].strip() else None,
                'file_format': groups[6].strip() if groups[6] and groups[6].strip() else None
            })
    
    return meta_info

def extract_source_info(content: str) -> Dict[str, Any]:
    """提取来源信息"""
    source_info = {}
    
    # 提取官方网站 (支持多种写法)
    website_patterns = [
        r'\|\s*官方网站\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*官方网址\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*网站\s*\|\s*([^|\n]+)\s*\|'
    ]
    for pattern in website_patterns:
        website_match = re.search(pattern, content)
        if website_match:
            url = website_match.group(1).strip()
            # 清理可能的markdown链接格式
            url = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\2', url)
            source_info['official_website'] = url
            break
    
    # 提取下载链接 (支持多种写法)
    download_patterns = [
        r'\|\s*下载链接\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*数据下载\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*相关资源\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*资源链接\s*\|\s*([^|\n]+)\s*\|'
    ]
    for pattern in download_patterns:
        download_match = re.search(pattern, content)
        if download_match:
            url = download_match.group(1).strip()
            # 清理可能的markdown链接格式
            url = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\2', url)
            source_info['download_link'] = url
            break
    
    # 提取百度网盘链接 (支持多种写法)
    baidu_pan_patterns = [
        r'\|\s*百度网盘\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*百度云\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*网盘链接\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*网盘地址\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*BaiduPan\s*\|\s*([^|\n]+)\s*\|'
    ]
    for pattern in baidu_pan_patterns:
        baidu_match = re.search(pattern, content)
        if baidu_match:
            url = baidu_match.group(1).strip()
            # 清理可能的markdown链接格式
            url = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\2', url)
            source_info['baidu_pan_link'] = url
            break
    
    # 提取百度网盘提取码 (支持多种写法)
    password_patterns = [
        r'\|\s*提取码\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*密码\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*提取密码\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*访问密码\s*\|\s*([^|\n]+)\s*\|',
        r'提取码[:：]\s*([a-zA-Z0-9]{4})',
        r'密码[:：]\s*([a-zA-Z0-9]{4})'
    ]
    for pattern in password_patterns:
        password_match = re.search(pattern, content)
        if password_match:
            password = password_match.group(1).strip()
            source_info['baidu_pan_password'] = password
            break
    
    # 提取论文链接 (支持多种写法)
    paper_patterns = [
        r'\|\s*文章地址\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*论文链接\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*相关论文\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*知乎文章\s*\|\s*([^|\n]+)\s*\|',
        r'\|\s*参考文献\s*\|\s*([^|\n]+)\s*\|'
    ]
    for pattern in paper_patterns:
        paper_match = re.search(pattern, content)
        if paper_match:
            url = paper_match.group(1).strip()
            # 清理可能的markdown链接格式
            url = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\2', url)
            source_info['paper_link'] = url
            break
    
    # 提取发布日期 (支持多种写法)
    date_patterns = [
        r'数据公开日期[^|]*\|\s*([^|\n]+)',
        r'公开日期[^|]*\|\s*([^|\n]+)',
        r'发布日期[^|]*\|\s*([^|\n]+)',
        r'发布时间[^|]*\|\s*([^|\n]+)'
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, content)
        if date_match:
            source_info['publication_date'] = date_match.group(1).strip()
            break
    
    return source_info

def extract_visualization_images(content: str) -> List[str]:
    """提取可视化图片链接"""
    images = []
    
    # 匹配markdown图片语法
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    img_matches = re.findall(img_pattern, content)
    
    for alt_text, img_url in img_matches:
        if img_url.startswith('http'):
            images.append({
                'alt': alt_text,
                'url': img_url
            })
    
    return images

def extract_file_structure(content: str) -> str:
    """提取文件结构信息"""
    # 寻找文件结构部分
    file_structure_pattern = r'##\s*文件结构.*?\n```(?:text)?\n(.*?)\n```'
    file_structure_match = re.search(file_structure_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if file_structure_match:
        return file_structure_match.group(1).strip()
    
    # 备用方案：寻找代码块中的文件结构
    code_blocks = re.findall(r'```(?:text)?\n(.*?)\n```', content, re.DOTALL)
    
    for block in code_blocks:
        # 如果包含文件/目录结构的特征，但不是引用信息
        if any(indicator in block for indicator in ['├──', '└──', '│', '.zip', '.txt', '.md', '/']) and not block.strip().startswith('@'):
            return block.strip()
    
    return ""

def extract_citation(content: str) -> str:
    """提取引用信息"""
    # 尝试多种引用格式和章节名称
    citation_patterns = [
        # BibTeX代码块格式
        r'##\s*引用.*?\n```(?:text|bibtex)?\n(.*?)\n```',
        r'##\s*引用格式.*?\n```(?:text|bibtex)?\n(.*?)\n```',
        r'##\s*Citation.*?\n```(?:text|bibtex)?\n(.*?)\n```',
        # 参考/引用章节格式（从章节开始到下一个章节或文件末尾）
        r'##\s*参考\s*\n(.*?)(?=\n##|$)',
        r'##\s*引用\s*\n(.*?)(?=\n##|$)',
        r'##\s*参考文献\s*\n(.*?)(?=\n##|$)',
        r'##\s*References?\s*\n(.*?)(?=\n##|$)'
    ]
    
    for pattern in citation_patterns:
        citation_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if citation_match:
            citation_text = citation_match.group(1).strip()
            if citation_text:
                # 如果是BibTeX格式，直接返回
                if citation_text.startswith('@'):
                    return citation_text
                # 如果是列表格式，清理空行并格式化
                lines = [line.strip() for line in citation_text.split('\n') if line.strip()]
                if lines:
                    return '\n'.join(lines)
    
    return ""

def extract_image_stats(content: str) -> Dict[str, Any]:
    """提取图像尺寸统计信息 - 支持多种格式"""
    stats = {}
    
    # 查找图像尺寸统计段落（支持 ## 和 ### 标题）
    stats_section_pattern = r'(###?)\s*图像尺寸统计.*?\n(.*?)(?=\n###?|\Z)'
    stats_section_match = re.search(stats_section_pattern, content, re.MULTILINE | re.DOTALL)
    
    if not stats_section_match:
        return stats
    
    section_content = stats_section_match.group(2).strip()
    lines = section_content.split('\n')
    
    # 解析表格内容
    table_started = False
    for line in lines:
        line = line.strip()
        
        # 跳过空行和非表格行
        if not line or not line.startswith('|'):
            continue
            
        # 解析表格行
        cells = [cell.strip() for cell in line.split('|')]
        cells = [cell for cell in cells if cell]  # 移除空单元格
        
        if len(cells) < 2:
            continue
            
        # 跳过表头和分隔行
        first_cell = cells[0].lower()
        if ('spacing' in first_cell or 'size' in first_cell or 
            '---' in first_cell or '数据集统计' in first_cell or first_cell == ''):
            continue
        
        # 解析统计行
        stat_type = first_cell
        
        # 确定是哪种格式的表格
        if len(cells) == 3:
            # 三列格式：| 统计类型 | spacing | size |
            spacing_value = cells[1].strip()
            size_value = cells[2].strip()
        elif len(cells) == 2:
            # 两列格式：| 统计类型 | size | （Cholec80格式）
            spacing_value = None
            size_value = cells[1].strip()
        else:
            continue
        
        # 匹配统计类型
        if ('最小' in stat_type or 'min' in stat_type or '各维度最小值' in stat_type):
            stats['min'] = {'size': size_value, 'spacing': spacing_value}
        elif ('中值' in stat_type or '中位' in stat_type or 'median' in stat_type or '各维度中值' in stat_type):
            stats['median'] = {'size': size_value, 'spacing': spacing_value}
        elif ('最大' in stat_type or 'max' in stat_type or '各维度最大值' in stat_type):
            stats['max'] = {'size': size_value, 'spacing': spacing_value}
    
    return stats

def extract_label_stats(content: str) -> Dict[str, Any]:
    """提取标签统计信息"""
    stats = {}
    
    # 寻找标签统计相关信息
    # 可以扩展以解析更复杂的标签统计表格
    
    return stats

def parse_int(value: str) -> Optional[int]:
    """安全地解析整数"""
    if not value or value.strip() == '':
        return None
    try:
        # 移除非数字字符，只保留数字
        number_str = re.sub(r'[^\d]', '', value)
        if number_str:
            return int(number_str)
    except (ValueError, TypeError):
        pass
    return None

def extract_authors_from_content(content: str) -> List[Dict[str, str]]:
    """提取作者信息"""
    authors = []
    
    # 寻找作者及机构部分
    author_pattern = r'##\s*作者及机构.*?\n(.*?)(?=\n##|\n$)'
    author_match = re.search(author_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if author_match:
        author_section = author_match.group(1)
        # 匹配 "- 姓名 (机构)" 格式
        author_lines = re.findall(r'-\s*([^(]+)(?:\s*\(([^)]+)\))?', author_section)
        
        for name, institution in author_lines:
            authors.append({
                'name': name.strip(),
                'institution': institution.strip() if institution else ''
            })
    
    return authors

# 使用示例和测试函数
if __name__ == "__main__":
    # 测试多个文件
    test_files = [
        "/Users/chenziqiang/Desktop/数据集md样例/fubu/3D-IRCADB.md",
        "/Users/chenziqiang/Desktop/数据集md样例/neikuijing/AIDA-E2.md",
        "/Users/chenziqiang/Desktop/数据集md样例/quanshen/AutoPET.md"
    ]
    
    for test_file in test_files:
        print(f"\n{'='*50}")
        print(f"解析文件: {test_file}")
        print('='*50)
        
        try:
            result = parse_markdown_file(test_file)
            print("解析结果:")
            for key, value in result.items():
                if value:  # 只显示有值的字段
                    print(f"{key}: {value}")
        except Exception as e:
            print(f"解析失败: {e}")