#!/bin/bash
# NextChat 启动脚本

echo "启动 NextChat 服务..."

# 加载环境变量
if [ -f "nextchat.env" ]; then
    echo "加载环境变量..."
    export $(cat nextchat.env | grep -v '^#' | xargs)
fi

# 设置环境变量
export NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL:-"http://1118qg49520ma.vicp.fun"}
export NEXT_PUBLIC_API_KEY=${NEXT_PUBLIC_API_KEY:-"your-trustrag-api-key"}
export NEXT_PUBLIC_MODEL_NAME=${NEXT_PUBLIC_MODEL_NAME:-"trustrag"}
export NEXT_PUBLIC_TITLE=${NEXT_PUBLIC_TITLE:-"数字金融实验室"}
export NEXT_PUBLIC_DESCRIPTION=${NEXT_PUBLIC_DESCRIPTION:-"基于 TrustRAG 的智能问答系统"}

# TrustRAG 配置
export TRUSTRAG_BASE_URL=${TRUSTRAG_BASE_URL:-"http://1118qg49520ma.vicp.fun"}
export TRUSTRAG_PORT=${TRUSTRAG_PORT:-"8217"}
export TRUSTRAG_NAMESPACE=${TRUSTRAG_NAMESPACE:-"ezdata-1"}
export EZDATA_SECRET_KEY=${EZDATA_SECRET_KEY:-"erwqefdscweer)qi"}

# 检查依赖
echo "检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "错误: 未找到 npm，请先安装 npm"
    exit 1
fi

# 检查 NextChat 目录
if [ ! -d "nextchat" ]; then
    echo "创建 NextChat 目录..."
    mkdir -p nextchat
    cd nextchat
    
    echo "克隆 NextChat 项目..."
    git clone https://github.com/ChatGPTNextWeb/NextChat.git .
    
    echo "安装依赖..."
    npm install
    
    echo "构建项目..."
    npm run build
else
    echo "进入 NextChat 目录..."
    cd nextchat
fi

# 启动服务
echo "启动 NextChat 服务..."
echo "服务地址: http://localhost:3000"
echo "代理地址: http://1118qg49520ma.vicp.fun/nextchat"

npm start
