import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import hashlib
from timezone_utils import get_timestamp_filename

# 创建图片上传蓝图
image_upload_bp = Blueprint('image_upload', __name__)

# 允许的图片扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 最大文件大小 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

def allowed_file(filename):
    """检查文件扩展名是否被允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_hash(file_content):
    """获取文件内容的MD5哈希值，用于去重"""
    return hashlib.md5(file_content).hexdigest()

def create_unique_filename(original_filename, file_content):
    """创建唯一的文件名"""
    # 获取文件扩展名
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    
    # 使用文件内容哈希值和时间戳创建唯一文件名
    file_hash = get_file_hash(file_content)
    timestamp = get_timestamp_filename().rstrip('_')
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{timestamp}_{file_hash[:8]}_{unique_id}.{ext}"

def optimize_image(image_path, max_width=1200, max_height=1200, quality=85):
    """优化图片大小和质量"""
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式（如果需要）
            if img.mode in ('RGBA', 'LA'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 调整大小（保持宽高比）
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # 保存优化后的图片
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            
        return True
    except Exception as e:
        print(f"图片优化失败: {e}")
        return False

@image_upload_bp.route('/api/upload-image', methods=['POST'])
def upload_image():
    """处理图片上传请求"""
    try:
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        file = request.files['image']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '不支持的文件格式'}), 400
        
        # 读取文件内容
        file_content = file.read()
        
        # 检查文件大小
        if len(file_content) > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': '文件过大，最大支持5MB'}), 400
        
        # 重置文件指针
        file.seek(0)
        
        # 确保上传目录存在
        upload_dir = os.path.join(current_app.root_path, 'static', 'images', 'datasets')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 创建唯一文件名
        filename = create_unique_filename(file.filename, file_content)
        file_path = os.path.join(upload_dir, filename)
        
        # 保存文件
        file.save(file_path)
        
        # 优化图片
        if optimize_image(file_path):
            print(f"图片已优化: {filename}")
        
        # 生成访问URL（相对路径）
        image_url = f"/static/images/datasets/{filename}"
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': image_url,
            'message': '图片上传成功'
        })
        
    except Exception as e:
        print(f"图片上传错误: {e}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@image_upload_bp.route('/api/delete-image', methods=['DELETE'])
def delete_image():
    """删除已上传的图片"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'success': False, 'error': '缺少文件名'}), 400
        
        filename = data['filename']
        
        # 验证文件名安全性
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': '非法文件名'}), 400
        
        # 构建文件路径
        file_path = os.path.join(current_app.root_path, 'static', 'images', 'datasets', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 删除文件
        os.remove(file_path)
        
        return jsonify({'success': True, 'message': '文件删除成功'})
        
    except Exception as e:
        print(f"图片删除错误: {e}")
        return jsonify({'success': False, 'error': '删除失败'}), 500

@image_upload_bp.route('/api/images/info', methods=['GET'])
def get_image_info():
    """获取图片信息"""
    try:
        filename = request.args.get('filename')
        if not filename:
            return jsonify({'success': False, 'error': '缺少文件名'}), 400
        
        # 验证文件名安全性
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': '非法文件名'}), 400
        
        # 构建文件路径
        file_path = os.path.join(current_app.root_path, 'static', 'images', 'datasets', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 获取文件信息
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        created_time = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
        
        # 尝试获取图片尺寸
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
        except:
            width = height = 0
            format_name = 'Unknown'
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': file_size,
            'width': width,
            'height': height,
            'format': format_name,
            'created_time': created_time,
            'url': f"/static/images/datasets/{filename}"
        })
        
    except Exception as e:
        print(f"获取图片信息错误: {e}")
        return jsonify({'success': False, 'error': '获取信息失败'}), 500