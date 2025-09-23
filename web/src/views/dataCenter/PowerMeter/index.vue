<template>
  <div class="power-meter">
    <a-card title="电表设备概览" class="mb-4">
      <a-row :gutter="16" class="mb-4">
        <a-col :span="6"><a-statistic title="设备总数" :value="deviceStats.total_devices || 0" /></a-col>
        <a-col :span="6"><a-statistic title="在线设备" :value="deviceStats.status_dist?.online || 0" /></a-col>
        <a-col :span="6"><a-statistic title="离线设备" :value="deviceStats.status_dist?.offline || 0" /></a-col>
        <a-col :span="6"><a-statistic title="总用电量" :value="totalPowerConsumption" suffix="kWh" :precision="2" /></a-col>
      </a-row>
      
      <DeviceChart 
        :device-options="powerMeterOptions" 
        device-type="power"
        ref="deviceChartRef"
      />
    </a-card>

    <!-- 电表设备列表 -->
    <a-card title="电表设备列表" class="mb-4">
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
          <template v-if="column.key === 'powerConsumption'">
            <a-statistic 
              :value="record.powerConsumption || 0" 
              suffix="kWh" 
              :precision="2"
              :value-style="{ fontSize: '14px' }"
            />
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

    <!-- 实时用电监控 -->
    <a-card title="实时用电监控" class="mb-4">
      <a-row :gutter="16">
        <a-col :span="12" v-for="device in powerMeterDevices" :key="device.name">
          <a-card size="small" :title="device.name" class="device-card">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-statistic 
                  title="当前功率" 
                  :value="device.metrics?.power || 0" 
                  suffix="kW" 
                  :precision="2"
                  :value-style="{ color: '#1890ff' }"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic 
                  title="累计用电" 
                  :value="device.metrics?.totalPower || 0" 
                  suffix="kWh" 
                  :precision="2"
                  :value-style="{ color: '#52c41a' }"
                />
              </a-col>
            </a-row>
            <a-row :gutter="16" class="mt-2">
              <a-col :span="12">
                <a-statistic 
                  title="电压" 
                  :value="device.metrics?.voltage || 0" 
                  suffix="V" 
                  :precision="1"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic 
                  title="电流" 
                  :value="device.metrics?.current || 0" 
                  suffix="A" 
                  :precision="2"
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

    <!-- 用电统计图表 -->
    <a-card title="用电统计" class="mb-4">
      <a-row :gutter="16">
        <a-col :span="12">
          <div class="chart-container">
            <div class="chart-title">日用电量趋势</div>
            <div ref="dailyPowerChartRef" class="chart"></div>
          </div>
        </a-col>
        <a-col :span="12">
          <div class="chart-container">
            <div class="chart-title">设备用电占比</div>
            <div ref="powerDistributionChartRef" class="chart"></div>
          </div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import dayjs from 'dayjs';
import { useMessage } from '/@/hooks/web/useMessage';
import { useECharts } from '/@/hooks/web/useECharts';
import { getDeviceStats } from '/@/views/dashboard/api';
import DeviceChart from '../components/DeviceChart.vue';

const { createMessage } = useMessage();

// 图表引用
const dailyPowerChartRef = ref<HTMLDivElement | null>(null);
const powerDistributionChartRef = ref<HTMLDivElement | null>(null);
const { setOptions: setDailyPowerChart } = useECharts(dailyPowerChartRef);
const { setOptions: setPowerDistributionChart } = useECharts(powerDistributionChartRef);

// 响应式数据
const deviceStats = ref<any>({ total_devices: 0, status_dist: {}, devices: [] });
const deviceList = ref<any[]>([]);
const powerMeterDevices = ref<any[]>([]);

// 电表设备选项
const powerMeterOptions = [
  { label: '07室电表', value: '07室电表' },
  { label: '08室电表', value: '08室电表' },
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
    title: '累计用电量',
    dataIndex: 'powerConsumption',
    key: 'powerConsumption',
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
const totalPowerConsumption = computed(() => {
  return powerMeterDevices.value.reduce((sum, device) => {
    return sum + (device.metrics?.totalPower || 0);
  }, 0);
});

// 获取设备统计信息
async function fetchDeviceStats() {
  try {
    const res = await getDeviceStats();
    deviceStats.value = res;
    
    // 过滤电表设备
    const allDevices = res.devices || [];
    const powerDevices = allDevices.filter((device: any) => 
      device.name && device.name.includes('电表')
    );
    
    deviceList.value = powerDevices.map((device: any) => ({
      name: device.name,
      type: '电表',
      status: device.status || 'offline',
      powerConsumption: Math.random() * 1000, // 模拟累计用电量
      lastUpdate: device.lastUpdate || null,
    }));
    
    // 初始化实时监控数据
    powerMeterDevices.value = powerDevices.map((device: any) => ({
      name: device.name,
      status: device.status || 'offline',
      lastUpdate: device.lastUpdate || null,
      metrics: {
        power: 0,
        totalPower: 0,
        voltage: 0,
        current: 0,
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
  powerMeterDevices.value.forEach(device => {
    if (device.status === 'online') {
      // 模拟实时数据更新
      device.metrics = {
        power: Math.round((Math.random() * 5) * 100) / 100, // 0-5kW
        totalPower: Math.round((Math.random() * 1000) * 100) / 100, // 累计用电量
        voltage: Math.round((220 + Math.random() * 20) * 10) / 10, // 220-240V
        current: Math.round((Math.random() * 20) * 100) / 100, // 0-20A
      };
      device.lastUpdate = new Date().getTime();
    }
  });
}

// 初始化图表
function initCharts() {
  // 日用电量趋势图
  setDailyPowerChart({
    title: {
      text: '近7天用电量',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    },
    yAxis: {
      type: 'value',
      name: '用电量(kWh)',
    },
    series: [
      {
        name: '用电量',
        type: 'line',
        data: [120, 132, 101, 134, 90, 230, 210],
        smooth: true,
        areaStyle: {
          opacity: 0.3,
        },
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
      formatter: '{a} <br/>{b}: {c} ({d}%)',
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
        data: [
          { value: 335, name: '07室电表' },
          { value: 310, name: '08室电表' },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  });
}

onMounted(async () => {
  await fetchDeviceStats();
  initCharts();
  
  // 每30秒更新一次实时数据
  setInterval(updateRealTimeData, 30000);
});
</script>

<style scoped>
.power-meter {
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

.chart-container {
  height: 300px;
}

.chart-title {
  text-align: center;
  font-weight: bold;
  margin-bottom: 16px;
  color: #333;
}

.chart {
  width: 100%;
  height: 250px;
}
</style>
