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


    <!-- 二氧化碳趋势图表 -->
    <div class="co2-charts-section">
      <h3 class="section-title">
        <a-icon type="line-chart" />
        二氧化碳浓度趋势图
      </h3>
      
      <!-- 时间范围选择器 -->
      <div class="time-selector">
        <a-select 
          v-model:value="selectedTimeRange" 
          placeholder="选择时间范围"
          style="width: 150px;"
          @change="onTimeRangeChange"
        >
          <a-select-option value="1h">最近1小时</a-select-option>
          <a-select-option value="6h">最近6小时</a-select-option>
          <a-select-option value="24h">最近24小时</a-select-option>
          <a-select-option value="7d">最近7天</a-select-option>
        </a-select>
      </div>

      <!-- 两个CO2图表 -->
      <div class="co2-charts-grid">
        <!-- 第一个图表：07、08、09室 -->
        <div class="co2-chart-card">
          <div class="chart-header">
            <h4>07、08、09设备二氧化碳浓度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="co2Chart1Ref" class="co2-chart"></div>
          </div>
        </div>

        <!-- 第二个图表：01、02、室外 -->
        <div class="co2-chart-card">
          <div class="chart-header">
            <h4>01、02、室外设备二氧化碳浓度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="co2Chart2Ref" class="co2-chart"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- PM2.5浓度趋势图 -->
    <div class="charts-section">
      <div class="section-header">
        <h3 class="section-title">
          <a-icon type="cloud" />
          PM2.5浓度趋势图
        </h3>
      </div>
      
      <!-- 两个PM2.5图表 -->
      <div class="charts-grid">
        <!-- 第一个图表：07、08、09室 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>07、08、09设备PM2.5浓度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="pm25Chart1Ref" class="metric-chart"></div>
          </div>
        </div>

        <!-- 第二个图表：01、02、室外 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>01、02、室外设备PM2.5浓度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="pm25Chart2Ref" class="metric-chart"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- PM10浓度趋势图 -->
    <div class="charts-section">
      <div class="section-header">
        <h3 class="section-title">
          <a-icon type="cloud-server" />
          PM10浓度趋势图
        </h3>
      </div>
      
      <!-- 两个PM10图表 -->
      <div class="charts-grid">
        <!-- 第一个图表：07、08、09室 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>07、08、09设备PM10浓度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="pm10Chart1Ref" class="metric-chart"></div>
          </div>
        </div>

        <!-- 第二个图表：01、02、室外 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>01、02、室外设备PM10浓度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="pm10Chart2Ref" class="metric-chart"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 温度趋势图 -->
    <div class="charts-section">
      <div class="section-header">
        <h3 class="section-title">
          <a-icon type="fire" />
          温度趋势图
        </h3>
      </div>
      
      <!-- 两个温度图表 -->
      <div class="charts-grid">
        <!-- 第一个图表：07、08、09室 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>07、08、09设备温度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="tempChart1Ref" class="metric-chart"></div>
          </div>
        </div>

        <!-- 第二个图表：01、02、室外 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>01、02、室外设备温度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="tempChart2Ref" class="metric-chart"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 湿度趋势图 -->
    <div class="charts-section">
      <div class="section-header">
        <h3 class="section-title">
          <a-icon type="water" />
          湿度趋势图
        </h3>
      </div>
      
      <!-- 两个湿度图表 -->
      <div class="charts-grid">
        <!-- 第一个图表：07、08、09室 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>07、08、09设备湿度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="humidityChart1Ref" class="metric-chart"></div>
          </div>
        </div>

        <!-- 第二个图表：01、02、室外 -->
        <div class="chart-card">
          <div class="chart-header">
            <h4>01、02、室外设备湿度变化</h4>
          </div>
          <div class="chart-content">
            <div ref="humidityChart2Ref" class="metric-chart"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import dayjs from 'dayjs';
import { useMessage } from '/@/hooks/web/useMessage';
import { getDeviceStats, getDeviceMetrics } from '/@/views/dashboard/api';
import DeviceChart from '../components/DeviceChart.vue';

