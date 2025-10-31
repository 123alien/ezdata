#!/bin/bash
echo "==================== 数据采集器状态检查 ===================="
echo ""

# 检查门禁数据采集器
if [ -f "door_access_collector.pid" ]; then
    PID=$(cat door_access_collector.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 门禁数据采集器: 运行中 (PID: $PID)"
        echo "   采集间隔: 1小时"
        echo "   日志文件: door_access.log"
    else
        echo "❌ 门禁数据采集器: 未运行"
    fi
else
    echo "❌ 门禁数据采集器: PID文件不存在"
fi

echo ""

# 检查设备数据采集器
if [ -f "device_realtime_collector.pid" ]; then
    PID=$(cat device_realtime_collector.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 设备数据采集器: 运行中 (PID: $PID)"
        echo "   采集间隔: 60秒"
        echo "   日志文件: device_data.log"
    else
        echo "❌ 设备数据采集器: 未运行"
    fi
else
    echo "❌ 设备数据采集器: PID文件不存在"
fi

echo ""
echo "==================== MongoDB数据统计 ===================="
echo "门禁数据记录数: $(docker exec mongodb mongosh -u admin -p admin123 --authenticationDatabase admin ezdata --quiet --eval 'db.door_access_logs.countDocuments({})')"
echo "设备快照记录数: $(docker exec mongodb mongosh -u admin -p admin123 --authenticationDatabase admin ezdata --quiet --eval 'db.env_device_snapshot.countDocuments({})')"
echo "设备因子记录数: $(docker exec mongodb mongosh -u admin -p admin123 --authenticationDatabase admin ezdata --quiet --eval 'db.env_device_factor_snapshot.countDocuments({})')"
