#!/bin/bash
# 门禁数据采集器停止脚本

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查PID文件是否存在
if [ ! -f "door_access_collector.pid" ]; then
    echo "门禁数据采集器未运行 (未找到PID文件)"
    exit 1
fi

# 读取PID
PID=$(cat door_access_collector.pid)

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "门禁数据采集器未运行 (进程不存在)"
    rm -f door_access_collector.pid
    exit 1
fi

# 停止进程
echo "停止门禁数据采集器 (PID: $PID)..."
kill $PID

# 等待进程结束
sleep 2

# 检查是否成功停止
if ps -p $PID > /dev/null 2>&1; then
    echo "强制停止门禁数据采集器..."
    kill -9 $PID
    sleep 1
fi

# 清理PID文件
rm -f door_access_collector.pid

echo "门禁数据采集器已停止"