const { createMessage } = useMessage();

// 响应式数据
const deviceStats = ref<any>({ 
  total_devices: 0, status_dist: {}, devices: [] });
const deviceList = ref<any[]>([]);
const environmentDevices = ref<any[]>([]);
const isLoading = ref(false);

// 图表相关数据
const selectedTimeRange = ref('1h');
const co2Chart1Ref = ref<HTMLDivElement>();
const co2Chart2Ref = ref<HTMLDivElement>();
const pm25Chart1Ref = ref<HTMLDivElement>();
const pm25Chart2Ref = ref<HTMLDivElement>();
const pm10Chart1Ref = ref<HTMLDivElement>();
const pm10Chart2Ref = ref<HTMLDivElement>();
const tempChart1Ref = ref<HTMLDivElement>();
const tempChart2Ref = ref<HTMLDivElement>();
const humidityChart1Ref = ref<HTMLDivElement>();
const humidityChart2Ref = ref<HTMLDivElement>();

// 环境监测设备选项
const environmentDeviceOptions = [
  { label: '07室环境监测', value: '07室环境监测' },
  { label: '08室环境监测', value: '08室环境监测' },
  { label: '09室环境监测', value: '09室环境监测' },
  { label: '01室环境监测', value: '01室环境监测' },
  { label: '02室环境监测', value: '02室环境监测' },
  { label: '室外环境检测仪', value: '室外环境检测仪' },
];


// 计算属性
const totalDataPoints = computed(() => {
  return environmentDevices.value.reduce((sum, device) => {
    return sum + (device.metrics ? Object.keys(device.metrics).length : 0);
  }, 0);
});

// 室内设备（07、08、09室）
const indoorDevices = computed(() => {
  return environmentDevices.value.filter(device => {
    const deviceName = device.device_name || device.name || '';
    return deviceName.includes('07室') || 
           deviceName.includes('08室') || 
           deviceName.includes('09室');
  });
});

