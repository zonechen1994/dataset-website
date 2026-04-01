# 图片上传功能使用指南

本文档介绍了数据集网站的本地化图片上传功能。

## 功能概述

### 1. 百度网盘链接支持
- **数据库字段**: 为数据集添加了 `baidu_pan_link` 和 `baidu_pan_password` 字段
- **MD解析器**: 自动从Markdown文件中提取百度网盘链接和提取码
- **前端显示**: 在数据集详情页面显示百度网盘下载链接和提取码
- **表单支持**: 创建和编辑数据集时可以手动添加百度网盘信息

### 2. 本地化图片上传
- **拖放上传**: 支持拖放图片文件到上传区域
- **文件管理**: 图片自动存储到 `static/images/datasets/` 目录
- **图片优化**: 自动压缩和优化图片大小和质量
- **相对路径**: 使用相对路径确保部署后正常访问

## 使用方法

### 数据库迁移

首先运行数据库迁移脚本，为现有数据库添加百度网盘字段：

```bash
# 备份数据库
python dataset_website/migrate_baidu_pan.py --backup

# 执行迁移
python dataset_website/migrate_baidu_pan.py
```

### MD文件中添加百度网盘信息

在数据集Markdown文件中，可以使用以下格式添加百度网盘信息：

```markdown
## 来源信息

| 官方网站 | https://example.com/dataset |
|----------|----------------------------|
| 下载链接 | https://official.example.com/download |
| 百度网盘 | https://pan.baidu.com/s/1234567890abcdef |
| 提取码 | xyz1 |
| 论文链接 | https://arxiv.org/abs/2023.12345 |
```

支持的百度网盘字段名称：
- `百度网盘`, `百度云`, `网盘链接`, `网盘地址`, `BaiduPan`
- `提取码`, `密码`, `提取密码`, `访问密码`

### 创建/编辑数据集时上传图片

1. **拖放上传**：
   - 直接将图片文件拖放到上传区域
   - 支持多选和批量上传
   - 自动显示上传进度和结果

2. **点击上传**：
   - 点击上传区域或"选择文件"按钮
   - 选择本地图片文件上传

3. **URL链接方式**（备用）：
   - 点击"使用URL链接方式"按钮
   - 在文本框中每行输入一个图片URL

### 支持的图片格式

- **文件格式**: JPG, JPEG, PNG, GIF, WebP
- **文件大小**: 最大5MB
- **数量限制**: 最多10张图片
- **自动优化**: 自动调整尺寸(最大1200x1200)和压缩质量

## 技术实现

### 前端组件

- **JavaScript类**: `ImageUploader` (image_upload.js)
- **拖放支持**: HTML5 Drag & Drop API
- **文件验证**: 客户端格式和大小检查
- **预览功能**: 实时图片预览和删除

### 后端API

- **上传接口**: `POST /api/upload-image`
- **删除接口**: `DELETE /api/delete-image` 
- **信息查询**: `GET /api/images/info`
- **图片处理**: 使用Pillow库进行优化

### 文件存储

```
dataset_website/
├── static/
│   └── images/
│       └── datasets/          # 数据集图片存储目录
│           ├── 20231125_abc123_def456.jpg
│           ├── 20231125_def789_ghi012.png
│           └── ...
└── uploads/
    └── screenshots/           # 其他上传文件
```

### 文件命名规则

格式: `{timestamp}_{content_hash}_{uuid}.{ext}`
- `timestamp`: 上传时间戳 (YYYYMMDD_HHMMSS)
- `content_hash`: 文件内容MD5哈希前8位 (去重)
- `uuid`: 随机UUID前8位 (唯一性)
- `ext`: 原始文件扩展名

示例: `20231125_143022_a1b2c3d4_e5f6g7h8.jpg`

## 部署注意事项

### 1. 目录权限
确保Web服务器对图片目录有写权限：
```bash
chmod 755 dataset_website/static/images/datasets/
```

### 2. 依赖安装
安装图片处理依赖：
```bash
pip install -r requirements.txt
# 包含 Pillow==10.0.0
```

### 3. 服务器配置
- 配置Web服务器正确提供静态文件服务
- 设置合适的文件大小限制
- 考虑CDN或图片压缩服务

### 4. 数据库备份
在执行迁移前务必备份数据库：
```bash
python dataset_website/migrate_baidu_pan.py --backup
```

## 故障排除

### 常见问题

1. **图片上传失败**
   - 检查文件大小和格式
   - 确认目录权限
   - 查看服务器错误日志

2. **图片显示异常**
   - 确认静态文件路由配置
   - 检查相对路径是否正确
   - 验证文件是否存在

3. **百度网盘链接不显示**
   - 运行数据库迁移脚本
   - 检查MD文件格式
   - 重新导入数据集

### 日志查看
```bash
# 查看Python应用日志
tail -f app.log

# 查看Web服务器日志
tail -f /var/log/nginx/error.log
```

## 更新历史

- **v1.0** (2024-08): 初版百度网盘链接支持
- **v1.1** (2024-08): 添加本地化图片上传功能
- **v1.2** (2024-08): 图片优化和相对路径支持

---

如有问题，请查看应用程序日志或联系开发团队。