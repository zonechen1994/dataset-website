#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
退出登录问题调试工具
用于诊断线上环境退出登录异常的问题
"""

from flask import Flask, request, session, make_response
import os

def create_debug_app():
    app = Flask(__name__)
    app.secret_key = 'debug-key'
    
    @app.route('/debug/session')
    def debug_session():
        """调试session信息"""
        info = {
            'session_data': dict(session),
            'session_id': session.get('_id', 'No session ID'),
            'cookies': dict(request.cookies),
            'headers': dict(request.headers),
            'environment': {
                'FLASK_ENV': os.environ.get('FLASK_ENV', 'not set'),
                'DEBUG': app.debug,
                'SESSION_COOKIE_SECURE': app.config.get('SESSION_COOKIE_SECURE', 'not set'),
                'SESSION_COOKIE_HTTPONLY': app.config.get('SESSION_COOKIE_HTTPONLY', 'not set'),
                'SESSION_COOKIE_SAMESITE': app.config.get('SESSION_COOKIE_SAMESITE', 'not set'),
            }
        }
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Session Debug Info</title>
            <style>
                body { font-family: monospace; margin: 20px; }
                .section { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }
                pre { background: #f5f5f5; padding: 10px; overflow: auto; }
                .error { color: red; }
                .success { color: green; }
            </style>
        </head>
        <body>
            <h1>Session Debug Information</h1>
            
            <div class="section">
                <h2>Session Data</h2>
                <pre>{session_data}</pre>
            </div>
            
            <div class="section">
                <h2>Cookies</h2>
                <pre>{cookies}</pre>
            </div>
            
            <div class="section">
                <h2>Environment Settings</h2>
                <pre>{environment}</pre>
            </div>
            
            <div class="section">
                <h2>Request Headers</h2>
                <pre>{headers}</pre>
            </div>
            
            <div class="section">
                <h2>Logout Test</h2>
                <p>Current session has data: <span class="{status_class}">{has_session}</span></p>
                <a href="/debug/test_logout">Test Logout</a> | 
                <a href="/debug/test_login">Test Login</a>
            </div>
        </body>
        </html>
        """.format(
            session_data=str(info['session_data']),
            cookies=str(info['cookies']),
            environment=str(info['environment']),
            headers=str(dict(info['headers'])),
            has_session='Yes' if info['session_data'] else 'No',
            status_class='success' if info['session_data'] else 'error'
        )
        
        return html
    
    @app.route('/debug/test_login')
    def test_login():
        """测试登录"""
        session['user_id'] = 'test_user'
        session['username'] = 'test'
        session['is_admin'] = False
        return """
        <h1>Test Login Successful</h1>
        <p>Session data has been set.</p>
        <a href="/debug/session">Check Session</a> | 
        <a href="/debug/test_logout">Test Logout</a>
        """
    
    @app.route('/debug/test_logout')
    def test_logout():
        """测试退出登录"""
        # 保存退出前的session数据
        before_logout = dict(session)
        
        # 执行退出逻辑
        session.clear()
        
        # 创建响应并清除cookie
        response = make_response(f"""
        <h1>Test Logout</h1>
        <h2>Before Logout:</h2>
        <pre>{before_logout}</pre>
        <h2>After Logout:</h2>
        <pre>{dict(session)}</pre>
        <p>Session should be empty now.</p>
        <a href="/debug/session">Check Session</a> | 
        <a href="/debug/test_login">Test Login Again</a>
        """)
        
        # 清除所有可能的cookie
        for cookie_name in ['session', 'remember_token', 'user_session']:
            response.set_cookie(
                cookie_name, 
                '', 
                expires=0,
                secure=app.config.get('SESSION_COOKIE_SECURE', False),
                httponly=True,
                samesite='Lax'
            )
        
        # 添加no-cache头
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    
    return app

if __name__ == '__main__':
    print("启动退出登录调试工具...")
    print("访问 http://localhost:5555/debug/session 开始调试")
    
    app = create_debug_app()
    app.run(host='0.0.0.0', port=5555, debug=True)