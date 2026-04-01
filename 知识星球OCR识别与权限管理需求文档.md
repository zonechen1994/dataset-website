# 知识星球OCR识别与权限管理需求文档 (PRD)

## 🎯 需求概述

### 业务背景
现有的知识星球权限申请系统需要管理员手动审核。为提升效率，引入智谱AI GLM-4V多模态大模型自动识别到期时间，实现权限到期自动管理。

### 核心目标
1. **自动识别到期时间**：通过智谱AI GLM-4V多模态大模型自动识别知识星球截图中的红框内容（到期时间）
2. **权限到期管理**：自动检测并取消过期用户的下载权限
3. **邮件提醒服务**：在权限即将到期和已到期时自动发送邮件提醒
4. **示例图片引导**：在申请页面提供示例图片，指导用户正确上传截图

### 示例图片说明
- **示例图片位置**：`c:\Work\数据集网站\第二版\数据集md样例\image.png`
- **红框内容格式**：`截至权限到期至2026/7/16`
- **识别目标**：提取日期 `2026/7/16` 或识别"永久"标识

---

## 🔧 技术方案

### OCR技术选型：智谱AI GLM-4V多模态大模型

#### 选择理由
- ✅ 强大的视觉理解能力，识别准确率高（90%+）
- ✅ 支持复杂图像场景理解，不仅限于文字识别
- ✅ 官方Python SDK支持，易于集成
- ✅ 可以通过提示词引导模型提取特定信息
- ✅ 国产大模型，支持中文场景

#### API配置
```python
# 智谱AI GLM-4V配置
GLM_CONFIG = {
    'API_KEY': 'your_glm_api_key'
}
```

#### 接口文档
- 官方文档：https://bigmodel.cn/dev/api
- Python SDK：`pip install zhipuai`
- 模型：glm-4v-flash（快速视觉理解版本）

---

## 📊 数据库设计

### 1. 扩展 `users` 表
```sql
-- 添加权限到期时间字段
ALTER TABLE users ADD COLUMN planet_expiry_date DATETIME NULL COMMENT '知识星球权限到期时间（NULL表示永久）';

-- 添加权限时长字段
ALTER TABLE users ADD COLUMN planet_membership_duration INTEGER NULL COMMENT '知识星球会员时长（月数，NULL表示永久）';

-- 添加索引以优化到期检查查询
CREATE INDEX idx_planet_expiry ON users(planet_expiry_date);
CREATE INDEX idx_planet_user_active ON users(is_planet_user, planet_expiry_date);
```

**字段说明**：
- `planet_expiry_date`：到期时间
  - `NULL` = 永久会员
  - 具体日期 = 到指定日期到期
  - 配合 `is_planet_user` 字段使用
- `planet_membership_duration`：权限时长（单位：月）
  - `NULL` = 永久会员
  - `1` = 1个月
  - `3` = 3个月（季度）
  - `6` = 6个月（半年）
  - `12` = 12个月（年度）
  - 其他数值 = 其他时长
  - **用途**：用于数据统计分析、续期计算、用户购买习惯分析

### 2. 扩展 `planet_applications` 表
```sql
-- 添加OCR识别相关字段
ALTER TABLE planet_applications ADD COLUMN ocr_raw_text TEXT COMMENT 'OCR识别的原始文本';
ALTER TABLE planet_applications ADD COLUMN ocr_extracted_date DATETIME NULL COMMENT 'OCR提取的到期日期';
ALTER TABLE planet_applications ADD COLUMN ocr_confidence FLOAT COMMENT 'OCR识别置信度';
ALTER TABLE planet_applications ADD COLUMN is_permanent_member BOOLEAN DEFAULT FALSE COMMENT '是否为永久会员';
ALTER TABLE planet_applications ADD COLUMN date_confirmed_by_user BOOLEAN DEFAULT FALSE COMMENT '用户是否确认了识别的日期';
ALTER TABLE planet_applications ADD COLUMN membership_duration INTEGER NULL COMMENT '会员时长（月数）';
```

