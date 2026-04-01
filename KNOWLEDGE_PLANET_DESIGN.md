# 知识星球用户审核系统 - 设计文档

## 🎯 需求概述

实现一个知识星球用户审核系统，只有通过审核的用户才能下载数据集。用户需要提交购买截图申请，管理员审核后获得下载权限。

## 📊 数据库设计

### 1. 用户表扩展 (users表)
```sql
-- 在现有users表中添加字段
ALTER TABLE users ADD COLUMN is_planet_user BOOLEAN DEFAULT FALSE;  -- 是否为知识星球用户
ALTER TABLE users ADD COLUMN planet_approved_at DATETIME NULL;      -- 知识星球权限获得时间
ALTER TABLE users ADD COLUMN planet_approved_by INTEGER NULL;       -- 审核管理员ID
```

### 2. 知识星球申请表 (planet_applications)
```sql
CREATE TABLE planet_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                    -- 申请用户ID
    application_reason TEXT,                     -- 申请理由
    screenshot_filename VARCHAR(255),            -- 购买截图文件名
    status VARCHAR(20) DEFAULT 'pending',        -- 申请状态: pending, approved, rejected
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME NULL,                   -- 审核时间
    reviewed_by INTEGER NULL,                    -- 审核管理员ID
    review_comment TEXT,                         -- 审核备注
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);
```

### 3. 消息通知表 (notifications)
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id INTEGER NOT NULL,              -- 接收者ID
    sender_id INTEGER NULL,                     -- 发送者ID
    type VARCHAR(50) NOT NULL,                  -- 通知类型: application_submitted, application_approved, application_rejected
    title VARCHAR(200) NOT NULL,               -- 通知标题
    content TEXT,                              -- 通知内容
    related_id INTEGER NULL,                   -- 相关记录ID（如申请ID）
    is_read BOOLEAN DEFAULT FALSE,             -- 是否已读
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipient_id) REFERENCES users(id),
    FOREIGN KEY (sender_id) REFERENCES users(id)
);
```

## 🔄 功能流程设计

### 用户申请流程
1. **普通用户访问数据集详情页**
   - 下载按钮显示为"需要知识星球权限"
   - 显示"申请知识星球权限"按钮

2. **用户填写申请表单**
   - 申请理由（文本框）
   - 上传购买截图（图片文件）
   - 提交申请

3. **系统处理申请**
   - 保存申请信息和截图文件
   - 给所有管理员发送通知
   - 显示"申请已提交，等待审核"

### 管理员审核流程
1. **消息提醒**
   - 管理后台顶部显示未读通知数量
   - 新申请时实时显示红色徽章

2. **审核界面**
   - 待审核申请列表
   - 查看申请详情（理由、截图）
   - 审核操作（同意/拒绝 + 备注）

3. **审核结果**
   - 更新申请状态
   - 更新用户权限
   - 发送通知给用户

## 🎨 界面设计

### 1. 数据集详情页面增强
```html
<!-- 下载权限控制 -->
<div class="download-section">
    {% if current_user and current_user.is_planet_user %}
        <a href="{{ dataset.download_link }}" class="btn btn-success">
            <i class="fas fa-download"></i> 下载数据集
        </a>
    {% elif current_user %}
        <button class="btn btn-warning" onclick="showPlanetApplication()">
            <i class="fas fa-star"></i> 申请知识星球权限
        </button>
        <p class="text-muted mt-2">此数据集需要知识星球会员权限才能下载</p>
    {% else %}
        <a href="{{ url_for('auth.login') }}" class="btn btn-secondary">
            <i class="fas fa-sign-in-alt"></i> 登录后下载
        </a>
    {% endif %}
</div>
```

### 2. 申请表单模态框
```html
<!-- 知识星球申请模态框 -->
<div class="modal fade" id="planetApplicationModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5>申请知识星球下载权限</h5>
            </div>
            <div class="modal-body">
                <form id="planetApplicationForm" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label>申请理由</label>
                        <textarea class="form-control" name="reason" required></textarea>
                    </div>
                    <div class="mb-3">
                        <label>购买截图</label>
                        <input type="file" class="form-control" name="screenshot" 
                               accept="image/*" required>
                        <small class="text-muted">请上传知识星球购买截图</small>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="submit" class="btn btn-primary">提交申请</button>
            </div>
        </div>
    </div>
