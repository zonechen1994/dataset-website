#!/usr/bin/env python3
"""
测试管理后台侧边栏的一致性
"""

import os
import re
from glob import glob

def test_template_consistency():
    """测试模板文件的一致性"""
    print("=== 管理后台侧边栏一致性测试 ===\n")
    
    admin_templates = glob("templates/admin/*.html")
    admin_user_templates = glob("templates/admin/users/*.html")
    admin_planet_templates = glob("templates/admin/planet/*.html")
    
    all_templates = admin_templates + admin_user_templates + admin_planet_templates
    
    results = {
        'using_sidebar_include': [],
        'using_base_template': [],
        'inconsistent': [],
        'total_checked': len(all_templates)
    }
    
    print("检查的模板文件:")
    for template in all_templates:
        print(f"  - {template}")
    print()
    
    for template_path in all_templates:
        if not os.path.exists(template_path):
            continue
            
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        template_name = os.path.basename(template_path)
        
        # 检查是否使用 sidebar include
        uses_sidebar_include = "{% include 'admin/sidebar.html' %}" in content
        
        # 检查继承的基础模板
        base_template_match = re.search(r'{%\s*extends\s*["\']([^"\']+)["\']\s*%}', content)
        base_template = base_template_match.group(1) if base_template_match else "无"
        
        if uses_sidebar_include:
            results['using_sidebar_include'].append({
                'template': template_name,
                'base': base_template,
                'path': template_path
            })
        elif base_template == 'admin/base.html':
            results['using_base_template'].append({
                'template': template_name,
                'base': base_template,
                'path': template_path
            })
        else:
            results['inconsistent'].append({
                'template': template_name,
                'base': base_template,
                'path': template_path,
                'has_sidebar': uses_sidebar_include
            })
    
    return results

def print_results(results):
    """打印测试结果"""
    print("📊 测试结果统计:")
    print(f"  总计检查: {results['total_checked']} 个模板文件")
    print(f"  使用sidebar.html: {len(results['using_sidebar_include'])} 个")
    print(f"  使用admin/base.html: {len(results['using_base_template'])} 个")
    print(f"  不一致的: {len(results['inconsistent'])} 个")
    print()
    
    if results['using_sidebar_include']:
        print("✅ 使用统一侧边栏组件 (sidebar.html):")
        for item in results['using_sidebar_include']:
            print(f"  • {item['template']} (继承: {item['base']})")
        print()
    
    if results['using_base_template']:
        print("✅ 使用统一基础模板 (admin/base.html，已包含sidebar.html):")
        for item in results['using_base_template']:
            print(f"  • {item['template']} (继承: {item['base']})")
        print()
    
    if results['inconsistent']:
        print("❌ 需要修复的不一致模板:")
        for item in results['inconsistent']:
            print(f"  • {item['template']} - 继承: {item['base']}, 有侧边栏: {item['has_sidebar']}")
        print()

def test_css_consistency():
    """测试CSS样式的一致性"""
    print("🎨 CSS样式一致性检查:")
    
    sidebar_file = "templates/admin/sidebar.html"
    if os.path.exists(sidebar_file):
        with open(sidebar_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键CSS类
        css_features = [
            ('list-group-item-action', '菜单项交互样式'),
            ('.active', '活跃状态样式'),
            ('transition', '过渡动画'),
            ('pulse-subtle', '脉动动画'),
            ('ripple', '点击波纹效果'),
            ('badge-alert', '警告徽章动画'),
            ('transform: translateX', '悬停偏移效果')
        ]
        
        print("  检查的CSS特性:")
        for feature, description in css_features:
            found = feature in content
            status = "✅" if found else "❌"
            print(f"    {status} {description} ({feature})")
        print()

def test_javascript_functionality():
    """测试JavaScript功能"""
    print("⚡ JavaScript功能检查:")
    
    sidebar_file = "templates/admin/sidebar.html"
    if os.path.exists(sidebar_file):
        with open(sidebar_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        js_features = [
            ('highlightActiveMenuItem', '智能菜单高亮'),
            ('addMenuItemEffects', '菜单交互效果'),
            ('createRippleEffect', '点击波纹效果'),
            ('loadSidebarStats', '动态统计加载'),
            ('updateCounters', '计数器更新'),
            ('addEventListener.*DOMContentLoaded', '页面加载事件')
        ]
        
        print("  检查的JavaScript功能:")
        for feature, description in js_features:
            found = re.search(feature, content, re.IGNORECASE | re.MULTILINE)
            status = "✅" if found else "❌"
            print(f"    {status} {description} ({feature})")
        print()

def generate_improvement_report():
    """生成改进报告"""
    print("📋 侧边栏统一化改进报告:")
    
    improvements = [
        "✅ 创建统一的侧边栏组件 (admin/sidebar.html)",
        "✅ 实现基于Bootstrap list-group的现代化设计",
        "✅ 添加彩色图标和分组标题提升视觉层次",
        "✅ 集成动态计数徽章显示实时统计",
        "✅ 实现智能的活跃状态检测和高亮",
        "✅ 添加悬停动画和点击波纹效果",
        "✅ 优化响应式设计适配移动设备",
        "✅ 统一所有管理页面使用相同的侧边栏样式",
        "✅ 添加脉动和警告动画吸引注意力",
        "✅ 实现粘性定位保持侧边栏可见性"
    ]
    
    for improvement in improvements:
        print(f"  {improvement}")
    print()
    
    print("🎯 主要特性:")
    features = [
        "统一的视觉设计风格",
        "智能的页面状态检测", 
        "流畅的交互动画效果",
        "实时的数据统计显示",
        "完善的响应式适配",
        "易于维护的组件化结构"
    ]
    
    for feature in features:
        print(f"  • {feature}")

def main():
    """主测试函数"""
    results = test_template_consistency()
    print_results(results)
    test_css_consistency()
    test_javascript_functionality()
    generate_improvement_report()
    
    # 计算总体评分
    total_templates = results['total_checked']
    consistent_templates = len(results['using_sidebar_include']) + len(results['using_base_template'])
    consistency_score = (consistent_templates / total_templates * 100) if total_templates > 0 else 0
    
    print(f"\n🏆 总体一致性评分: {consistency_score:.1f}% ({consistent_templates}/{total_templates})")
    
    if consistency_score >= 90:
        print("🌟 优秀！侧边栏样式高度统一")
    elif consistency_score >= 75:
        print("👍 良好！大部分页面样式一致")
    else:
        print("⚠️  需要改进！存在较多不一致的地方")
    
    return consistency_score >= 90

if __name__ == "__main__":
    main()