**字段说明**：
- `ocr_raw_text`：OCR识别的完整原始文本，用于调试和记录
- `ocr_extracted_date`：从OCR文本中提取的到期日期
- `ocr_confidence`：识别置信度（0-1之间），用于判断是否需要人工确认
- `is_permanent_member`：标记是否识别出"永久"关键字
- `date_confirmed_by_user`：用户是否已确认识别结果
- `membership_duration`：会员时长（月数）
  - 从申请时间到到期时间计算得出
  - 便于统计用户购买习惯（1月、3月、6月、12月等）
  - 用于续期时自动计算新的到期时间

### 3. 新增 `planet_expiry_notifications` 表
```sql
CREATE TABLE planet_expiry_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notification_type VARCHAR(20) NOT NULL COMMENT '通知类型: expiring_soon, expired',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATETIME NOT NULL,
    days_before_expiry INTEGER COMMENT '到期前几天发送（仅expiring_soon类型）',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 添加索引
CREATE INDEX idx_expiry_notifications_user ON planet_expiry_notifications(user_id, sent_at);
```

**用途**：记录已发送的到期提醒，避免重复发送

---

## 💻 核心功能模块

### 模块1: OCR识别服务 (`ocr_service.py`)

#### 功能职责
- 调用百度OCR API识别图片文字
- 从OCR结果中提取到期时间
- 支持多种日期格式识别
- 处理"永久会员"标识

#### 核心函数

```python
def recognize_planet_screenshot(image_path):
    """
    识别知识星球截图并提取到期时间
    
    Args:
        image_path (str): 截图文件路径
    
    Returns:
        dict: {
            'success': bool,              # 是否成功识别
            'raw_text': str,              # OCR原始文本
            'expiry_date': datetime,      # 提取的到期日期（永久会员为None）
            'is_permanent': bool,         # 是否为永久会员
            'confidence': float,          # 识别置信度(0-1)
            'duration_months': int,       # 权限时长（月数，永久会员为None）
            'error': str                  # 错误信息（如有）
        }
    """
    pass

def calculate_membership_duration(start_date, expiry_date):
    """
    计算会员时长（月数）
    
    Args:
        start_date (datetime): 开始时间（申请时间）
        expiry_date (datetime): 到期时间
    
    Returns:
        int: 时长（月数），向上取整
    
    Examples:
        - 申请时间: 2026-01-26, 到期时间: 2026-02-26 -> 1个月
        - 申请时间: 2026-01-26, 到期时间: 2026-04-26 -> 3个月
        - 申请时间: 2026-01-26, 到期时间: 2027-01-26 -> 12个月
    """
    from dateutil.relativedelta import relativedelta
    
    # 计算月份差
    delta = relativedelta(expiry_date, start_date)
    months = delta.years * 12 + delta.months
    
    # 如果有余天，向上取整到下个月
    if delta.days > 0:
        months += 1
    
    return months

def extract_date_from_text(text):
    """
    从OCR文本中提取日期
    
    支持格式：
    - "截至权限到期至2026/7/16"
    - "2026年7月16日"
    - "2026-07-16"
    - "永久会员"、"永久续费"
    
    Args:
        text (str): OCR识别的文本
    
    Returns:
        tuple: (datetime对象 或 None, 是否永久会员)
    """
    pass
```

#### 日期格式正则表达式
```python
DATE_PATTERNS = [
    r'(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})',  # 2026/7/16, 2026-7-16, 2026年7月16日
    r'截至.*?(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',  # 截至权限到期至2026/7/16
    r'到期.*?(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',  # 到期至2026/7/16
]

PERMANENT_KEYWORDS = ['永久', '终身', '无限期']
```

---

### 模块2: 申请流程优化 (`planet_routes.py`)

#### 修改申请提交流程

**原流程**：
```
用户上传截图 → 保存文件 → 创建申请 → 通知管理员
```

