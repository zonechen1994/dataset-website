# 用户系统功能说明

## 🎉 功能概览

本系统已升级为完整的用户管理系统，支持：

- ✅ **用户注册登录系统**
- ✅ **管理员用户管理**  
- ✅ **权限控制和路由保护**
- ✅ **个人资料管理**
- ✅ **密码安全管理**

## 🚀 快速启动

```bash
cd dataset_website
python run_enhanced.py
```

访问地址：http://localhost:5003

## 👥 用户角色

### 🔑 管理员 (admin)
- **默认账户：** admin / admin123
- **权限：**
  - 管理所有数据集（增删改查）
  - 管理用户账户
  - 系统配置管理
  - 访问管理后台

### 👤 普通用户 (user) 
- **注册方式：** 网站注册或管理员创建
- **权限：**
  - 浏览数据集
  - 查看数据集详情
  - 管理个人资料

### 👁️ 访客 (visitor)
- **权限：**
  - 浏览数据集
  - 查看数据集详情

## 🌟 主要功能

### 1. 用户认证系统

#### 用户注册
- **URL：** `/register`
- **功能：** 新用户注册账户
- **字段：** 用户名、邮箱、密码、姓名
- **验证：** 用户名唯一性、邮箱格式、密码强度

#### 用户登录
- **URL：** `/login`
- **功能：** 用户登录系统
- **特性：** 记住我功能、重定向到目标页面

#### 用户登出
- **URL：** `/logout`
- **功能：** 安全退出登录

### 2. 个人资料管理

#### 个人资料查看
- **URL：** `/profile`
- **功能：** 查看个人信息和统计

#### 编辑个人资料
- **URL：** `/profile/edit`
- **功能：** 修改姓名、邮箱

#### 修改密码
- **URL：** `/profile/change-password`
- **功能：** 安全修改密码

### 3. 管理员用户管理

#### 用户列表
- **URL：** `/admin/users`
- **功能：** 查看所有用户、搜索筛选
- **特性：** 分页显示、状态筛选

#### 新建用户
- **URL：** `/admin/users/new`
- **功能：** 管理员创建新用户账户

#### 编辑用户
- **URL：** `/admin/users/{id}/edit`
- **功能：** 修改用户信息、角色

#### 用户详情
- **URL：** `/admin/users/{id}`
- **功能：** 查看用户详细信息

#### 用户操作
- 🔄 **切换状态：** 激活/禁用用户
- 🔑 **重置密码：** 为用户设置新密码
- 🗑️ **删除用户：** 删除用户账户（有保护机制）

### 4. 权限控制

#### 装饰器
- `@login_required` - 需要登录
- `@admin_required` - 需要管理员权限

#### 路由保护
- 数据集管理：仅管理员
- 用户管理：仅管理员  
- 个人资料：需要登录

## 🔧 技术架构

### 数据库模型
```python
# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # 'admin' 或 'user'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
```

### 认证系统
- **Flask-Login：** 用户会话管理
- **Werkzeug Security：** 密码加密
- **Session 兼容：** 支持旧版本session认证

### 蓝图架构
- `auth_bp` - 用户认证路由
- `user_admin_bp` - 用户管理路由

## 📁 文件结构

```
dataset_website/
├── app_enhanced.py          # 增强版主应用
├── auth_enhanced.py         # 认证系统
├── auth_routes.py          # 用户认证路由
├── user_admin_routes.py    # 用户管理路由
├── models.py               # 数据模型（已更新）
├── run_enhanced.py         # 启动脚本
├── templates/
│   ├── base_enhanced.html  # 增强版基础模板
│   ├── auth/              # 用户认证模板
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   ├── edit_profile.html
│   │   └── change_password.html
│   └── admin/
│       ├── base.html      # 管理后台基础模板
│       └── users/         # 用户管理模板
│           ├── list.html
│           ├── form.html
│           └── detail.html
└── ...
```

## 🔒 安全特性

### 密码安全
- 🔐 Werkzeug密码哈希加密
- 📏 密码长度验证（至少6位）
- 🔄 密码修改需验证当前密码

### 用户保护
- 🚫 防止删除最后一个管理员
- 🛡️ 超级管理员账户保护
- ⚠️ 危险操作二次确认

### 权限验证
- 🔑 基于角色的访问控制
- 🚪 路由级权限保护
- 📊 API接口权限验证

## 🌐 界面特性

### 响应式设计
- 📱 移动设备友好
- 🎨 Bootstrap 5 UI框架
- 🌈 Font Awesome 图标

### 用户体验
- 💡 实时表单验证
- 🔔 Flash消息提示
- 📄 分页显示
- 🔍 搜索筛选功能

## 🎯 使用场景

### 场景1：新用户注册
1. 访问 `/register`
2. 填写注册信息
3. 系统验证并创建账户
4. 自动跳转到登录页面

### 场景2：管理员创建用户
1. 管理员登录系统
2. 访问 `/admin/users/new`
3. 填写用户信息，设置角色
4. 创建成功，用户可正常登录

### 场景3：用户权限管理
1. 管理员访问用户管理页面
2. 查看用户列表，搜索目标用户
3. 编辑用户角色或状态
4. 必要时重置密码或删除账户

## 🔄 系统升级

### 从旧系统迁移
- ✅ 保持向后兼容
- ✅ 旧session认证仍有效
- ✅ 自动创建默认管理员账户
- ✅ 原有数据集功能不变

### 新功能特性
- 🆕 完整的用户管理
- 🆕 个人资料系统
- 🆕 权限控制机制
- 🆕 统计API接口

## 🚨 注意事项

1. **生产环境配置：**
   - 修改默认管理员密码
   - 配置安全的SECRET_KEY
   - 使用HTTPS协议

2. **数据库迁移：**
   - 首次运行会自动创建表
   - 自动创建默认admin账户

3. **权限管理：**
   - 谨慎分配管理员权限
   - 定期检查用户账户状态
   - 建议定期更改密码

## 📊 API接口

### 统计接口
- **URL：** `/api/stats`
- **方法：** GET
- **返回：** 系统统计数据

```json
{
    "datasets": 10,
    "users": 5,
    "categories": 3,
    "active_users": 4,
    "admin_users": 1
}
```

## 🎉 总结

新的用户系统为数据集管理网站提供了：

- **完整的用户生命周期管理**
- **灵活的权限控制机制** 
- **友好的用户界面体验**
- **强大的管理员工具**
- **安全的认证保护**

系统现在可以支持多用户协作，提供差异化的功能权限，适用于团队或组织的数据集管理需求！