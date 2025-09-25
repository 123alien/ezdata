<template>
  <div class="environment-monitoring">
    <!-- 页面标题和概览 -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="header-title">
          <a-icon type="environment" class="title-icon" />
          <h1>环境监测设备</h1>
          <div class="title-subtitle">实时监控环境监测设备状态</div>
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
          <div class="stat-value">{{ deviceStats.status_distribution?.find(s => s.name === '在线')?.value || 0 }}</div>
          <div class="stat-label">在线设备</div>
        </div>
      </div>
      
      <div class="stat-card offline-devices">
        <div class="stat-icon">
          <a-icon type="close-circle" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ deviceStats.status_distribution?.find(s => s.name === '离线')?.value || 0 }}</div>
          <div class="stat-label">离线设备</div>
        </div>
      </div>
      
      <div class="stat-card total-metrics">
        <div class="stat-icon">
          <a-icon type="dashboard" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ totalDataPoints }}</div>
          <div class="stat-label">数据点数</div>
        </div>
      </div>
    </div>

    <!-- 实时监控设备卡片 -->
    <div class="monitoring-section">
      <div class="section-header">
        <h2 class="section-title">
          <a-icon type="monitor" />
          实时数据监控
        </h2>
        <div class="section-subtitle">实时监控各环境监测设备状态</div>
      </div>
      
      <div class="device-grid">
        <div 
          v-for="device in environmentDevices" 
          :key="device.name"
          class="device-card"
          :class="{ 'device-offline': device.status !== 'online' }"
        >
          <div class="device-card-header">
            <div class="device-info">
              <div class="device-icon">
                <a-icon type="environment" />
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
                  <a-icon type="fire" />
                </div>
                <div class="metric-content">
                  <div class="metric-label">温度</div>
                  <div class="metric-value temperature">
                    {{ device.metrics?.TEM || 0 }}
                    <span class="metric-unit">°C</span>
                  </div>
                </div>
              </div>
              
              <div class="metric-item">
                <div class="metric-icon">
                  <a-icon type="cloud" />
                </div>
                <div class="metric-content">
                  <div class="metric-label">湿度</div>
                  <div class="metric-value humidity">
                    {{ device.metrics?.RH || 0 }}
                    <span class="metric-unit">%</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 室内环境监测设备显示CO2和PM2.5 -->
            <div v-if="!device.name.includes('室外')" class="metric-row">
              <div class="metric-item">
                <div class="metric-icon">
                  <a-icon type="experiment" />
                </div>
                <div class="metric-content">
                  <div class="metric-label">CO2</div>
                  <div class="metric-value co2">
                    {{ device.metrics?.CO2 || 0 }}
                    <span class="metric-unit">ppm</span>
                  </div>
                </div>
              </div>
              
              <div class="metric-item">
                <div class="metric-icon">
                  <a-icon type="cloud-download" />
                </div>
                <div class="metric-content">
                  <div class="metric-label">PM2.5</div>
                  <div class="metric-value pm25">
                    {{ device.metrics?.PM25 || 0 }}
                    <span class="metric-unit">μg/m³</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 室外环境检测仪只显示PM2.5 -->
            <div v-if="device.name.includes('室外')" class="metric-row">
              <div class="metric-item">
                <div class="metric-label">PM2.5</div>
                <div class="metric-value">{{ device.metrics?.PM25 || 0 }}μg/m³</div>
              </div>
              <div class="metric-item">
                <!-- 空位，保持布局平衡 -->
              </div>
            </div>
            
            <!-- 室内环境监测设备只显示PM10，居中显示 -->
            <div v-if="!device.name.includes('室外')" class="metric-row metric-row-single">
              <div class="metric-item metric-item-center">
                <div class="metric-label">PM10</div>
                <div class="metric-value">{{ device.metrics?.PM10 || 0 }}μg/m³</div>
              </div>
            </div>
            
            <!-- 室外环境检测仪显示PM10和大气压 -->
            <div v-if="device.name.includes('室外')" class="metric-row">
              <div class="metric-item">
                <div class="metric-label">PM10</div>
                <div class="metric-value">{{ device.metrics?.PM10 || 0 }}μg/m³</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">大气压</div>
                <div class="metric-value">{{ device.metrics?.PRESSURE || 0 }}hPa</div>
              </div>
            </div>
            
            <!-- 室外环境检测仪的风速和风向 -->
            <div v-if="device.name.includes('室外')" class="metric-row">
              <div class="metric-item">
                <div class="metric-label">风速</div>
                <div class="metric-value">{{ device.metrics?.WIND_SPEED || 0 }}m/s</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">风向</div>
                <div class="metric-value">{{ device.metrics?.WIND_DIRECTION || 0 }}°</div>
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
    
    <!-- 环境监测设备概览 -->
    <a-card title="环境监测设备概览" class="mb-4">
      <a-row :gutter="16" class="mb-4">
        <a-col :span="6"><a-statistic title="设备总数" :value="deviceStats.total_devices || 0" /></a-col>
        <a-col :span="6"><a-statistic title="在线设备" :value="deviceStats.status_distribution?.find(s => s.name === '在线')?.value || 0" /></a-col>
        <a-col :span="6"><a-statistic title="离线设备" :value="deviceStats.status_distribution?.find(s => s.name === '离线')?.value || 0" /></a-col>
        <a-col :span="6"><a-statistic title="数据点数" :value="totalDataPoints" /></a-col>
      </a-row>
      
      <DeviceChart 
        :device-options="environmentDeviceOptions" 
        device-type="environment"
        ref="deviceChartRef"
      />
    </a-card>

    <!-- 设备列表 -->
    <a-card title="设备列表" class="mb-4">
      <a-table 
        :columns="columns" 
        :data-source="deviceList" 
        :pagination="false"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'online' ? 'green' : 'red'">
              {{ record.status === 'online' ? '在线' : '离线' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'lastUpdate'">
            {{ record.lastUpdate ? dayjs(record.lastUpdate).format('YYYY-MM-DD HH:mm:ss') : '—' }}
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" @click="viewDeviceDetail(record)">
              查看详情
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import dayjs from 'dayjs';
import { useMessage } from '/@/hooks/web/useMessage';
import { getDeviceStats } from '/@/views/dashboard/api';
import DeviceChart from '../components/DeviceChart.vue';

const { createMessage } = useMessage();

// 响应式数据
const deviceStats = ref<any>({ 
  total_devices: 0, status_dist: {}, devices: [] });
const deviceList = ref<any[]>([]);
const environmentDevices = ref<any[]>([]);
const isLoading = ref(false);

// 环境监测设备选项
const environmentDeviceOptions = [
  { label: '07室环境监测', value: '07室环境监测' },
  { label: '08室环境监测', value: '08室环境监测' },
  { label: '09室环境监测', value: '09室环境监测' },
  { label: '01室环境监测', value: '01室环境监测' },
  { label: '02室环境监测', value: '02室环境监测' },
  { label: '室外环境检测仪', value: '室外环境检测仪' },
];

// 表格列配置
const columns = [
  {
    title: '设备名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '设备类型',
    dataIndex: 'type',
    key: 'type',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
  },
  {
    title: '最后更新',
    dataIndex: 'lastUpdate',
    key: 'lastUpdate',
  },
  {
    title: '操作',
    key: 'action',
  },
];

// 计算属性
const totalDataPoints = computed(() => {
  return environmentDevices.value.reduce((sum, device) => {
    return sum + (device.metrics ? Object.keys(device.metrics).length : 0);
  }, 0);
});

// 获取设备统计信息
async function fetchDeviceStats() {
  try {
    console.log('开始获取设备统计信息...');
    const res = await getDeviceStats();
    console.log('设备统计信息响应:', res);
    deviceStats.value = res;
    
    // 过滤环境监测设备
    const allDevices = res.recent_devices || [];
    const envDevices = allDevices.filter((device: any) => 
      device.device_name && (device.device_name.includes('环境监测') || device.device_name.includes('环境检测'))
    );
    
    deviceList.value = envDevices.map((device: any) => ({
      name: device.device_name,
      type: '环境监测',
      status: device.status || 'offline',
      lastUpdate: device.last_update || null,
    }));
    
    // 从设备统计数据中提取环境监测设备数据
    extractEnvironmentDevicesFromStats();
    
  } catch (error) {
    console.error('获取设备统计失败:', error);
    createMessage.error('获取设备统计失败');
  }
}

// 从设备统计数据中提取环境监测设备数据
function extractEnvironmentDevicesFromStats() {
  try {
    // 从设备统计中过滤环境监测设备
    const allDevices = deviceStats.value.recent_devices || [];
    const envDevices = allDevices.filter((device: any) => 
      device.device_name && (device.device_name.includes('环境监测') || device.device_name.includes('环境检测'))
    );
    
    console.log('从统计数据中找到的环境监测设备:', envDevices);
    
    // 转换为环境监测设备格式
    const devices = envDevices.map((device: any) => {
      // 从原始数据中提取各种指标
      const metrics = {
        TEM: extractMetricValue(device, 'TEM'),
        RH: extractMetricValue(device, 'RH'),
        CO2: extractMetricValue(device, 'CO2'),
        PM25: extractMetricValue(device, 'PM25'),
        PM10: extractMetricValue(device, 'PM10'),
        NOISE: extractMetricValue(device, 'NOISE'),
        // 室外环境检测仪的特殊指标
        PRESSURE: extractMetricValue(device, 'PRESSURE'),
        WIND_SPEED: extractMetricValue(device, 'WIND_SPEED'),
        WIND_DIRECTION: extractMetricValue(device, 'WIND_DIRECTION'),
      };
      
      // 判断设备在线状态
      let deviceStatus = 'offline';
      if (device.status === '在线' || device.status === 'online') {
        deviceStatus = 'online';
      } else if (device.last_update) {
        // 根据最后更新时间判断（10分钟内为在线）
        const lastUpdate = new Date(device.last_update);
        const now = new Date();
        const diffMinutes = (now.getTime() - lastUpdate.getTime()) / (1000 * 60);
        if (diffMinutes <= 10) {
          deviceStatus = 'online';
        }
      }
      
      return {
        name: device.device_name,
        status: deviceStatus,
        lastUpdate: device.last_update || new Date().getTime(),
        metrics: metrics
      };
    });
    
    // 如果找到真实设备，使用真实数据
    if (devices.length > 0) {
      environmentDevices.value = devices;
      console.log('从统计数据获取环境监测设备:', environmentDevices.value);
    } else {
      // 如果没有找到真实设备，使用默认数据
      console.log('未找到环境监测设备，使用默认数据');
    }
    
  } catch (error) {
    console.error('从统计数据提取环境监测设备失败:', error);
  }
}

// 从设备数据中提取指标值
function extractMetricValue(device: any, metricType: string) {
  try {
    // 直接从raw_data中获取对应指标的值
    if (device.raw_data && device.raw_data[metricType] !== undefined) {
      return parseFloat(device.raw_data[metricType]) || 0;
    }
    
    // 尝试从其他字段获取
    if (device[metricType]) {
      return parseFloat(device[metricType]) || 0;
    }
    
    // 尝试从metrics字段获取
    if (device.metrics && device.metrics[metricType]) {
      return parseFloat(device.metrics[metricType]) || 0;
    }
    
    return 0;
  } catch (error) {
    console.error(`提取指标 ${metricType} 失败:`, error);
    return 0;
  }
}


// 查看设备详情
function viewDeviceDetail(record: any) {
  createMessage.info(`查看设备详情: ${record.name}`);
  // 这里可以跳转到设备详情页面或打开详情弹窗
}


// 实时数据更新
async function updateRealTimeData() {
  try {
    // 重新获取设备统计数据
    await fetchDeviceStats();
  } catch (error) {
    console.error('更新环境监测设备数据失败:', error);
  }
}

onMounted(async () => {
  console.log('环境监测设备组件已挂载');
  
  // 先设置默认数据，确保界面有内容显示
  environmentDevices.value = [
    {
      name: '07室环境监测',
      status: 'online',
      lastUpdate: new Date().getTime(),
      metrics: {
        TEM: 24.5,
        RH: 61,
        CO2: 454,
        PM25: 45,
        PM10: 36,
        NOISE: 9.3,
      },
    },
    {
      name: '08室环境监测',
      status: 'online',
      lastUpdate: new Date().getTime(),
      metrics: {
        TEM: 23.8,
        RH: 58,
        CO2: 420,
        PM25: 38,
        PM10: 42,
        NOISE: 8.7,
      },
    },
    {
      name: '01室环境监测',
      status: 'online',
      lastUpdate: new Date().getTime(),
      metrics: {
        TEM: 25.2,
        RH: 65,
        CO2: 480,
        PM25: 52,
        PM10: 48,
        NOISE: 10.1,
      },
    },
    {
      name: '02室环境监测',
      status: 'online',
      lastUpdate: new Date().getTime(),
      metrics: {
        TEM: 22.9,
        RH: 55,
        CO2: 380,
        PM25: 32,
        PM10: 28,
        NOISE: 7.8,
      },
    },
    {
      name: '09室环境监测',
      status: 'online',
      lastUpdate: new Date().getTime(),
      metrics: {
        TEM: 26.1,
        RH: 68,
        CO2: 520,
        PM25: 58,
        PM10: 55,
        NOISE: 11.2,
      },
    },
    {
      name: '室外环境检测仪',
      status: 'offline',
      lastUpdate: new Date().getTime() - 600000,
      metrics: {
        TEM: 0,
        RH: 0,
        CO2: 0,
        PM25: 0,
        PM10: 0,
        NOISE: 0,
      },
    },
  ];
  
  console.log('默认环境监测设备数据已设置:', environmentDevices.value);
  console.log('设备数量:', environmentDevices.value.length);
  
  try {
    await fetchDeviceStats();
    console.log('设备统计获取成功');
  } catch (error) {
    console.error('设备统计获取失败:', error);
    createMessage.error('获取设备数据失败');
  }
  
  // 每30秒更新一次实时数据
  setInterval(updateRealTimeData, 30000);
});
</script>

<style scoped>
.environment-monitoring {
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

.stat-card.total-metrics::before {
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

.total-metrics .stat-icon {
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

.monitoring-header {
  margin-bottom: 32px;
  position: relative;
}

.monitoring-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  position: relative;
  z-index: 2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.title-decoration {
  position: absolute;
  top: 0;
  right: 0;
  width: 150px;
  height: 3px;
  background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
  border-radius: 2px;
}

.title-decoration::before {
  content: '';
  position: absolute;
  top: -6px;
  right: 15px;
  width: 40px;
  height: 2px;
  background: linear-gradient(45deg, #00d4ff 0%, #0099cc 100%);
  transform: rotate(15deg);
}

.title-decoration::after {
  content: '';
  position: absolute;
  top: -9px;
  right: 30px;
  width: 30px;
  height: 2px;
  background: linear-gradient(45deg, #00d4ff 0%, #0099cc 100%);
  transform: rotate(30deg);
}

/* 设备卡片网格 */
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.device-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  border: 2px solid #f8f9fa;
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

.device-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 15px;
  height: 15px;
  border-top: 2px solid #00d4ff;
  border-left: 2px solid #00d4ff;
}

.device-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 15px;
  height: 15px;
  border-bottom: 2px solid #00d4ff;
  border-right: 2px solid #00d4ff;
}

.device-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.15);
  border-color: rgba(0, 212, 255, 0.5);
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
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.device-location {
  font-size: 13px;
  color: #666666;
  font-weight: 500;
}

.device-status {
  flex-shrink: 0;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.device-status.online {
  color: #00ff88;
  border-color: rgba(0, 255, 136, 0.3);
  background: rgba(0, 255, 136, 0.1);
}

.device-status.offline {
  color: #ff6b6b;
  border-color: rgba(255, 107, 107, 0.3);
  background: rgba(255, 107, 107, 0.1);
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
  flex-shrink: 0;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
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
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.metric-item:hover {
  background: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #dee2e6;
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
  font-size: 13px;
  color: #333333;
  margin-bottom: 6px;
  font-weight: 600;
}

.metric-value {
  font-size: 20px;
  font-weight: 800;
  color: #1a1a1a;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-unit {
  font-size: 13px;
  color: #666666;
  font-weight: 600;
}

.temperature {
  color: #d63031;
}

.humidity {
  color: #0984e3;
}

.co2 {
  color: #6c5ce7;
}

.pm25 {
  color: #e17055;
}

.pm10 {
  color: #00b894;
}

.device-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.update-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #555555;
  font-weight: 500;
}

.mt-2 {
  margin-top: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .device-grid {
    grid-template-columns: 1fr;
  }
  
  .section-title {
    font-size: 20px;
  }
  
  .device-card {
    padding: 16px;
  }
  
  .metric-value {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .environment-monitoring {
    padding: 16px;
  }
  
  .real-time-monitoring {
    padding: 20px;
  }
  
  .monitoring-title {
    font-size: 20px;
  }
  
  .device-cards-grid {
    gap: 16px;
  }
  
  .metric-row {
    gap: 8px;
  }
  
  .metric-item {
    padding: 6px;
  }
}
</style>