**新流程**：
```
用户上传截图 
  ↓
OCR自动识别到期时间
  ↓
显示识别结果供用户确认/修改
  ↓
用户确认后提交申请
  ↓
保存OCR结果和确认的日期
  ↓
通知管理员（包含识别的日期信息）
```

#### 核心路由修改

```python
@planet_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    """申请知识星球权限（带OCR识别）"""
    
    if request.method == 'POST':
        # Step 1: 临时保存图片
        screenshot = request.files.get('screenshot')
        temp_path = save_temp_screenshot(screenshot)
        
        # Step 2: OCR识别
        ocr_result = recognize_planet_screenshot(temp_path)
        
        # Step 3: 返回识别结果供用户确认
        if ocr_result['success']:
            return jsonify({
                'ocr_result': {
                    'expiry_date': ocr_result['expiry_date'].strftime('%Y-%m-%d') if ocr_result['expiry_date'] else None,
                    'is_permanent': ocr_result['is_permanent'],
                    'confidence': ocr_result['confidence'],
                    'raw_text': ocr_result['raw_text']
                }
            })
```

#### 新增路由：确认并提交申请
```python
@planet_bp.route('/apply/confirm', methods=['POST'])
@login_required
def confirm_and_submit_application():
    """用户确认OCR结果并提交申请"""
    
    # 获取用户确认的数据
    data = request.get_json()
    screenshot_filename = data.get('screenshot_filename')
    expiry_date = data.get('expiry_date')  # 用户确认或修改的日期
    is_permanent = data.get('is_permanent', False)
    ocr_raw_text = data.get('ocr_raw_text')
    ocr_confidence = data.get('ocr_confidence')
    
    # 计算会员时长（如果不是永久会员）
    membership_duration = None
    if not is_permanent and expiry_date:
        from ocr_service import calculate_membership_duration
        expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
        current_time = get_china_datetime()
        membership_duration = calculate_membership_duration(current_time, expiry_dt)
    
    # 创建申请记录
    application = PlanetApplication(
        user_id=current_user.id,
        application_reason=data.get('reason'),
        screenshot_filename=screenshot_filename,
        ocr_raw_text=ocr_raw_text,
        ocr_extracted_date=datetime.strptime(expiry_date, '%Y-%m-%d') if expiry_date else None,
        ocr_confidence=ocr_confidence,
        is_permanent_member=is_permanent,
        date_confirmed_by_user=True,
        membership_duration=membership_duration  # 新增：记录会员时长
    )
    
    db.session.add(application)
    db.session.commit()
    
    # 通知管理员
    notify_all_admins(...)
```

---

### 模块3: 管理员审核优化

#### 审核界面显示OCR信息

**管理员审核页面新增显示内容**：
- OCR识别的原始文本
- 提取的到期日期
- 是否为永久会员
- 识别置信度
- 用户是否已确认

#### 审核通过逻辑修改

```python
@planet_bp.route('/admin/applications/<int:app_id>/review', methods=['POST'])
@admin_required
def admin_review_application(app_id):
    """管理员审核申请（自动设置到期时间和权限时长）"""
    
    application = PlanetApplication.query.get_or_404(app_id)
    action = request.form.get('action')  # 'approve' 或 'reject'
    
    if action == 'approve':
        user = application.user
        user.is_planet_user = True
        user.planet_approved_at = get_china_datetime()
        user.planet_approved_by = current_user.id
        
        # ✨ 新增：自动设置到期时间和会员时长
        if application.is_permanent_member:
            user.planet_expiry_date = None  # 永久会员
            user.planet_membership_duration = None  # 永久会员无时长限制
        elif application.ocr_extracted_date:
            user.planet_expiry_date = application.ocr_extracted_date
            user.planet_membership_duration = application.membership_duration  # 使用申请时计算的时长
        
        # 管理员可以手动修改到期时间（通过表单）
        manual_expiry = request.form.get('manual_expiry_date')
        manual_duration = request.form.get('manual_duration')  # 管理员手动输入时长（月数）
        
        if manual_expiry:
            user.planet_expiry_date = datetime.strptime(manual_expiry, '%Y-%m-%d')
            
            # 如果手动修改了到期时间，重新计算时长
            if not application.is_permanent_member:
                from ocr_service import calculate_membership_duration
                user.planet_membership_duration = calculate_membership_duration(
                    user.planet_approved_at,
                    user.planet_expiry_date
                )
        
        # 管理员也可以直接手动指定时长
        if manual_duration and manual_duration.isdigit():
            user.planet_membership_duration = int(manual_duration)
        
        db.session.commit()
```

