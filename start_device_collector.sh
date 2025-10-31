#!/bin/bash
# 设备实时数据采集器启动脚本

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量（如果有的话）
if [ -f "device.env" ]; then
    echo "加载设备数据采集器环境配置..."
    export $(grep -v '^#' device.env | xargs)
else
    echo "使用默认配置"
fi

# 检查Python脚本是否存在
if [ ! -f "device_realtime_collector.py" ]; then
    echo "错误: 未找到 device_realtime_collector.py 脚本"
    exit 1
fi

# 检查是否已经在运行
if [ -f "device_realtime_collector.pid" ]; then
    PID=$(cat device_realtime_collector.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "设备数据采集器已在运行 (PID: $PID)"
        echo "如需重启，请先停止现有进程"
        exit 1
    else
        echo "清理旧的PID文件"
        rm -f device_realtime_collector.pid
    fi
fi

# 启动设备数据采集器
echo "启动设备数据采集器..."
echo "数据库: ${MONGO_DB:-ezdata}"
echo "采集间隔: ${IOT_INTERVAL_SECONDS:-60}秒"
echo "日志文件: ${IOT_LOG_FILE:-device_data.log}"

nohup python3 device_realtime_collector.py > device_realtime_boost.out 2>&1 & 
echo $! > device_realtime_collector.pid

echo "设备数据采集器已启动 (PID: $(cat device_realtime_collector.pid))"
echo "查看日志: tail -f device_data.log"
echo "查看输出: tail -f device_realtime_boost.out"

