// 主要JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 卡片悬停效果增强
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // 搜索框实时搜索功能
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const searchTerm = this.value.trim();
            
            if (searchTerm.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performLiveSearch(searchTerm);
                }, 500);
            }
        });
    }

    // 筛选表单自动提交
    const filterSelects = document.querySelectorAll('.filters-section select');
    filterSelects.forEach(select => {
        let changeTimeout;
        select.addEventListener('change', function() {
            clearTimeout(changeTimeout);
            changeTimeout = setTimeout(() => {
                // 添加加载状态
                showLoadingState();
                // 提交表单
                this.closest('form').submit();
            }, 300);
        });
    });

    // 删除确认对话框
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const datasetName = this.getAttribute('data-dataset-name');
            if (confirm(`确定要删除数据集 "${datasetName}" 吗？此操作不可撤销。`)) {
                // 添加加载状态
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 删除中...';
                this.disabled = true;
                
                // 提交删除表单
                const form = this.closest('form');
                if (form) {
                    form.submit();
                }
            }
        });
    });

    // 文件上传预览
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const fileInfo = document.getElementById('file-info');
                if (fileInfo) {
                    fileInfo.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-file-text"></i>
                            已选择文件: <strong>${file.name}</strong> (${formatFileSize(file.size)})
                        </div>
                    `;
                }
                
                // 如果是markdown文件，尝试预览内容
                if (file.name.endsWith('.md')) {
                    previewMarkdownFile(file);
                }
            }
        });
    }

    // 表单验证增强
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
                submitButton.disabled = true;
                
                // 如果表单验证失败，恢复按钮状态
                setTimeout(() => {
                    if (!form.checkValidity()) {
                        submitButton.innerHTML = originalText;
                        submitButton.disabled = false;
                    }
                }, 100);
            }
        });
    });

    // 添加淡入动画到卡片
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // 返回顶部按钮
    createBackToTopButton();
    
    // 响应式导航栏处理
    handleResponsiveNavbar();
    
    // 管理后台侧边栏功能
    initAdminSidebar();
});

// 实时搜索功能
function performLiveSearch(searchTerm) {
    // 这里可以实现AJAX搜索，现在先简单处理
    console.log('搜索:', searchTerm);
    
    // 高亮搜索结果
    highlightSearchResults(searchTerm);
}

// 高亮搜索结果
function highlightSearchResults(searchTerm) {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        const title = card.querySelector('.card-title a');
        const description = card.querySelector('.card-text');
        
        if (title || description) {
            const titleText = title ? title.textContent.toLowerCase() : '';
            const descText = description ? description.textContent.toLowerCase() : '';
            const term = searchTerm.toLowerCase();
            
            if (titleText.includes(term) || descText.includes(term)) {
                card.style.opacity = '1';
                card.style.transform = 'scale(1)';
            } else {
                card.style.opacity = '0.6';
                card.style.transform = 'scale(0.95)';
            }
        }
    });
}

// 显示加载状态
function showLoadingState() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="loading-spinner">
            <div class="loading"></div>
            <p>加载中...</p>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
    
    // 3秒后自动移除加载状态（防止卡住）
    setTimeout(() => {
        if (document.body.contains(loadingOverlay)) {
            document.body.removeChild(loadingOverlay);
        }
    }, 3000);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 预览Markdown文件
function previewMarkdownFile(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        const preview = document.getElementById('file-preview');
        if (preview) {
            // 简单的markdown预览
            const lines = content.split('\n').slice(0, 10);
            preview.innerHTML = `
                <div class="card mt-3">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-eye"></i> 文件预览</h6>
                    </div>
                    <div class="card-body">
                        <pre style="max-height: 200px; overflow-y: auto;">${lines.join('\n')}</pre>
                        ${content.split('\n').length > 10 ? '<small class="text-muted">... 还有更多内容</small>' : ''}
                    </div>
                </div>
            `;
        }
    };
    reader.readAsText(file, 'UTF-8');
}

// 创建返回顶部按钮
function createBackToTopButton() {
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopButton.className = 'btn btn-primary back-to-top';
    backToTopButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: none;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(backToTopButton);
    
    // 滚动事件监听
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
    
    // 点击返回顶部
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// 响应式导航栏处理
function handleResponsiveNavbar() {
    const navbar = document.querySelector('.navbar-collapse');
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    if (navbar && navbarToggler) {
        // 点击导航链接时自动收起菜单
        const navLinks = navbar.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 992) {
                    navbar.classList.remove('show');
                }
            });
        });
    }
}

// 工具函数：显示toast消息
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // 自动清理
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// 创建toast容器
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// 复制到剪贴板功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('已复制到剪贴板', 'success');
    });
}

// 键盘快捷键支持
document.addEventListener('keydown', function(e) {
    // Ctrl+K 或 Cmd+K 聚焦搜索框
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // ESC 清空搜索
    if (e.key === 'Escape') {
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput && searchInput === document.activeElement) {
            searchInput.value = '';
            searchInput.blur();
        }
    }
});

// 管理后台侧边栏初始化
function initAdminSidebar() {
    // 只在管理页面执行
    if (!window.location.pathname.includes('/admin/') && 
        !window.location.pathname.includes('/user_admin/') && 
        !window.location.pathname.includes('/planet/admin/')) {
        return;
    }
    
    // 高亮当前页面菜单项
    highlightActiveSidebarMenuItem();
    
    // 添加菜单项交互效果
    addSidebarMenuItemEffects();
}

// 高亮当前激活的菜单项（管理后台）
function highlightActiveSidebarMenuItem() {
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.admin-sidebar-card .list-group-item-action[href]');
    
    // 首先移除所有active类
    menuItems.forEach(item => item.classList.remove('active'));
    
    // 匹配规则 - 精确匹配路由
    const matchRules = [
        { pattern: '/admin', selector: 'a[href$="/admin"]', exact: true },
        { pattern: '/admin/categories', selector: 'a[href*="/admin/categories"]' },
        { pattern: '/admin/modalities', selector: 'a[href*="/admin/modalities"]' },
        { pattern: '/admin/task-types', selector: 'a[href*="/admin/task-types"]' },
        { pattern: '/user_admin/', selector: 'a[href*="/user_admin/"]' },
        { pattern: '/planet/admin/applications', selector: 'a[href*="/planet/admin/applications"]' },
        { pattern: '/planet/admin/notifications', selector: 'a[href*="/planet/admin/notifications"]' }
    ];
    
    // 尝试匹配规则
    for (const rule of matchRules) {
        const matches = rule.exact ? 
            currentPath === rule.pattern : 
            currentPath.includes(rule.pattern);
            
        if (matches) {
            const targetItem = document.querySelector(rule.selector);
            if (targetItem) {
                targetItem.classList.add('active');
                return;
            }
        }
    }
    
    // 回退到简单匹配
    menuItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && (currentPath === href || (href.length > 1 && currentPath.includes(href)))) {
            item.classList.add('active');
        }
    });
}

// 添加侧边栏菜单项交互效果
function addSidebarMenuItemEffects() {
    const menuItems = document.querySelectorAll('.admin-sidebar-card .list-group-item-action[href]');
    
    menuItems.forEach(item => {
        // 鼠标悬停效果
        item.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active')) {
                this.style.transform = 'translateX(3px)';
                this.style.borderLeft = '3px solid #dee2e6';
            }
        });
        
        item.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.transform = 'translateX(0)';
                this.style.borderLeft = 'none';
            }
        });
    });
}