---

### 模块4: 定时任务 - 权限到期检查 (`scheduler_tasks.py`)

#### 任务1: 检查并撤销过期权限

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

def check_and_revoke_expired_permissions():
    """
    检查并撤销过期用户的知识星球权限
    建议执行频率：每天凌晨2点
    """
    from models import User, db
    from email_service import send_permission_expired_email
    
    current_time = get_china_datetime()
    
    # 查找所有已过期但权限仍开启的用户
    expired_users = User.query.filter(
        User.is_planet_user == True,
        User.planet_expiry_date < current_time,
        User.planet_expiry_date.isnot(None)  # 排除永久会员
    ).all()
    
    for user in expired_users:
        # 撤销权限
        user.is_planet_user = False
        
        # 发送到期通知邮件
        send_permission_expired_email(user)
        
        # 记录通知发送
        notification = PlanetExpiryNotification(
            user_id=user.id,
            notification_type='expired',
            expiry_date=user.planet_expiry_date
        )
        db.session.add(notification)
    
    db.session.commit()
    
    logger.info(f"已撤销 {len(expired_users)} 个过期用户的权限")
```

#### 任务2: 提前提醒即将到期

```python
def send_expiry_reminders():
    """
    发送权限到期提醒
    提醒时间点：到期前7天、3天、1天
    建议执行频率：每天上午10点
    """
    from models import User, PlanetExpiryNotification, db
    from email_service import send_permission_expiring_soon_email
    
    current_time = get_china_datetime()
    reminder_days = [7, 3, 1]  # 提前7天、3天、1天提醒
    
    for days in reminder_days:
        target_date = current_time + timedelta(days=days)
        target_start = target_date.replace(hour=0, minute=0, second=0)
        target_end = target_date.replace(hour=23, minute=59, second=59)
        
        # 查找即将到期的用户
        expiring_users = User.query.filter(
            User.is_planet_user == True,
            User.planet_expiry_date >= target_start,
            User.planet_expiry_date <= target_end
        ).all()
        
        for user in expiring_users:
            # 检查是否已发送过该时间点的提醒
            existing_notification = PlanetExpiryNotification.query.filter_by(
                user_id=user.id,
                notification_type='expiring_soon',
                days_before_expiry=days
            ).first()
            
            if not existing_notification:
                # 发送提醒邮件
                send_permission_expiring_soon_email(user, days)
                
                # 记录通知
                notification = PlanetExpiryNotification(
                    user_id=user.id,
                    notification_type='expiring_soon',
                    expiry_date=user.planet_expiry_date,
                    days_before_expiry=days
                )
                db.session.add(notification)
        
        db.session.commit()
```

#### 定时任务初始化

```python
def init_scheduler(app):
    """初始化定时任务调度器"""
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    
    # 每天凌晨2点检查过期权限
    scheduler.add_job(
        func=check_and_revoke_expired_permissions,
        trigger='cron',
        hour=2,
        minute=0,
        id='check_expired_permissions',
        name='检查并撤销过期权限'
    )
    
    # 每天上午10点发送到期提醒
    scheduler.add_job(
        func=send_expiry_reminders,
        trigger='cron',
        hour=10,
        minute=0,
        id='send_expiry_reminders',
        name='发送权限到期提醒'
    )
    
    scheduler.start()
    logger.info("定时任务调度器已启动")
    
    return scheduler
