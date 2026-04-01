#!/bin/bash

echo "===================================================="
echo "Flask-Mail 安装脚本"
echo "===================================================="

# 尝试不同的Python命令
PYTHON_CMD=""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 未找到Python解释器"
    exit 1
fi

echo "✅ 使用Python解释器: $PYTHON_CMD"

# 尝试不同的pip安装方法
echo "📦 开始安装Flask-Mail..."

if $PYTHON_CMD -m pip install Flask-Mail==0.9.1; then
    echo "✅ Flask-Mail安装成功！"
elif pip3 install Flask-Mail==0.9.1; then
    echo "✅ Flask-Mail安装成功！"
elif pip install Flask-Mail==0.9.1; then
    echo "✅ Flask-Mail安装成功！"
else
    echo "❌ Flask-Mail安装失败"
    echo "请手动运行以下命令之一："
    echo "  python3 -m pip install Flask-Mail==0.9.1"
    echo "  pip3 install Flask-Mail==0.9.1"
    echo "  pip install Flask-Mail==0.9.1"
    exit 1
fi

# 验证安装
echo "🔍 验证安装..."
if $PYTHON_CMD -c "import flask_mail; print('Flask-Mail版本:', flask_mail.__version__)" 2>/dev/null; then
    echo "✅ Flask-Mail验证成功！"
else
    echo "❌ Flask-Mail验证失败"
    exit 1
fi

echo "===================================================="
echo "🎉 安装完成！"
echo "现在请重启你的应用："
echo "  python3 run_enhanced.py"
echo "===================================================="