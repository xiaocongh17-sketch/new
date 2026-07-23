#!/bin/bash
# AI Store Copilot - 阿里云部署脚本
# 在宝塔面板的「终端」中运行此脚本

set -e
echo "===== AI Store Copilot 部署开始 ====="

# 1. 安装 Docker（如果没装）
if ! command -v docker &> /dev/null; then
    echo "[1/5] 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
else
    echo "[1/5] Docker 已安装 ✓"
fi

# 2. 安装 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[2/5] 安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "[2/5] Docker Compose 已安装 ✓"
fi

# 3. 配置环境变量
echo "[3/5] 配置环境变量..."
cd /opt/ai-store-copilot
if [ ! -f .env ]; then
    cp .env.example .env
    echo "请编辑 .env 文件填入你的 DeepSeek API Key"
fi

# 4. 启动服务
echo "[4/5] 启动服务..."
docker-compose -f docker/docker-compose.prod.yml up -d --build

# 5. 检查状态
echo "[5/5] 检查服务状态..."
sleep 10
docker-compose -f docker/docker-compose.prod.yml ps

echo ""
echo "===== 部署完成 ====="
echo "前端: http://$(curl -s ifconfig.me):3003"
echo "后端: http://$(curl -s ifconfig.me):8000"
echo "API文档: http://$(curl -s ifconfig.me):8000/api/docs"