```

---

### 模块5: 邮件服务扩展 (`email_service.py`)

#### 1. 权限即将到期提醒 (`send_permission_expiring_soon_email`)
- **触发时机**：由定时任务触发，在到期前7天、3天、1天发送。
- **关键数据**：用户姓名、到期日期、剩余天数。
- **邮件内容**：提醒用户权限即将到期，建议及时续费并重新提交申请。

#### 2. 权限已到期通知 (`send_permission_expired_email`)
- **触发时机**：由定时任务触发，在权限过期当天发送。
- **关键数据**：用户姓名、到期日期。
- **邮件内容**：通知用户下载权限已关闭，引导用户重新申请。

---

## 🎨 前端界面设计
 
### 1. 申请页面优化 (`templates/planet/apply.html`)
- **新增示例图片区**：展示标准合格的截图示例（强调红框内的到期时间）。
- **OCR结果确认区**：
  - 上传图片后自动显示OCR识别结果（日期、时长、置信度）。
  - 提供用户手动修正日期的输入框。
  - "永久会员"勾选框。
  - 必须确认识别结果后才能提交申请。

### 2. 管理员审核页面 (`templates/admin/planet/application_detail.html`)
- **OCR信息展示**：
  - 显示原始OCR文本、提取日期、置信度。
  - 显示系统自动计算的会员时长。
  - 标记用户是否已人工确认识别结果。
- **手动调整功能**：
  - 管理员可强制修改到期时间。
  - 提供快捷时长按钮（1月、3月、1年等），自动计算到期日。

---

## 📦 依赖包安装

### requirements.txt 新增内容
```txt
# OCR识别（智谱AI GLM-4V）
zhipuai>=2.0.0           # 智谱AI Python SDK

# 定时任务
APScheduler==3.10.4    # 定时任务调度器

# 日期计算
python-dateutil==2.8.2 # 用于计算会员时长的月份差

# 现有依赖（确保已安装）
Flask==2.3.0
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Flask-Mail==0.9.1
Pillow==10.0.0         # 图片处理
```

### 安装命令
```bash
pip install zhipuai
pip install APScheduler==3.10.4
pip install python-dateutil==2.8.2
```

---

## 🚀 实施步骤

### Phase 1: 数据库迁移与OCR集成（预计2天）

#### Step 1.1: 数据库扩展
```bash
# 创建数据库迁移文件
python migrate_planet_ocr.py
```

**迁移脚本** (`migrate_planet_ocr.py`):
```python
"""
知识星球OCR功能数据库迁移脚本
"""
from models import db
from app import create_app
import logging

logger = logging.getLogger(__name__)

def migrate_database():
    """执行数据库迁移"""
    app = create_app()
    
    with app.app_context():
        try:
            # 扩展users表
            db.engine.execute("""
                ALTER TABLE users 
                ADD COLUMN planet_expiry_date DATETIME NULL
            """)
            
            # 添加会员时长字段
            db.engine.execute("""
                ALTER TABLE users 
                ADD COLUMN planet_membership_duration INTEGER NULL
            """)
            
            # 扩展planet_applications表
            db.engine.execute("""
                ALTER TABLE planet_applications 
                ADD COLUMN ocr_raw_text TEXT,
                ADD COLUMN ocr_extracted_date DATETIME NULL,
                ADD COLUMN ocr_confidence FLOAT,
                ADD COLUMN is_permanent_member BOOLEAN DEFAULT FALSE,
                ADD COLUMN date_confirmed_by_user BOOLEAN DEFAULT FALSE,
                ADD COLUMN membership_duration INTEGER NULL
            """)
            
            # 创建新表
            db.engine.execute("""
                CREATE TABLE IF NOT EXISTS planet_expiry_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    notification_type VARCHAR(20) NOT NULL,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expiry_date DATETIME NOT NULL,
                    days_before_expiry INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # 创建索引
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_planet_expiry 
                ON users(planet_expiry_date)
            """)
            
            db.engine.execute("""
                CREATE INDEX IF NOT EXISTS idx_planet_user_active 
                ON users(is_planet_user, planet_expiry_date)
            """)
            
            logger.info("数据库迁移成功！")
            return True
            
        except Exception as e:
            logger.error(f"数据库迁移失败: {str(e)}")
            return False

