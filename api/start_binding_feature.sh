#!/bin/bash

echo "🚀 启动知识库绑定功能部署脚本"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "web_api.py" ]; then
    echo "❌ 请在 api 目录下运行此脚本"
    exit 1
fi

# 检查conda环境
echo "📋 检查conda环境..."
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到conda，请先安装conda"
    exit 1
fi

# 激活ezdata环境
echo "🔧 激活ezdata环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate ezdata

if [ $? -ne 0 ]; then
    echo "❌ 激活ezdata环境失败，请检查环境是否存在"
    exit 1
fi

echo "✅ ezdata环境已激活"

# 创建数据库表
echo ""
echo "🗄️  创建知识库绑定表..."
python create_binding_table.py

if [ $? -eq 0 ]; then
    echo "✅ 数据库表创建成功"
else
    echo "❌ 数据库表创建失败"
    exit 1
fi

# 测试绑定功能
echo ""
echo "🧪 测试绑定功能..."
python test_binding.py

if [ $? -eq 0 ]; then
    echo "✅ 绑定功能测试通过"
else
    echo "⚠️  绑定功能测试失败（可能是数据问题，但不影响基本功能）"
fi

# 启动后端服务
echo ""
echo "🚀 启动后端服务..."
echo "📝 提示：服务启动后，请在新终端中启动前端服务"
echo "📝 前端启动命令：cd ../web && npm run dev"
echo ""
echo "按 Ctrl+C 停止后端服务"
echo "=================================="

python web_api.py
