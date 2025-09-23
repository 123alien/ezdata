<template>
  <div class="p-4">
    <!-- 顶部统计卡 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :span="6"><a-statistic title="总模型数" :value="overviewData.totalCount" /></a-col>
      <a-col :span="6"><a-statistic title="已建立" :value="overviewData.establishedCount" /></a-col>
      <a-col :span="6"><a-statistic title="未建立" :value="overviewData.unestablishedCount" /></a-col>
      <a-col :span="6"><a-statistic title="可接口" :value="overviewData.interfaceCount" /></a-col>
    </a-row>

    <!-- 数据模型分布概览 -->
    <a-card title="数据模型分布概览" class="mb-4">
      <!-- 图表区域 -->
      <a-row :gutter="16" class="mb-4">
        <a-col :span="8">
          <div class="chart-container">
            <div class="chart-title">类型分布</div>
            <div ref="typeChartRef" class="chart"></div>
          </div>
        </a-col>
        <a-col :span="8">
          <div class="chart-container">
            <div class="chart-title">状态分布</div>
            <div ref="statusChartRef" class="chart"></div>
          </div>
        </a-col>
        <a-col :span="8">
          <div class="chart-container">
            <div class="chart-title">创建趋势</div>
            <div ref="trendChartRef" class="chart"></div>
          </div>
        </a-col>
      </a-row>
      
      <!-- 数据流向图（移动至此） -->
      <DataFlowSankey title="数据流向图" />
    </a-card>

    <!-- 金融数据（AkShare 股票K线） -->
    <StockKlineCard class="mb-4" />

    <!-- 数据中心入口 -->
    <a-card title="数据中心" class="mb-4">
      <a-row :gutter="16">
        <a-col :span="12">
          <a-card hoverable @click="navigateToEnvironmentMonitoring">
            <template #title>
              <EnvironmentOutlined style="margin-right: 8px;" />
              环境监测设备
            </template>
            <template #extra>
              <a-button type="link">查看详情</a-button>
            </template>
            <p>监控温度、湿度、CO2、PM2.5等环境指标</p>
            <a-statistic title="设备数量" :value="3" />
          </a-card>
        </a-col>
        <a-col :span="12">
          <a-card hoverable @click="navigateToPowerMeter">
            <template #title>
              <ThunderboltOutlined style="margin-right: 8px;" />
              电表设备
            </template>
            <template #extra>
              <a-button type="link">查看详情</a-button>
            </template>
            <p>监控用电量、功率、电压、电流等电力指标</p>
            <a-statistic title="设备数量" :value="2" />
          </a-card>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, type Ref } from 'vue';
import { useECharts } from '/@/hooks/web/useECharts';
import { useMessage } from '/@/hooks/web/useMessage';
import { useRouter } from 'vue-router';
import { getDataModelOverview, getDataModelTypeStats, getDataModelCreationTrend, getDataModelDataflow } from '../api';
import StockKlineCard from '/@/views/dataManage/dataModel/components/StockKlineCard.vue';
import DataFlowSankey from '../components/DataFlowSankey.vue';
import { EnvironmentOutlined, ThunderboltOutlined } from '@ant-design/icons-vue';

const { createMessage } = useMessage();
const router = useRouter();

// refs & echarts instances
const typeChartRef = ref<HTMLDivElement | null>(null);
const statusChartRef = ref<HTMLDivElement | null>(null);
const trendChartRef = ref<HTMLDivElement | null>(null);

const { setOptions: setTypeChart } = useECharts(typeChartRef as Ref<HTMLDivElement>);
const { setOptions: setStatusChart } = useECharts(statusChartRef as Ref<HTMLDivElement>);
const { setOptions: setTrendChart } = useECharts(trendChartRef as Ref<HTMLDivElement>);

// 响应式数据
const overviewData = ref({ totalCount: 0, establishedCount: 0, unestablishedCount: 0, interfaceCount: 0 });

// 导航函数
function navigateToEnvironmentMonitoring() {
  router.push('/data-center/environment-monitoring');
}

function navigateToPowerMeter() {
  router.push('/data-center/power-meter');
}

// 获取概览数据
async function fetchOverview() {
  try {
    const res = await getDataModelOverview();
    overviewData.value = res;
  } catch (error) {
    console.error('获取概览数据失败:', error);
  }
}

// 获取类型分布数据
async function fetchTypeStats() {
  try {
    const res = await getDataModelTypeStats();
    const data = res.map((item: any) => ({ name: item.type, value: item.count }));
    
    setTypeChart({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        name: '类型分布',
        type: 'pie',
        radius: '50%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    });
  } catch (error) {
    console.error('获取类型统计失败:', error);
  }
}

// 获取状态分布数据
async function fetchStatusStats() {
  try {
    const res = await getDataModelTypeStats();
    const data = res.map((item: any) => ({ name: item.status, value: item.count }));
    
    setStatusChart({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        name: '状态分布',
        type: 'pie',
        radius: '50%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    });
  } catch (error) {
    console.error('获取状态统计失败:', error);
  }
}

// 获取创建趋势数据
async function fetchCreationTrend() {
  try {
    const res = await getDataModelCreationTrend();
    const dates = res.map((item: any) => item.date);
    const counts = res.map((item: any) => item.count);
    
    setTrendChart({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        name: '创建数量',
        type: 'line',
        data: counts,
        smooth: true,
        areaStyle: {
          opacity: 0.3
        }
      }]
    });
  } catch (error) {
    console.error('获取创建趋势失败:', error);
  }
}

onMounted(async () => {
  try {
    await Promise.all([fetchOverview(), fetchTypeStats(), fetchStatusStats(), fetchCreationTrend()]);
    
    // 数据流向：动态获取并渲染
    try {
      await getDataModelDataflow();
      // 如需使用动态数据：将返回值存入 dataflowNodes/dataflowLinks，并传给 DataFlowSankey 组件
    } catch (e) {
      console.warn('数据流向获取失败，使用默认示例');
    }
  } catch (error) {
    console.error('初始化失败:', error);
    createMessage.error('数据加载失败');
  }
});
</script>

<style scoped>
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