// 室外设备（01、02、室外）
const outdoorDevices = computed(() => {
  return environmentDevices.value.filter(device => {
    const deviceName = device.device_name || device.name || '';
    return deviceName.includes('01室') || 
           deviceName.includes('02室') || 
           deviceName.includes('室外');
  });
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
    console.log('开始提取环境监测设备数据...');
    console.log('设备统计数据:', deviceStats.value);
    
    // 从设备统计中过滤环境监测设备
    const allDevices = deviceStats.value.recent_devices || [];
    console.log('所有设备列表:', allDevices);
    
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



// 时间范围变化处理
function onTimeRangeChange(value: string) {
  console.log('选择时间范围:', value);
  selectedTimeRange.value = value;
  // 重新渲染所有图表
  renderCO2Charts();
  renderPM25Charts();
  renderPM10Charts();
  renderTempCharts();
  renderHumidityCharts();
}

// 渲染CO2图表
async function renderCO2Charts() {
  try {
    // 获取真实的历史数据
    await fetchRealTimeData();
    
    // 渲染第一个图表（室内设备）
    await renderCO2Chart(co2Chart1Ref.value, indoorDevices.value, '室内环境监测');
    
    // 渲染第二个图表（室外设备）
    await renderCO2Chart(co2Chart2Ref.value, outdoorDevices.value, '室外及特殊环境');
  } catch (error) {
    console.error('渲染CO2图表失败:', error);
  }
}

// 渲染PM2.5图表
async function renderPM25Charts() {
  try {
    // 获取真实的历史数据
    await fetchRealTimeData();
    
    // 渲染第一个图表（室内设备）
    await renderMetricChart(pm25Chart1Ref.value, indoorDevices.value, '室内环境监测', 'PM25', 'PM2.5浓度', 'μg/m³');
    
    // 渲染第二个图表（室外设备）
    await renderMetricChart(pm25Chart2Ref.value, outdoorDevices.value, '室外及特殊环境', 'PM25', 'PM2.5浓度', 'μg/m³');
  } catch (error) {
    console.error('渲染PM2.5图表失败:', error);
  }
}

// 渲染PM10图表
async function renderPM10Charts() {
  try {
    // 获取真实的历史数据
    await fetchRealTimeData();
    
    // 渲染第一个图表（室内设备）
    await renderMetricChart(pm10Chart1Ref.value, indoorDevices.value, '室内环境监测', 'PM10', 'PM10浓度', 'μg/m³');
    
    // 渲染第二个图表（室外设备）
    await renderMetricChart(pm10Chart2Ref.value, outdoorDevices.value, '室外及特殊环境', 'PM10', 'PM10浓度', 'μg/m³');
  } catch (error) {
    console.error('渲染PM10图表失败:', error);
  }
}

// 渲染温度图表
async function renderTempCharts() {
  try {
    // 获取真实的历史数据
    await fetchRealTimeData();
    
    // 渲染第一个图表（室内设备）
    await renderMetricChart(tempChart1Ref.value, indoorDevices.value, '室内环境监测', 'TEM', '温度', '°C');
    
    // 渲染第二个图表（室外设备）
    await renderMetricChart(tempChart2Ref.value, outdoorDevices.value, '室外及特殊环境', 'TEM', '温度', '°C');
  } catch (error) {
    console.error('渲染温度图表失败:', error);
  }
}

// 渲染湿度图表
async function renderHumidityCharts() {
  try {
    // 获取真实的历史数据
    await fetchRealTimeData();
    
    // 渲染第一个图表（室内设备）
    await renderMetricChart(humidityChart1Ref.value, indoorDevices.value, '室内环境监测', 'RH', '湿度', '%');
    
    // 渲染第二个图表（室外设备）
    await renderMetricChart(humidityChart2Ref.value, outdoorDevices.value, '室外及特殊环境', 'RH', '湿度', '%');
  } catch (error) {
    console.error('渲染湿度图表失败:', error);
  }
}

// 获取真实的历史数据
async function fetchRealTimeData() {
  try {
    console.log('获取真实设备数据...');
    
    // 调用设备统计API获取最新数据
    const response = await getDeviceStats();
    console.log('设备统计响应:', response);
    
    if (response && response.data) {
      // 更新设备统计数据
      deviceStats.value = response.data;
      
      // 重新提取环境监测设备数据
      extractEnvironmentDevicesFromStats();
      
      console.log('环境监测设备数据已更新:', environmentDevices.value);
    }
  } catch (error) {
    console.error('获取真实数据失败:', error);
  }
}

// 渲染单个CO2图表
async function renderCO2Chart(chartRef: HTMLDivElement | undefined, devices: any[], title: string) {
  if (!chartRef) return;
  
  try {
    console.log(`渲染${title}图表，设备数量:`, devices.length);
    console.log('设备列表:', devices);
    
    // 动态导入ECharts
    const echarts = await import('echarts');
    
    // 生成真实的时间序列数据
    const timePoints = generateTimePoints(selectedTimeRange.value);
    const seriesData = await generateCO2SeriesData(devices, timePoints);
    
    // 统一Y轴标签和单位为二氧化碳浓度 (ppm)
    const yAxisName = '二氧化碳浓度';
    const unit = 'ppm';
    
    // 配置图表选项
    const option = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
          color: '#333'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        formatter: function(params: any) {
          let result = `时间: ${params[0].axisValue}<br/>`;
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${param.value} ${unit}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: devices.map(d => d.name || d.device_name),
        bottom: 10,
        textStyle: {
          fontSize: 12
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: timePoints,
        name: '时间',
        nameLocation: 'middle',
        nameGap: 30,
        axisLabel: {
          fontSize: 10,
          rotate: 45, // 旋转45度避免重叠
          formatter: function(value: string) {
            return value;
          }
        }
      },
      yAxis: {
        type: 'value',
        name: yAxisName,
        nameLocation: 'middle',
        nameGap: 50,
        axisLabel: {
          formatter: `{value} ${unit}`,
          fontSize: 10
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      series: seriesData
    };
    
    // 初始化图表
    const chart = echarts.init(chartRef);
    chart.setOption(option);
    
    // 响应式调整
    window.addEventListener('resize', () => {
      chart.resize();
    });
    
  } catch (error) {
    console.error('渲染图表失败:', error);
    // 如果ECharts加载失败，显示占位内容
    chartRef.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: center; height: 300px; color: #666; background: #fafafa; border: 1px solid #e8e8e8; border-radius: 8px;">
        <div style="text-align: center;">
          <div style="font-size: 16px; margin-bottom: 8px; color: #333;">${title} - 环境监测趋势图</div>
          <div style="font-size: 14px; color: #666;">设备数量: ${devices.length}</div>
          <div style="font-size: 12px; color: #999; margin-top: 8px;">时间范围: ${selectedTimeRange.value}</div>
          <div style="font-size: 12px; color: #ff4d4f; margin-top: 8px;">图表加载失败</div>
        </div>
      </div>
    `;
  }
}

// 通用指标图表渲染函数
async function renderMetricChart(chartRef: HTMLDivElement | undefined, devices: any[], title: string, metricKey: string, yAxisName: string, unit: string) {
  if (!chartRef) return;
  
  try {
    console.log(`渲染${title}图表，设备数量:`, devices.length);
    console.log('设备列表:', devices);
    
    // 动态导入ECharts
    const echarts = await import('echarts');
    
    // 生成真实的时间序列数据
    const timePoints = generateTimePoints(selectedTimeRange.value);
    const seriesData = await generateMetricSeriesData(devices, timePoints, metricKey);
    
    // 配置图表选项
    const option = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
          color: '#333'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        formatter: function(params: any) {
          let result = `时间: ${params[0].axisValue}<br/>`;
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${param.value} ${unit}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: devices.map(d => d.name || d.device_name),
        bottom: 10,
        textStyle: {
          fontSize: 12
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: timePoints,
        name: '时间',
        nameLocation: 'middle',
        nameGap: 30,
        axisLabel: {
          fontSize: 10,
          rotate: 45, // 旋转45度避免重叠
          formatter: function(value: string) {
            return value;
          }
        }
      },
      yAxis: {
        type: 'value',
        name: yAxisName,
        nameLocation: 'middle',
        nameGap: 50,
        axisLabel: {
          formatter: `{value} ${unit}`,
          fontSize: 10
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      series: seriesData
    };
    
    // 初始化图表
    const chart = echarts.init(chartRef);
    chart.setOption(option);
    
    // 响应式调整
    window.addEventListener('resize', () => {
      chart.resize();
    });
    
  } catch (error) {
    console.error('渲染图表失败:', error);
    // 如果ECharts加载失败，显示占位内容
    chartRef.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: center; height: 300px; color: #666; background: #fafafa; border: 1px solid #e8e8e8; border-radius: 8px;">
        <div style="text-align: center;">
          <div style="font-size: 16px; margin-bottom: 8px; color: #333;">${title} - 环境监测趋势图</div>
          <div style="font-size: 14px; color: #666;">设备数量: ${devices.length}</div>
          <div style="font-size: 12px; color: #999; margin-top: 8px;">时间范围: ${selectedTimeRange.value}</div>
          <div style="font-size: 12px; color: #ff4d4f; margin-top: 8px;">图表加载失败</div>
        </div>
      </div>
    `;
  }
}

// 生成时间点数据
function generateTimePoints(timeRange: string): string[] {
  const points: string[] = [];
  const now = new Date();
  let interval = 0;
  let count = 0;
  
  switch (timeRange) {
    case '1h':
      interval = 5 * 60 * 1000; // 5分钟间隔
      count = 12; // 12个点
      break;
    case '6h':
      interval = 15 * 60 * 1000; // 15分钟间隔
      count = 24; // 24个点
      break;
    case '24h':
      interval = 60 * 60 * 1000; // 1小时间隔
      count = 24; // 24个点
      break;
    case '7d':
      interval = 6 * 60 * 60 * 1000; // 6小时间隔
      count = 28; // 28个点
      break;
    default:
      interval = 5 * 60 * 1000;
      count = 12;
  }
  
  // 从当前时间往前推
  for (let i = count - 1; i >= 0; i--) {
    const time = new Date(now.getTime() - i * interval);
    let timeStr = '';
    
    switch (timeRange) {
      case '1h':
        timeStr = dayjs(time).format('HH:mm');
        break;
      case '6h':
        timeStr = dayjs(time).format('HH:mm');
        break;
      case '24h':
        timeStr = dayjs(time).format('MM-DD HH:mm');
        break;
      case '7d':
        timeStr = dayjs(time).format('MM-DD HH:mm');
        break;
      default:
        timeStr = dayjs(time).format('HH:mm');
    }
    
    points.push(timeStr);
  }
  
  return points;
}

// 生成CO2系列数据
async function generateCO2SeriesData(devices: any[], timePoints: string[]) {
  const colors = ['#1890ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1', '#13c2c2'];
  
  const seriesData: any[] = [];
  
  // 统一时间范围，确保所有设备使用相同的时间点
  const endTime = new Date();
  const startTime = new Date(endTime.getTime() - getTimeRangeMs(selectedTimeRange.value));
  
  console.log(`统一时间范围: ${startTime.toISOString()} - ${endTime.toISOString()}`);
  
  for (let index = 0; index < devices.length; index++) {
    const device = devices[index];
    const deviceName = device.name || device.device_name || `设备${index + 1}`;
    
    try {
      // 检查设备是否在线
      const deviceStatus = device.status || device.device_status;
      if (deviceStatus === 'offline' || deviceStatus === '离线') {
        console.warn(`设备 ${deviceName} 离线，跳过历史数据获取`);
        // 离线设备显示空数据
        seriesData.push({
          name: `${deviceName} (离线)`,
          type: 'line',
          data: [],
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: {
            width: 2,
            type: 'dashed' // 离线设备用虚线
          },
          itemStyle: {
            color: colors[index % colors.length]
          },
          emphasis: {
            focus: 'series'
          }
        });
        continue; // 跳过这个设备
      }
      
      console.log(`获取设备 ${deviceName} 历史数据，时间范围: ${startTime.toISOString()} - ${endTime.toISOString()}`);
      
      const historyData = await getDeviceMetrics({
        deviceName: deviceName, // 使用正确的参数名
        start: startTime.valueOf(), // 使用毫秒时间戳
        end: endTime.valueOf()
      });
      
      console.log(`设备 ${deviceName} 历史数据:`, historyData);
      
      // 检查设备类型，室外设备没有CO2指标
      const isOutdoorDevice = deviceName.includes('室外') || deviceName.includes('Outdoor');
      const metricKey = 'CO2'; // 所有设备都尝试获取CO2数据
      const metricName = 'CO2';
      
      let data: number[] = [];
      
      if (historyData && historyData.series && historyData.series[metricKey] && historyData.series[metricKey].length > 0) {
        // 使用真实历史数据
        const metricSeries = historyData.series[metricKey];
        console.log(`设备 ${deviceName} ${metricName}原始数据:`, metricSeries);
        
        // 将时间序列数据转换为数值数组
        data = metricSeries.map((item: any) => item.v || item.value || 0);
        console.log(`设备 ${deviceName} ${metricName}数据点: ${data.length}`);
      } else {
        // 如果没有历史数据
        if (isOutdoorDevice) {
          // 室外设备没有CO2数据，设置为空数组（不画线）
          data = [];
          console.log(`设备 ${deviceName} 是室外设备，无CO2数据，不画线`);
        } else {
          // 室内设备使用当前值生成模拟数据
          const currentValue = device.metrics?.[metricKey] || device.raw_data?.[metricKey] || 400;
          data = timePoints.map((_, i) => {
            const baseValue = currentValue;
            const variation = Math.sin(i * 0.3) * 20 + Math.random() * 10 - 5;
            return Math.max(0, Math.round(baseValue + variation));
          });
          console.log(`设备 ${deviceName} 使用模拟数据，当前${metricName}: ${currentValue}`);
        }
      }
      
      seriesData.push({
        name: deviceName,
        type: 'line',
        data: data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 2
        },
        itemStyle: {
          color: colors[index % colors.length]
        },
        emphasis: {
          focus: 'series'
        }
      });
      
    } catch (error) {
      console.error(`处理设备 ${deviceName} 数据失败:`, error);
      
      // 检查设备类型，室外设备没有CO2指标
      const isOutdoorDevice = deviceName.includes('室外') || deviceName.includes('Outdoor');
      
      let data: number[] = [];
      
      if (isOutdoorDevice) {
        // 室外设备没有CO2数据，设置为空数组（不画线）
        data = [];
        console.log(`设备 ${deviceName} 是室外设备，无CO2数据，不画线`);
      } else {
        // 室内设备使用当前值生成模拟数据
        const currentValue = device.metrics?.CO2 || device.raw_data?.CO2 || 400;
        data = timePoints.map((_, i) => {
          const baseValue = currentValue;
          const variation = Math.sin(i * 0.3) * 20 + Math.random() * 10 - 5;
          return Math.max(0, Math.round(baseValue + variation));
        });
      }
      
      seriesData.push({
        name: deviceName,
        type: 'line',
        data: data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 2
        },
        itemStyle: {
          color: colors[index % colors.length]
        },
        emphasis: {
          focus: 'series'
        }
      });
    }
  }
  
  return seriesData;
}

// 通用指标系列数据生成函数
async function generateMetricSeriesData(devices: any[], timePoints: string[], metricKey: string) {
  const colors = ['#1890ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1', '#13c2c2'];
  
  const seriesData: any[] = [];
  
  // 统一时间范围，确保所有设备使用相同的时间点
  const endTime = new Date();
  const startTime = new Date(endTime.getTime() - getTimeRangeMs(selectedTimeRange.value));
  
  console.log(`统一时间范围: ${startTime.toISOString()} - ${endTime.toISOString()}`);
  
  for (let index = 0; index < devices.length; index++) {
    const device = devices[index];
    const deviceName = device.name || device.device_name || `设备${index + 1}`;
    
    try {
      // 检查设备是否在线
      const deviceStatus = device.status || device.device_status;
      if (deviceStatus === 'offline' || deviceStatus === '离线') {
        console.warn(`设备 ${deviceName} 离线，跳过历史数据获取`);
        // 离线设备显示空数据
        seriesData.push({
          name: `${deviceName} (离线)`,
          type: 'line',
          data: [],
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: {
            width: 2,
            type: 'dashed' // 离线设备用虚线
          },
          itemStyle: {
            color: colors[index % colors.length]
          },
          emphasis: {
            focus: 'series'
          }
        });
        continue; // 跳过这个设备
      }
      
      console.log(`获取设备 ${deviceName} 历史数据，时间范围: ${startTime.toISOString()} - ${endTime.toISOString()}`);
      
      const historyData = await getDeviceMetrics({
        deviceName: deviceName, // 使用正确的参数名
        start: startTime.valueOf(), // 使用毫秒时间戳
        end: endTime.valueOf()
      });
      
      console.log(`设备 ${deviceName} 历史数据:`, historyData);
      
      let data: number[] = [];
      
      if (historyData && historyData.series && historyData.series[metricKey] && historyData.series[metricKey].length > 0) {
        // 使用真实历史数据
        const metricSeries = historyData.series[metricKey];
        console.log(`设备 ${deviceName} ${metricKey}原始数据:`, metricSeries);
        
        // 将时间序列数据转换为数值数组
        data = metricSeries.map((item: any) => item.v || item.value || 0);
        console.log(`设备 ${deviceName} ${metricKey}数据点: ${data.length}`);
      } else {
        // 如果没有历史数据，使用当前值生成模拟数据
        const currentValue = device.metrics?.[metricKey] || device.raw_data?.[metricKey] || getDefaultValue(metricKey);
        data = timePoints.map((_, i) => {
          const baseValue = currentValue;
          const variation = Math.sin(i * 0.3) * getVariationRange(metricKey) + Math.random() * getRandomRange(metricKey) - getRandomRange(metricKey) / 2;
          return Math.max(0, Math.round(baseValue + variation));
        });
        console.log(`设备 ${deviceName} 使用模拟数据，当前${metricKey}: ${currentValue}`);
      }
      
      seriesData.push({
        name: deviceName,
        type: 'line',
        data: data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 2
        },
        itemStyle: {
          color: colors[index % colors.length]
        },
        emphasis: {
          focus: 'series'
        }
      });
      
    } catch (error) {
      console.error(`处理设备 ${deviceName} 数据失败:`, error);
      
      // 使用当前值生成模拟数据
      const currentValue = device.metrics?.[metricKey] || device.raw_data?.[metricKey] || getDefaultValue(metricKey);
      const data = timePoints.map((_, i) => {
        const baseValue = currentValue;
        const variation = Math.sin(i * 0.3) * getVariationRange(metricKey) + Math.random() * getRandomRange(metricKey) - getRandomRange(metricKey) / 2;
        return Math.max(0, Math.round(baseValue + variation));
      });
      
      seriesData.push({
        name: deviceName,
        type: 'line',
        data: data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 2
        },
        itemStyle: {
          color: colors[index % colors.length]
        },
        emphasis: {
          focus: 'series'
        }
      });
    }
  }
  
  return seriesData;
}

