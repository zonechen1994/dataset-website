/**
 * 智能未读通知管理
 * 自动更新未读通知数量，提供更好的用户体验
 */

class NotificationManager {
    constructor() {
        this.updateInterval = 30000; // 30秒更新一次
        this.autoUpdateTimer = null;
        this.init();
    }
    
    init() {
        // 页面加载后立即更新一次计数
        this.updateUnreadCount();
        
        // 开启自动更新
        this.startAutoUpdate();
        
        // 页面隐藏时停止更新，显示时恢复
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoUpdate();
            } else {
                this.startAutoUpdate();
                this.updateUnreadCount(); // 重新显示时立即更新
            }
        });
    }
    
    /**
     * 更新未读通知数量
     */
    async updateUnreadCount() {
        try {
            const response = await fetch('/planet/api/notifications/unread-count');
            if (response.ok) {
                const data = await response.json();
                this.updateUnreadBadges(data.count);
            }
        } catch (error) {
            console.warn('更新未读通知数量失败:', error);
        }
    }
    
    /**
     * 更新页面上的未读徽章
     */
    updateUnreadBadges(count) {
        // 更新所有的未读计数徽章
        const badges = document.querySelectorAll('.unread-count-badge, [data-unread-count]');
        badges.forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline';
                badge.classList.remove('d-none');
            } else {
                badge.style.display = 'none';
                badge.classList.add('d-none');
            }
        });
        
        // 更新导航栏中的未读徽章
        const navBadges = document.querySelectorAll('.badge.bg-danger');
        navBadges.forEach(badge => {
            if (badge.textContent.match(/^\d+$/)) { // 只更新数字徽章
                if (count > 0) {
                    badge.textContent = count;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        });
        
        // 更新页面标题中的计数（如果存在）
        this.updatePageTitle(count);
    }
    
    /**
     * 更新页面标题中的未读计数
     */
    updatePageTitle(count) {
        const title = document.title;
        const baseTitle = title.replace(/^\(\d+\)\s*/, ''); // 移除现有的计数
        
        if (count > 0) {
            document.title = `(${count}) ${baseTitle}`;
        } else {
            document.title = baseTitle;
        }
    }
    
    /**
     * 开始自动更新
     */
    startAutoUpdate() {
        if (this.autoUpdateTimer) {
            clearInterval(this.autoUpdateTimer);
        }
        
        this.autoUpdateTimer = setInterval(() => {
            this.updateUnreadCount();
        }, this.updateInterval);
    }
    
    /**
     * 停止自动更新
     */
    stopAutoUpdate() {
        if (this.autoUpdateTimer) {
            clearInterval(this.autoUpdateTimer);
            this.autoUpdateTimer = null;
        }
    }
    
    /**
     * 手动触发更新（在执行操作后调用）
     */
    forceUpdate() {
        this.updateUnreadCount();
    }
    
    /**
     * 标记特定通知为已读
     */
    async markNotificationRead(notificationId) {
        try {
            const response = await fetch(`/planet/api/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                // 标记成功后立即更新计数
                setTimeout(() => this.updateUnreadCount(), 500);
                return true;
            }
        } catch (error) {
            console.warn('标记通知已读失败:', error);
        }
        return false;
    }
    
    /**
     * 批量标记所有通知为已读
     */
    async markAllRead() {
        try {
            const response = await fetch('/planet/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                // 立即更新计数为0
                this.updateUnreadBadges(0);
                return data.count;
            }
        } catch (error) {
            console.warn('批量标记已读失败:', error);
        }
        return 0;
    }
}

// 页面特定的智能标记功能
class PageSpecificAutoRead {
    constructor(notificationManager) {
        this.notificationManager = notificationManager;
        this.init();
    }
    
    init() {
        // 检测当前页面类型并应用相应的自动标记逻辑
        const currentPath = window.location.pathname;
        
        if (currentPath.includes('/planet/admin/applications')) {
            this.handleApplicationPages();
        } 
        // 暂时禁用通知消息页面处理，避免与权限申请功能重复
        // else if (currentPath.includes('/planet/admin/notifications')) {
        //     this.handleNotificationPage();
        // }
    }
    
    /**
     * 处理申请管理页面的自动标记
     */
    handleApplicationPages() {
        // 页面加载后延迟标记相关通知为已读
        setTimeout(() => {
            this.notificationManager.forceUpdate();
        }, 1000);
        
        // 监听申请操作（审核通过/拒绝）
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="approve"], [data-action="reject"]') ||
                e.target.closest('[data-action="approve"], [data-action="reject"]')) {
                // 操作完成后更新计数
                setTimeout(() => {
                    this.notificationManager.forceUpdate();
                }, 1500);
            }
        });
        
        // 监听AJAX成功响应
        this.interceptAjaxSuccess();
    }
    
    /**
     * 处理通知页面的自动标记
     */
    handleNotificationPage() {
        // 监听通知点击事件
        document.addEventListener('click', (e) => {
            const notificationItem = e.target.closest('[data-notification-id]');
            if (notificationItem) {
                const notificationId = notificationItem.dataset.notificationId;
                const isUnread = notificationItem.classList.contains('unread');
                
                if (isUnread) {
                    // 自动标记为已读
                    this.notificationManager.markNotificationRead(notificationId);
                    
                    // 立即更新UI
                    notificationItem.classList.remove('unread');
                    notificationItem.style.opacity = '0.8';
                }
            }
        });
    }
    
    /**
     * 拦截AJAX成功响应来触发更新
     */
    interceptAjaxSuccess() {
        // 拦截原生fetch
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const response = await originalFetch(...args);
            
            if (response.ok && args[0].includes('review')) {
                // 如果是审核操作，延迟更新计数
                setTimeout(() => {
                    this.notificationManager.forceUpdate();
                }, 1000);
            }
            
            return response;
        };
        
        // 拦截jQuery AJAX（如果使用）
        if (window.jQuery) {
            const originalAjax = jQuery.ajax;
            jQuery.ajax = function(options) {
                const originalSuccess = options.success;
                options.success = function(data, textStatus, jqXHR) {
                    if (originalSuccess) {
                        originalSuccess.apply(this, arguments);
                    }
                    // 如果是申请相关的操作，更新计数
                    if (options.url && options.url.includes('applications')) {
                        setTimeout(() => {
                            window.notificationManager?.forceUpdate();
                        }, 1000);
                    }
                };
                return originalAjax.call(this, options);
            };
        }
    }
}

// 初始化管理器
document.addEventListener('DOMContentLoaded', () => {
    // 创建全局通知管理器
    window.notificationManager = new NotificationManager();
    
    // 创建页面特定的自动标记功能
    window.pageSpecificAutoRead = new PageSpecificAutoRead(window.notificationManager);
    
    console.log('智能未读通知管理已启用');
});