</div>
```

### 3. 管理员通知区域
```html
<!-- 导航栏通知 -->
<div class="nav-item dropdown">
    <a class="nav-link" href="#" id="notificationDropdown" data-bs-toggle="dropdown">
        <i class="fas fa-bell"></i>
        <span class="badge bg-danger">{{ unread_notifications_count }}</span>
    </a>
    <ul class="dropdown-menu">
        {% for notification in recent_notifications %}
        <li class="dropdown-item {{ 'fw-bold' if not notification.is_read }}">
            <div class="d-flex">
                <div class="flex-grow-1">
                    <h6 class="mb-1">{{ notification.title }}</h6>
                    <p class="mb-1">{{ notification.content }}</p>
                    <small>{{ notification.created_at.strftime('%m/%d %H:%M') }}</small>
                </div>
            </div>
        </li>
        {% endfor %}
    </ul>
</div>
```

### 4. 管理员审核页面
```html
<!-- 申请审核列表 -->
<div class="card">
    <div class="card-header">
        <h5>知识星球申请管理</h5>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table">
                <thead>
                    <tr>
                        <th>申请用户</th>
                        <th>申请时间</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for application in applications %}
                    <tr>
                        <td>
                            <div>
                                <strong>{{ application.user.username }}</strong>
                                <br><small>{{ application.user.email }}</small>
                            </div>
                        </td>
                        <td>{{ application.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>
                            <span class="badge bg-{{ 'warning' if application.status == 'pending' else 'success' if application.status == 'approved' else 'danger' }}">
                                {{ {'pending': '待审核', 'approved': '已通过', 'rejected': '已拒绝'}[application.status] }}
                            </span>
                        </td>
                        <td>
                            {% if application.status == 'pending' %}
                            <button class="btn btn-sm btn-success" onclick="reviewApplication({{ application.id }}, 'approve')">
                                通过
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="reviewApplication({{ application.id }}, 'reject')">
                                拒绝
                            </button>
                            {% endif %}
                            <button class="btn btn-sm btn-info" onclick="viewApplication({{ application.id }})">
                                查看详情
                            </button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
```

## 🔧 技术实现要点

### 1. 路由设计
```python
# 用户申请相关
@app.route('/apply/planet', methods=['GET', 'POST'])
@login_required
def apply_planet_membership()

# 管理员审核相关  
@app.route('/admin/planet/applications')
@admin_required
def list_planet_applications()

@app.route('/admin/planet/applications/<int:app_id>/review', methods=['POST'])
@admin_required
def review_planet_application(app_id)

# 通知相关
@app.route('/api/notifications')
@login_required
def get_notifications()

@app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id)
```

### 2. 权限装饰器
```python
def planet_user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_planet_user:
            flash('需要知识星球会员权限', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
```

### 3. 文件上传处理
```python
def save_screenshot(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'screenshots', filename)
        file.save(file_path)
        return filename
    return None
```

### 4. 消息通知系统
```python
def create_notification(recipient_id, notification_type, title, content, related_id=None, sender_id=None):
    notification = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=notification_type,
        title=title,
        content=content,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def notify_all_admins(title, content, related_id=None, sender_id=None):
    admin_users = User.query.filter_by(role='admin').all()
    for admin in admin_users:
        create_notification(admin.id, 'application_submitted', title, content, related_id, sender_id)
```

## 📱 用户体验优化

### 1. 状态提示
- 申请提交后显示进度条
- 实时显示申请状态
- 审核结果邮件通知

### 2. 界面优化
- 响应式设计
- 图片预览功能
- 批量操作支持

### 3. 安全考虑
- 文件类型验证
- 文件大小限制
- 图片压缩处理
- 防重复提交

## 🚀 实现优先级

### Phase 1 - 核心功能
1. 数据库表创建和用户模型扩展
2. 基本的申请提交功能
3. 简单的管理员审核界面

### Phase 2 - 体验优化
1. 消息通知系统
2. 文件上传优化
3. 界面美化

### Phase 3 - 高级功能
1. 批量审核
2. 邮件通知
3. 统计报表

这个设计确保了功能的完整性和用户体验的优化，你觉得这个方案如何？需要我开始实现哪个部分？