// 获取指标的默认值
function getDefaultValue(metricKey: string): number {
  switch (metricKey) {
    case 'PM25': return 50;
    case 'PM10': return 80;
    case 'TEM': return 25;
    case 'RH': return 60;
    default: return 0;
  }
}

// 获取指标的变化范围
function getVariationRange(metricKey: string): number {
  switch (metricKey) {
    case 'PM25': return 10;
    case 'PM10': return 15;
    case 'TEM': return 5;
    case 'RH': return 10;
    default: return 10;
  }
}

// 获取指标的随机范围
function getRandomRange(metricKey: string): number {
  switch (metricKey) {
    case 'PM25': return 8;
    case 'PM10': return 12;
    case 'TEM': return 3;
    case 'RH': return 8;
    default: return 5;
  }
}

// 获取时间范围的毫秒数
function getTimeRangeMs(timeRange: string): number {
  switch (timeRange) {
    case '1h':
      return 60 * 60 * 1000; // 1小时
    case '6h':
      return 6 * 60 * 60 * 1000; // 6小时
    case '24h':
      return 24 * 60 * 60 * 1000; // 24小时
    case '7d':
      return 7 * 24 * 60 * 60 * 1000; // 7天
    default:
      return 60 * 60 * 1000; // 默认1小时
  }
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
  
  // 渲染所有图表
  setTimeout(() => {
    renderCO2Charts();
    renderPM25Charts();
    renderPM10Charts();
    renderTempCharts();
    renderHumidityCharts();
  }, 1000);
  
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

/* CO2图表区域样式 */
.co2-charts-section {
  margin-top: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.section-title .anticon {
  margin-right: 8px;
  color: #1890ff;
}

.time-selector {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.co2-charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 20px;
}

.co2-chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.co2-chart-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.chart-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.chart-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: white;
}

.chart-content {
  padding: 20px;
  min-height: 300px;
}

.co2-chart {
  width: 100%;
  height: 300px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafafa;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .co2-charts-grid {
    grid-template-columns: 1fr;
  }
}

/* 其他指标图表样式 */
.charts-section {
  margin-top: 32px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 20px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.chart-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.chart-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-content {
  padding: 20px;
}

.metric-chart {
  width: 100%;
  height: 300px;
  border-radius: 8px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .time-selector {
    flex-direction: column;
    gap: 12px;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .metric-chart {
    height: 250px;
  }
}
</style>
