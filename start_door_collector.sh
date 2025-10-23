#!/bin/bash
# 门禁数据采集器启动脚本

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量
if [ -f "door_access.env" ]; then
    echo "加载门禁数据采集器环境配置..."
    export $(grep -v '^#' door_access.env | xargs)
else
    echo "警告: 未找到 door_access.env 配置文件，使用默认配置"
fi

# 检查Python脚本是否存在
if [ ! -f "door_access_collector.py" ]; then
    echo "错误: 未找到 door_access_collector.py 脚本"
    exit 1
fi

# 检查是否已经在运行
if [ -f "door_access_collector.pid" ]; then
    PID=$(cat door_access_collector.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "门禁数据采集器已在运行 (PID: $PID)"
        echo "如需重启，请先运行: ./stop_door_collector.sh"
        exit 1
    else
        echo "清理旧的PID文件"
        rm -f door_access_collector.pid
    fi
fi

# 启动门禁数据采集器
echo "启动门禁数据采集器..."
echo "数据库: ${DOOR_MONGO_DB:-door_access}"
echo "采集间隔: ${DOOR_INTERVAL_HOURS:-1}小时"
echo "日志文件: ${DOOR_LOG_FILE:-door_access.log}"

nohup python3 door_access_collector.py > door_access_boost.out 2>&1 & 
echo $! > door_access_collector.pid

echo "门禁数据采集器已启动 (PID: $(cat door_access_collector.pid))"
echo "查看日志: tail -f door_access.log"
echo "查看输出: tail -f door_access_boost.out"