if __name__ == '__main__':
    migrate_database()
```

#### Step 1.2: 创建OCR服务模块
```bash
# 创建文件
touch ocr_service.py
```

#### Step 1.3: 配置智谱AI GLM-4V
在 `config.py` 中添加：
```python
# 智谱AI GLM-4V配置
GLM_API_KEY = os.getenv('GLM_API_KEY', '')
```

在 `.env` 中添加：
```bash
GLM_API_KEY=your_glm_api_key
```

---

### Phase 2: 申请流程改造（预计1.5天）

#### Step 2.1: 修改申请路由
- 新增OCR识别接口
- 修改申请提交流程
- 添加确认步骤

#### Step 2.2: 更新前端页面
- 添加示例图片
- 实现OCR结果展示
- 添加用户确认逻辑

#### Step 2.3: 复制示例图片
```bash
# 将示例图片复制到static目录
cp "c:\Work\数据集网站\第二版\数据集md样例\image.png" \
   "dataset_website/static/images/planet_example.png"
```

---

### Phase 3: 定时任务实现（预计1天）

#### Step 3.1: 创建定时任务模块
```bash
touch scheduler_tasks.py
```

#### Step 3.2: 在app.py中初始化调度器
```python
from scheduler_tasks import init_scheduler

# 在create_app函数中
scheduler = init_scheduler(app)
```

#### Step 3.3: 测试定时任务
```python
# 手动触发测试
python test_scheduler.py
```

---

### Phase 4: 邮件服务扩展（预计0.5天）

#### Step 4.1: 在email_service.py中添加新邮件模板
- `send_permission_expiring_soon_email()`
- `send_permission_expired_email()`

#### Step 4.2: 测试邮件发送
```bash
python test_expiry_emails.py
```

---

### Phase 5: 管理员界面优化（预计0.5天）

#### Step 5.1: 更新审核详情页
- 显示OCR识别信息
- 添加手动调整到期时间功能

#### Step 5.2: 更新审核逻辑
- 自动设置到期时间
- 支持管理员手动修改

---

### Phase 6: 测试与部署（预计1天）

#### Step 6.1: 单元测试
```bash
# 测试OCR识别
python test_ocr_service.py

# 测试申请流程
python test_planet_application_ocr.py

# 测试定时任务
python test_scheduler_tasks.py
```

#### Step 6.2: 集成测试
- 完整申请流程测试
- 到期检查测试
- 邮件发送测试

#### Step 6.3: 部署到生产环境
```bash
# 拉取最新代码
git pull origin main

# 执行数据库迁移
python migrate_planet_ocr.py

# 重启服务
sudo systemctl restart dataset_website
```

---

## 🔐 Git管理规范

### 分支策略

#### 主分支
- `main`：生产环境代码
- `develop`：开发主分支

#### 功能分支命名
```bash
feature/planet-ocr-recognition        # OCR识别功能
feature/planet-expiry-management      # 到期管理功能
feature/planet-email-notifications    # 邮件通知功能
```

### 提交规范

#### Commit Message格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链更新

**示例**：
```bash
git commit -m "feat(planet): 添加百度OCR识别功能

- 集成百度OCR API
- 实现日期提取逻辑
- 支持多种日期格式识别
- 处理永久会员标识

Closes #123"
```

### 开发工作流

#### 1. 创建功能分支
```bash
# 从develop分支创建
git checkout develop
git pull origin develop
git checkout -b feature/planet-ocr-recognition
```

#### 2. 开发过程
```bash
# 频繁提交，保持小步快跑
git add .
git commit -m "feat(ocr): 实现OCR服务基础类"

