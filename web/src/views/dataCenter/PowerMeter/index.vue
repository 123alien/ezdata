<template>
  <div class="power-meter-dashboard">
    <!-- 页面标题和概览 -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="header-title">
          <a-icon type="thunderbolt" class="title-icon" />
          <h1>用电统计监控</h1>
          <div class="title-subtitle">实时监控电表设备用电情况</div>
        </div>
        <div class="header-actions">
          <a-tooltip title="数据每30秒自动更新">
            <a-button type="primary" shape="circle" :loading="isLoading">
              <a-icon type="sync" :spin="isLoading" />
            </a-button>
          </a-tooltip>
        </div>
      </div>
    </div>

    <!-- 统计概览卡片 -->
    <div class="stats-overview">
      <div class="stat-card total-devices">
        <div class="stat-icon">
          <a-icon type="cluster" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ deviceStats.total_devices || 0 }}</div>
          <div class="stat-label">设备总数</div>
        </div>
      </div>
      
      <div class="stat-card online-devices">
        <div class="stat-icon">
          <a-icon type="check-circle" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ deviceStats.online_devices || 0 }}</div>
          <div class="stat-label">在线设备</div>
        </div>
      </div>
      
      <div class="stat-card offline-devices">
        <div class="stat-icon">
          <a-icon type="close-circle" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ deviceStats.offline_devices || 0 }}</div>
          <div class="stat-label">离线设备</div>
        </div>
      </div>
      
      <div class="stat-card total-power">
        <div class="stat-icon">
          <a-icon type="dashboard" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ totalPowerConsumption.toLocaleString() }}</div>
          <div class="stat-label">总用电量 (kWh)</div>
        </div>
      </div>
    </div>

    <!-- 实时监控设备卡片 -->
    <div class="monitoring-section">
      <div class="section-header">
        <h2 class="section-title">
          <a-icon type="monitor" />
          实时用电监控
        </h2>
        <div class="section-subtitle">实时监控各电表设备的用电状态</div>
      </div>
      
      <div class="device-grid">
        <div 
          v-for="device in powerMeterDevices" 
          :key="device.name"
          class="device-card"
          :class="{ 'device-offline': device.status !== 'online' }"
        >
          <div class="device-card-header">
            <div class="device-info">
              <div class="device-icon">
                <a-icon type="thunderbolt" />
              </div>
              <div class="device-details">
                <div class="device-name">{{ device.name }}</div>
                <div class="device-location">{{ device.location || '未知位置' }}</div>
              </div>
            </div>
            <div class="device-status">
              <a-badge 
                :status="device.status === 'online' ? 'processing' : 'error'" 
                :text="device.status === 'online' ? '在线' : '离线'"
              />
            </div>
          </div>
          
          <div class="device-metrics">
            <div class="metric-row">
              <div class="metric-item">
                <div class="metric-icon">
                  <a-icon type="dashboard" />
                </div>
                <div class="metric-content">
                  <div class="metric-label">累计用电</div>
                  <div class="metric-value total-power">
                    {{ (device.metrics?.totalPower || 0).toLocaleString() }}
                    <span class="metric-unit">kWh</span>
                  </div>
                </div>
              </div>
              
              <div class="metric-item">
                <div class="metric-icon">
                  <a-icon type="calendar" />
                </div>
                <div class="metric-content">
                  <div class="metric-label">今日用电</div>
                  <div class="metric-value today-power">
                    {{ (device.metrics?.todayPower || 0).toLocaleString() }}
                    <span class="metric-unit">kWh</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="device-footer">
            <div class="update-info">
              <a-icon type="clock-circle" />
              <span>{{ device.lastUpdate ? dayjs(device.lastUpdate).format('MM-DD HH:mm:ss') : '—' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据图表区域 -->
    <div class="charts-section">
      <div class="section-header">
        <h2 class="section-title">
          <a-icon type="bar-chart" />
          用电数据分析
        </h2>
        <div class="section-subtitle">用电趋势和设备占比分析</div>
      </div>
      
      <div class="charts-grid">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">日用电量趋势</h3>
            <div class="chart-subtitle">近7天用电量变化趋势</div>
          </div>
          <div class="chart-content">
            <div ref="dailyPowerChartRef" class="chart-container"></div>
          </div>
        </div>
        
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">设备用电占比</h3>
            <div class="chart-subtitle">各设备用电量分布</div>
          </div>
          <div class="chart-content">
            <div ref="powerDistributionChartRef" class="chart-container"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 设备详情图表 -->
    <div class="device-chart-section">
      <div class="section-header">
        <h2 class="section-title">
          <a-icon type="line-chart" />
          设备详情分析
        </h2>
        <div class="section-subtitle">选择设备查看详细用电数据</div>
      </div>
      
      <div class="device-chart-container">
        <DeviceChart 
          :device-options="powerMeterOptions" 
          device-type="power"
          ref="deviceChartRef"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import dayjs from 'dayjs';
import { useMessage } from '/@/hooks/web/useMessage';
import { useECharts } from '/@/hooks/web/useECharts';
import { getPowerMeterStats, getDailyPowerTrend } from '/@/views/dashboard/api';
import DeviceChart from '../components/DeviceChart.vue';

const { createMessage } = useMessage();

// 图表引用
const dailyPowerChartRef = ref<HTMLDivElement | null>(null);
const powerDistributionChartRef = ref<HTMLDivElement | null>(null);
const { setOptions: setDailyPowerChart } = useECharts(dailyPowerChartRef);
const { setOptions: setPowerDistributionChart } = useECharts(powerDistributionChartRef);

// 响应式数据
const deviceStats = ref<any>({ total_devices: 0, status_dist: {}, devices: [] });
const powerMeterDevices = ref<any[]>([]);
const isLoading = ref(false);

// 电表设备选项
const powerMeterOptions = [
  { label: '07室电表', value: '07室电表' },
  { label: '08室电表', value: '08室电表' },
  { label: '01室电表', value: '01室电表' },
];


// 计算属性
const totalPowerConsumption = computed(() => {
  return powerMeterDevices.value.reduce((sum, device) => {
    return sum + (device.metrics?.totalPower || 0);
  }, 0);
});

// 获取设备统计信息
async function fetchDeviceStats() {
  try {
    const res = await getPowerMeterStats();
    deviceStats.value = res;
    
    // 使用电表设备数据
    const powerDevices = res.recent_devices || [];
    
    
    // 初始化实时监控数据
    powerMeterDevices.value = powerDevices.map((device: any) => ({
      name: device.device_name,
      status: device.status === '在线' ? 'online' : 'offline',
      lastUpdate: device.last_update || null,
      metrics: {
        totalPower: device.total_power || 0,
        todayPower: device.today_power || 0,
      },
    }));
    
  } catch (error) {
    console.error('获取设备统计失败:', error);
    createMessage.error('获取设备统计失败');
  }
}


// 更新实时数据（从后端获取真实数据）
async function updateRealTimeData() {
  try {
    const res = await getPowerMeterStats();
    const powerDevices = res.recent_devices || [];
    
    // 更新设备数据
    powerMeterDevices.value = powerDevices.map((device: any) => ({
      name: device.device_name,
      status: device.status === '在线' ? 'online' : 'offline',
      lastUpdate: device.last_update || null,
      metrics: {
        totalPower: device.total_power || 0,
        todayPower: device.today_power || 0,
      },
    }));
  } catch (error) {
    console.error('更新实时数据失败:', error);
  }
}

// 获取日用电量趋势数据
async function fetchDailyPowerTrend() {
  try {
    // 使用后端API获取历史数据
    const res = await getDailyPowerTrend({ days: 7 });
    const trendData = res || [];
    
    // 如果API返回空数据，使用模拟数据作为备选
    if (trendData.length === 0) {
      const today = dayjs();
      const mockData = [35, 28, 42, 31, 38, 25, 33];
      
      return Array.from({ length: 7 }, (_, i) => {
        const date = today.subtract(6 - i, 'day');
        return {
          date: date.format('YYYY-MM-DD'),
          dayName: date.format('ddd'),
          value: mockData[i]
        };
      });
    }
    
    return trendData;
  } catch (error) {
    console.error('获取日用电量趋势失败:', error);
    // 返回模拟数据作为备选
    const today = dayjs();
    const mockData = [35, 28, 42, 31, 38, 25, 33];
    
    return Array.from({ length: 7 }, (_, i) => {
      const date = today.subtract(6 - i, 'day');
      return {
        date: date.format('YYYY-MM-DD'),
        dayName: date.format('ddd'),
        value: mockData[i]
      };
    });
  }
}

// 获取设备用电占比数据
async function fetchPowerDistribution() {
  try {
    const res = await getPowerMeterStats();
    const devices = res.recent_devices || [];
    
    const distributionData = devices.map(device => ({
      name: device.device_name,
      value: device.total_power || 0
    }));
    
    return distributionData;
  } catch (error) {
    console.error('获取设备用电占比失败:', error);
    return [];
  }
}

// 初始化图表
async function initCharts() {
  // 获取真实数据
  const dailyTrend = await fetchDailyPowerTrend();
  const distributionData = await fetchPowerDistribution();
  
  // 日用电量趋势图
  setDailyPowerChart({
    title: {
      text: '近7天用电量',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const data = params[0];
        return `${data.name}<br/>用电量: ${data.value} kWh`;
      }
    },
    xAxis: {
      type: 'category',
      data: dailyTrend.map(item => item.dayName),
    },
    yAxis: {
      type: 'value',
      name: '用电量(kWh)',
    },
    series: [
      {
        name: '用电量',
        type: 'line',
        data: dailyTrend.map(item => item.value),
        smooth: true,
        areaStyle: {
          opacity: 0.3,
        },
        itemStyle: {
          color: '#1890ff'
        }
      },
    ],
  });

  // 设备用电占比饼图
  setPowerDistributionChart({
    title: {
      text: '设备用电占比',
      left: 'center',
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} kWh ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: '用电量',
        type: 'pie',
        radius: '50%',
        data: distributionData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        }
      },
    ],
  });
}

