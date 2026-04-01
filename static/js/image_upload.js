/**
 * 图片拖放上传组件
 * 支持拖放、点击上传、预览、删除功能
 */

class ImageUploader {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            maxFiles: options.maxFiles || 10,
            maxFileSize: options.maxFileSize || 5 * 1024 * 1024, // 5MB
            allowedTypes: options.allowedTypes || ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
            uploadUrl: options.uploadUrl || '/api/upload-image',
            onUploadSuccess: options.onUploadSuccess || null,
            onUploadError: options.onUploadError || null,
            ...options
        };
        
        this.uploadedImages = [];
        this.init();
    }
    
    init() {
        this.createUploadArea();
        this.setupEventListeners();
        
        // 如果有初始图片，显示它们
        if (this.options.initialImages) {
            this.displayInitialImages(this.options.initialImages);
        }
    }
    
    createUploadArea() {
        this.container.innerHTML = `
            <div class="image-upload-container">
                <div class="drag-drop-area" id="${this.container.id}-drop-area">
                    <div class="upload-content">
                        <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">拖放图片到这里或点击上传</h5>
                        <p class="text-muted small">
                            支持 JPG、PNG、GIF、WebP 格式，单个文件最大 ${this.formatFileSize(this.options.maxFileSize)}
                        </p>
                        <button type="button" class="btn btn-outline-primary btn-sm" id="${this.container.id}-browse-btn">
                            <i class="fas fa-folder-open"></i> 选择文件
                        </button>
                    </div>
                    <input type="file" id="${this.container.id}-file-input" 
                           multiple accept="image/*" style="display: none;">
                </div>
                
                <div class="uploaded-images mt-3" id="${this.container.id}-images" style="display: none;">
                    <h6 class="mb-2">已上传的图片</h6>
                    <div class="row" id="${this.container.id}-image-list"></div>
                </div>
                
                <div class="upload-progress mt-2" id="${this.container.id}-progress" style="display: none;">
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            
            <style>
                .image-upload-container {
                    width: 100%;
                }
                
                .drag-drop-area {
                    border: 2px dashed #dee2e6;
                    border-radius: 8px;
                    padding: 40px;
                    text-align: center;
                    background-color: #f8f9fa;
                    transition: all 0.3s ease;
                    cursor: pointer;
                }
                
                .drag-drop-area:hover {
                    border-color: #007bff;
                    background-color: rgba(0, 123, 255, 0.05);
                }
                
                .drag-drop-area.drag-over {
                    border-color: #007bff;
                    background-color: rgba(0, 123, 255, 0.1);
                    transform: scale(1.02);
                }
                
                .image-preview {
                    position: relative;
                    margin-bottom: 15px;
                }
                
                .image-preview img {
                    width: 100%;
                    height: 150px;
                    object-fit: cover;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                }
                
                .image-preview .remove-btn {
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    background: rgba(220, 53, 69, 0.9);
                    border: none;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    opacity: 0;
                    transition: opacity 0.3s;
                }
                
                .image-preview:hover .remove-btn {
                    opacity: 1;
                }
                
                .image-preview .image-info {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 5px 8px;
                    font-size: 12px;
                    border-radius: 0 0 8px 8px;
                    opacity: 0;
                    transition: opacity 0.3s;
                }
                
                .image-preview:hover .image-info {
                    opacity: 1;
                }
                
                .upload-progress {
                    margin-top: 10px;
                }
                
                .progress {
                    height: 6px;
                }
            </style>
        `;
    }
    
    setupEventListeners() {
        const dropArea = this.container.querySelector(`#${this.container.id}-drop-area`);
        const fileInput = this.container.querySelector(`#${this.container.id}-file-input`);
        const browseBtn = this.container.querySelector(`#${this.container.id}-browse-btn`);
        
        // 拖放事件
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add('drag-over'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove('drag-over'), false);
        });
        
        dropArea.addEventListener('drop', (e) => this.handleDrop(e), false);
        dropArea.addEventListener('click', () => fileInput.click());
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }
    
    handleFiles(files) {
        const validFiles = Array.from(files).filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            return;
        }
        
        if (this.uploadedImages.length + validFiles.length > this.options.maxFiles) {
            this.showError(`最多只能上传 ${this.options.maxFiles} 张图片`);
            return;
        }
        
        validFiles.forEach(file => this.uploadFile(file));
    }
    
    validateFile(file) {
        // 检查文件类型
        if (!this.options.allowedTypes.includes(file.type)) {
            this.showError(`不支持的文件类型: ${file.name}`);
            return false;
        }
        
        // 检查文件大小
        if (file.size > this.options.maxFileSize) {
            this.showError(`文件过大: ${file.name} (${this.formatFileSize(file.size)})`);
            return false;
        }
        
        return true;
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('type', 'dataset');
        
        const progressContainer = this.container.querySelector(`#${this.container.id}-progress`);
        const progressBar = progressContainer.querySelector('.progress-bar');
        
        try {
            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';
            
            const response = await fetch(this.options.uploadUrl, {
                method: 'POST',
                body: formData
            });
            
            progressBar.style.width = '100%';
            
            if (!response.ok) {
                throw new Error(`上传失败: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.addUploadedImage({
                    filename: result.filename,
                    url: result.url,
                    alt: file.name,
                    size: file.size
                });
                
                if (this.options.onUploadSuccess) {
                    this.options.onUploadSuccess(result);
                }
                
                this.showSuccess(`图片上传成功: ${file.name}`);
            } else {
                throw new Error(result.error || '上传失败');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError(`上传失败: ${error.message}`);
            
            if (this.options.onUploadError) {
                this.options.onUploadError(error);
            }
        } finally {
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 1000);
        }
    }
    
    addUploadedImage(imageData) {
        this.uploadedImages.push(imageData);
        this.updateImageDisplay();
        this.updateHiddenInput();
    }
    
    removeImage(index) {
        this.uploadedImages.splice(index, 1);
        this.updateImageDisplay();
        this.updateHiddenInput();
    }
    
    updateImageDisplay() {
        const imagesContainer = this.container.querySelector(`#${this.container.id}-images`);
        const imageList = this.container.querySelector(`#${this.container.id}-image-list`);
        
        if (this.uploadedImages.length === 0) {
            imagesContainer.style.display = 'none';
            return;
        }
        
        imagesContainer.style.display = 'block';
        
        imageList.innerHTML = this.uploadedImages.map((image, index) => `
            <div class="col-md-3 col-sm-6">
                <div class="image-preview">
                    <img src="${image.url}" alt="${image.alt}" loading="lazy">
                    <button type="button" class="remove-btn" onclick="imageUploader.removeImage(${index})" title="删除图片">
                        <i class="fas fa-times"></i>
                    </button>
                    <div class="image-info">
                        ${image.alt} (${this.formatFileSize(image.size)})
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    updateHiddenInput() {
        // 更新隐藏的输入字段，用于表单提交
        let hiddenInput = this.container.querySelector('input[name="uploaded_images"]');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'uploaded_images';
            this.container.appendChild(hiddenInput);
        }
        
        hiddenInput.value = JSON.stringify(this.uploadedImages.map(img => ({
            url: img.url,
            alt: img.alt || ''
        })));
    }
    
    displayInitialImages(images) {
        images.forEach(image => {
            this.uploadedImages.push({
                filename: image.url.split('/').pop(),
                url: image.url,
                alt: image.alt || '',
                size: 0 // 初始图片不知道大小
            });
        });
        this.updateImageDisplay();
        this.updateHiddenInput();
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type) {
        // 创建临时消息提示
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show mt-2`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        this.container.appendChild(alertDiv);
        
        // 3秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 3000);
    }
    
    // 获取已上传的图片列表
    getUploadedImages() {
        return this.uploadedImages;
    }
    
    // 清空所有图片
    clearImages() {
        this.uploadedImages = [];
        this.updateImageDisplay();
        this.updateHiddenInput();
    }
}

// 全局变量，供模板使用
let imageUploader;