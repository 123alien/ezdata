<template>
  <div class="environment-monitoring">
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

    <!-- 实时数据监控 -->
    <a-card title="实时数据监控" class="mb-4">
      <a-row :gutter="16">
        <a-col :span="8" v-for="device in environmentDevices" :key="device.name">
          <a-card size="small" :title="device.name" class="device-card">
            <a-row :gutter="8">
              <a-col :span="12">
                <a-statistic 
                  title="温度" 
                  :value="device.metrics?.TEM || 0" 
                  suffix="℃" 
                  :precision="1"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic 
                  title="湿度" 
                  :value="device.metrics?.RH || 0" 
                  suffix="%" 
                  :precision="1"
                />
              </a-col>
            </a-row>
            <a-row :gutter="8" class="mt-2">
              <a-col :span="12">
                <a-statistic 
                  title="CO2" 
                  :value="device.metrics?.CO2 || 0" 
                  suffix="ppm" 
                  :precision="0"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic 
                  title="PM2.5" 
                  :value="device.metrics?.PM25 || 0" 
                  suffix="μg/m³" 
                  :precision="1"
                />
              </a-col>
            </a-row>
            <div class="device-status">
              <a-tag :color="device.status === 'online' ? 'green' : 'red'" size="small">
                {{ device.status === 'online' ? '在线' : '离线' }}
              </a-tag>
              <span class="last-update">
                {{ device.lastUpdate ? dayjs(device.lastUpdate).format('HH:mm:ss') : '—' }}
              </span>
            </div>
          </a-card>
        </a-col>
      </a-row>
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
const deviceStats = ref<any>({ total_devices: 0, status_dist: {}, devices: [] });
const deviceList = ref<any[]>([]);
const environmentDevices = ref<any[]>([]);

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
      device.device_name && (device.device_name.includes('温度') || device.device_name.includes('湿度') || device.device_name.includes('CO2') || device.device_name.includes('PM'))
    );
    
    deviceList.value = envDevices.map((device: any) => ({
      name: device.device_name,
      type: '环境监测',
      status: device.status || 'offline',
      lastUpdate: device.last_update || null,
    }));
    
    // 初始化实时监控数据
    environmentDevices.value = envDevices.map((device: any) => ({
      name: device.device_name,
      status: device.status || 'offline',
      lastUpdate: device.last_update || null,
      metrics: {
        TEM: device.raw_data?.factor_code === 'TEM' ? device.raw_data.factor_value : 0,
        RH: device.raw_data?.factor_code === 'RH' ? device.raw_data.factor_value : 0,
        CO2: device.raw_data?.factor_code === 'CO2' ? device.raw_data.factor_value : 0,
        PM25: device.raw_data?.factor_code === 'PM25' ? device.raw_data.factor_value : 0,
        PM10: device.raw_data?.factor_code === 'PM10' ? device.raw_data.factor_value : 0,
      },
    }));
    
  } catch (error) {
    console.error('获取设备统计失败:', error);
    createMessage.error('获取设备统计失败');
  }
}

// 查看设备详情
function viewDeviceDetail(record: any) {
  createMessage.info(`查看设备详情: ${record.name}`);
  // 这里可以跳转到设备详情页面或打开详情弹窗
}

// 模拟实时数据更新
function updateRealTimeData() {
  environmentDevices.value.forEach(device => {
    if (device.status === 'online') {
      // 模拟实时数据更新
      device.metrics = {
        TEM: Math.round((20 + Math.random() * 10) * 10) / 10,
        RH: Math.round((50 + Math.random() * 30) * 10) / 10,
        CO2: Math.round(400 + Math.random() * 200),
        PM25: Math.round((10 + Math.random() * 20) * 10) / 10,
        PM10: Math.round((15 + Math.random() * 25) * 10) / 10,
      };
      device.lastUpdate = new Date().getTime();
    }
  });
}

onMounted(async () => {
  console.log('环境监测设备组件已挂载');
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
  padding: 16px;
}

.device-card {
  margin-bottom: 16px;
}

.device-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.last-update {
  font-size: 12px;
  color: #999;
}

.mt-2 {
  margin-top: 8px;
}
</style>