onMounted(async () => {
  await fetchDeviceStats();
  await initCharts();
  
  // 每30秒更新一次实时数据
  setInterval(updateRealTimeData, 30000);
});
</script>

<style scoped>
.power-meter-dashboard {
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* 页面标题区域 */
.dashboard-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 32px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.dashboard-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  pointer-events: none;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.header-title h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
  color: #fff;
}

.title-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin-left: 48px;
}

.header-actions {
  position: relative;
  z-index: 1;
}

/* 统计概览卡片 */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.total-devices::before {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.online-devices::before {
  background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
}

.stat-card.offline-devices::before {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
}

.stat-card.total-power::before {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.total-devices .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.online-devices .stat-icon {
  background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
}

.offline-devices .stat-icon {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
}

.total-power .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

/* 监控区域 */
.monitoring-section {
  margin-bottom: 40px;
}

.section-header {
  margin-bottom: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-subtitle {
  font-size: 16px;
  color: #7f8c8d;
  margin-left: 36px;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.device-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
  position: relative;
  overflow: hidden;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.device-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
}

.device-card.device-offline::before {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
}

.device-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.device-details {
  flex: 1;
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.device-location {
  font-size: 12px;
  color: #7f8c8d;
}

.device-status {
  flex-shrink: 0;
}

.device-metrics {
  margin-bottom: 20px;
}

.metric-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.metric-item {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
}

.metric-item:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.metric-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
}

.metric-content {
  flex: 1;
}

.metric-label {
  font-size: 12px;
  color: #7f8c8d;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: #2c3e50;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-unit {
  font-size: 12px;
  color: #7f8c8d;
  font-weight: 500;
}

.total-power {
  color: #27ae60;
}

.today-power {
  color: #f39c12;
}

.device-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.update-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #7f8c8d;
}

/* 图表区域 */
.charts-section {
  margin-bottom: 40px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 24px;
}

.chart-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.chart-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.chart-header {
  margin-bottom: 20px;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.chart-subtitle {
  font-size: 14px;
  color: #7f8c8d;
}

.chart-content {
  height: 300px;
}

.chart-container {
  height: 100%;
  width: 100%;
}

/* 设备详情图表 */
.device-chart-section {
  margin-bottom: 40px;
}

.device-chart-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .power-meter-dashboard {
    padding: 16px;
  }
  
  .dashboard-header {
    padding: 24px;
  }
  
  .header-title h1 {
    font-size: 24px;
  }
  
  .stats-overview {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .device-grid {
    grid-template-columns: 1fr;
  }
  
  .metric-row {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .title-subtitle {
    margin-left: 0;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .device-card {
    padding: 16px;
  }
}
</style>