git add .
git commit -m "feat(ocr): 添加日期提取正则表达式"

git add .
git commit -m "test(ocr): 添加OCR服务单元测试"
```

#### 3. 推送到远程
```bash
git push origin feature/planet-ocr-recognition
```

#### 4. 创建Pull Request
- 目标分支：`develop`
- 标题：`[Feature] 知识星球OCR识别功能`
- 描述：详细说明功能实现、测试情况
- 标签：`enhancement`, `planet`, `ocr`

#### 5. 代码审查与合并
```bash
# 审查通过后合并到develop
git checkout develop
git merge feature/planet-ocr-recognition
git push origin develop
```

#### 6. 发布到生产
```bash
# 从develop创建release分支
git checkout -b release/v2.1.0 develop

# 测试通过后合并到main
git checkout main
git merge release/v2.1.0
git tag -a v2.1.0 -m "版本2.1.0: 知识星球OCR识别与权限管理"
git push origin main --tags

# 同步回develop
git checkout develop
git merge release/v2.1.0
git push origin develop
```

### 重要文件保护

#### .gitignore更新
```bash
# 百度OCR配置（敏感信息）
.env
*.env.local

# OCR临时文件
uploads/screenshots/temp_*

# 数据库备份
*.db.backup
*.db.bak
```

#### 敏感信息管理
- ✅ 使用环境变量存储API密钥
- ✅ 不提交 `.env` 文件
- ✅ 提供 `.env.example` 模板
- ✅ 在README中说明配置步骤

---

## 📊 项目里程碑

| 里程碑 | 交付内容 | 预计时间 | 状态 |
|--------|---------|---------|------|
| M1: 数据库迁移 | 数据库表结构扩展完成 | Day 1 | ⏳ 待开始 |
| M2: OCR集成 | OCR识别功能可用 | Day 2 | ⏳ 待开始 |
| M3: 申请流程优化 | 新申请流程上线 | Day 4 | ⏳ 待开始 |
| M4: 定时任务 | 到期检查与邮件提醒 | Day 5 | ⏳ 待开始 |
| M5: 测试与优化 | 功能测试通过 | Day 6 | ⏳ 待开始 |
| M6: 生产部署 | 功能正式上线 | Day 7 | ⏳ 待开始 |

---

## 🧪 测试清单

### 功能测试

#### OCR识别测试
- [ ] 识别标准格式日期：`2026/7/16`
- [ ] 识别中文格式日期：`2026年7月16日`
- [ ] 识别红框文本：`截至权限到期至2026/7/16`
- [ ] 识别永久会员标识
- [ ] 处理模糊图片
- [ ] 处理倾斜图片
- [ ] 处理截图缺失到期时间

#### 申请流程测试
- [ ] 上传截图并触发OCR
- [ ] 显示识别结果
- [ ] 用户确认识别结果
- [ ] 用户手动修改日期
- [ ] 提交申请成功
- [ ] 管理员收到通知

#### 权限管理测试
- [ ] 审核通过自动设置到期时间
- [ ] 永久会员标记正确
- [ ] 定时任务检测到期用户
- [ ] 自动撤销过期权限
- [ ] 发送到期提醒邮件
- [ ] 发送已到期邮件

#### 边界情况测试
- [ ] 无到期时间的截图
- [ ] OCR识别失败
- [ ] 用户未确认直接提交
- [ ] 管理员手动修改到期时间
- [ ] 同一用户多次申请
- [ ] 到期日期为过去时间

---

## 🔍 监控与日志

### 关键指标监控

1. **OCR识别成功率**
   - 目标：>95%
   - 监控点：`ocr_service.py`

2. **到期检查任务执行**
   - 监控定时任务是否正常运行
   - 记录每次撤销的用户数量

3. **邮件发送成功率**
   - 监控提醒邮件发送状态
   - 记录失败案例

### 日志记录

#### 关键日志点
```python
# OCR识别
logger.info(f"OCR识别成功: 用户{user_id}, 到期时间{expiry_date}, 置信度{confidence}")
logger.error(f"OCR识别失败: 用户{user_id}, 错误{error}")

