# 人体器官数据集展示网站

一个基于Flask的数据集管理和展示网站，专门用于展示和管理人体器官相关的医学影像数据集。

## 功能特性

### 核心功能
- 📊 **数据集展示**: 清晰展示数据集的所有关键信息
- 🔍 **智能搜索**: 支持关键字搜索和多维度筛选
- 📝 **CRUD操作**: 完整的数据集增删改查功能
- 📤 **MD文件解析**: 自动解析Markdown文件提取数据集信息
- 🏷️ **分类管理**: 按器官分类组织数据集

### 用户界面
- 🎨 **现代化设计**: 简洁美观的用户界面
- 📱 **响应式布局**: 完美适配桌面和移动设备
- ⚡ **交互优化**: 流畅的用户体验和动画效果
- 🔑 **键盘快捷键**: 支持Ctrl+K快速搜索

### 技术特性
- 🚀 **高性能**: 优化的数据库查询和前端渲染
- 🔒 **数据安全**: 完善的输入验证和错误处理
- 🔧 **易于部署**: 简单的部署流程和配置

## 技术栈

- **后端**: Flask + SQLAlchemy + SQLite
- **前端**: Bootstrap 5 + HTML5 + CSS3 + JavaScript
- **数据解析**: Python Markdown解析器
- **样式**: 自定义CSS + Font Awesome图标

## 项目结构

```
dataset_website/
├── app.py                 # Flask应用主文件
├── models.py              # 数据模型定义
├── config.py              # 配置文件
├── md_parser.py           # Markdown文件解析器
├── init_database.py       # 数据库初始化脚本
├── requirements.txt       # Python依赖
├── dataset.db             # SQLite数据库文件
├── templates/             # HTML模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── dataset_detail.html # 数据集详情
│   ├── edit_dataset.html # 编辑数据集
│   ├── new_dataset.html  # 新建数据集
│   └── upload.html       # 文件上传
├── static/               # 静态文件
│   ├── css/
│   │   └── custom.css    # 自定义样式
│   └── js/
│       └── main.js       # 主要JavaScript
├── uploads/              # 文件上传目录
└── tests/                # 测试文件
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd dataset_website

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

```bash
# 初始化数据库并导入现有MD文件
python init_database.py --init
```

### 3. 启动应用

```bash
# 启动开发服务器
python app.py
```

访问 `http://localhost:5001` 查看网站。

## 使用指南

### 数据集管理

1. **查看数据集**: 在首页浏览所有数据集，支持分类筛选和搜索
2. **添加数据集**: 
   - 手动填写：点击"手动添加数据集"
   - 文件上传：上传MD文件自动解析
3. **编辑数据集**: 在数据集详情页点击"编辑"
4. **删除数据集**: 在数据集详情页点击"删除"

### 搜索和筛选

- **关键字搜索**: 在搜索框输入关键词（支持Ctrl+K快捷键）
- **分类筛选**: 选择器官分类（腹部、骨头、内窥镜、全身）
- **模态筛选**: 按成像模态筛选（CT、MRI、PET等）
- **任务筛选**: 按任务类型筛选（分割、分类、检测等）
- **组合筛选**: 同时使用多个筛选条件

### MD文件格式

网站支持解析标准格式的Markdown文件，需包含以下信息：

```markdown
# 数据集名称

## 数据集信息
数据集的详细描述...

### 数据集元信息
| 维度 | 模态 | 任务类型 | 解剖结构 | 解剖区域 | 类别数 | 数据量 | 文件格式 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3D | CT | 分割 | 肝脏 | 腹部 | 40 | 22 | dicom,vtk |

## 来源信息
| 官方网站 | https://example.com |
| 下载链接 | https://example.com/download |
| 文章地址 | https://example.com/paper |
| 数据公开日期 | 2023 |

## 作者及机构
- 张三 (某某大学)
- 李四 (某某研究所)

## 引用
```bibtex
@article{example2023,
  title={Example Dataset},
  author={Zhang, San and Li, Si},
  year={2023}
}
```

## 数据库管理

### 备份数据库
```bash
cp dataset.db dataset_backup.db
```

### 清空数据库
```bash
python init_database.py --clear
```

### 重新初始化
```bash
python init_database.py --init
```

## 开发和测试

### 运行测试
```bash
# 测试基本功能
python test_app.py

# 测试CRUD操作
python test_crud.py

# 测试搜索功能
python test_search.py

# 测试上传功能
python test_upload.py

# 测试UI功能
python test_ui.py
```

### 开发模式
```bash
# 开启调试模式
export FLASK_DEBUG=1
python app.py
```

## 部署

### 生产环境部署

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
```

3. **使用WSGI服务器**
```bash
# 使用Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:create_app()
```

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 5001
CMD ["python", "app.py"]
```

## 性能优化

- 数据库索引已优化
- 静态文件缓存
- 分页显示减少加载时间
- 响应式设计优化移动端性能

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用MIT许可证。详见 `LICENSE` 文件。

## 联系方式

如有问题或建议，请提交Issue或联系开发者。

---

**注意**: 这是一个演示项目，用于展示数据集管理系统的基本功能。在生产环境中使用前，请确保进行充分的安全性测试和性能优化。