# 权限撤销
logger.info(f"撤销过期权限: 用户{user_id}, 到期时间{expiry_date}")

# 邮件发送
logger.info(f"发送到期提醒: 用户{user_id}, 剩余{days}天")
logger.error(f"邮件发送失败: 用户{user_id}, 错误{error}")
```

---

## 📚 附录

### A. 智谱AI GLM-4V API申请指南

1. 访问智谱AI开放平台：https://bigmodel.cn/
2. 注册/登录账号
3. 进入控制台 → API密钥管理
4. 创建API Key，获取：
   - API_KEY
5. 选择模型：glm-4v-flash（快速视觉理解版本）
6. 注：免费额度和计费详情请查看官方文档

### B. APScheduler使用参考

**触发器类型**：
- `cron`: 定时任务（如每天10点）
- `interval`: 间隔任务（如每小时）
- `date`: 一次性任务

**示例**：
```python
# 每天10点
scheduler.add_job(func, trigger='cron', hour=10, minute=0)

# 每小时
scheduler.add_job(func, trigger='interval', hours=1)

# 2026年1月26日16点30分
scheduler.add_job(func, trigger='date', run_date='2026-01-26 16:30:00')
```

### C. 常见问题FAQ

**Q1: OCR识别不准确怎么办？**
A: 用户可以手动修改识别结果，管理员审核时也可以调整。置信度低于0.8时建议人工确认。

**Q2: 永久会员如何处理？**
A: `planet_expiry_date` 字段设置为 `NULL`，定时任务会自动跳过 `NULL` 值的用户。

**Q3: 定时任务服务器重启后会丢失吗？**
A: APScheduler支持持久化，建议配置数据库存储。或使用系统cron作为备份。

**Q4: 邮件发送失败怎么办？**
A: 邮件发送采用异步机制，失败会记录日志。可配置重试机制或手动补发。

---

## ✅ 验收标准

### 功能完整性
- [x] OCR自动识别到期时间
- [x] 支持用户确认/修改识别结果
- [x] 管理员审核时自动设置到期时间
- [x] 定时检查并撤销过期权限
- [x] 到期前7/1天发送提醒邮件
- [x] 到期后发送通知邮件
- [x] 永久会员正确标记

### 性能要求
- OCR识别速度：< 3秒
- 识别准确率：> 95%
- 定时任务准时执行：误差 < 5分钟
- 邮件发送延迟：< 10秒

### 用户体验
- 申请流程流畅，用户理解成本低
- 识别结果清晰展示
- 邮件模板美观专业
- 示例图片引导明确

---

## 📞 联系方式

**技术支持**：开发团队
**文档维护**：产品团队
**最后更新**：2026-01-26

---

## 📊 补充功能：数据统计分析

### 功能概述
为管理员提供知识星球会员的数据统计和分析功能，帮助了解用户购买习惯、续期趋势和权限到期预测。

### 核心统计指标与实现
 
#### 1. 会员时长分布统计
- 统计各时长段用户（1月/3月/6月/12月/永久）。
- 计算平均会员时长和最受欢迎套餐。
- **实现方案**: 聚合查询 `User` 表的 `planet_membership_duration` 字段。

#### 2. 续期率分析
- 统计"首次申请"与"续期用户"比例。
- **实现方案**: 统计 `PlanetApplication` 表中同一 `user_id` 的成功申请次数。

#### 3. 到期预测
- 预测未来30天即将到期的用户量趋势。
- **实现方案**: 筛选 `User.planet_expiry_date` 在 `[now, now+30d]` 范围内的记录。

#### 4. 数据导出
- 支持将会员名单及到期信息导出为CSV。
- 字段包含：用户名、邮箱、会员时长、到期时间、审核时间。

---

**文档结束**
