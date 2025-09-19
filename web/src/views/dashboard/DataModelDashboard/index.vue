<template>
  <div class="p-4">
    <!-- 顶部统计卡 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :span="6"><a-card><a-statistic title="总模型数" :value="overviewData.totalCount" /></a-card></a-col>
      <a-col :span="6"><a-card><a-statistic title="已建立" :value="overviewData.establishedCount" /></a-card></a-col>
      <a-col :span="6"><a-card><a-statistic title="未建立" :value="overviewData.unestablishedCount" /></a-card></a-col>
      <a-col :span="6"><a-card><a-statistic title="可接口" :value="overviewData.interfaceCount" /></a-card></a-col>
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

    <!-- 物联网设备概览与多指标折线图（单轴） -->
    <a-card title="物联网设备概览" class="mb-4">
      <a-row :gutter="16" class="mb-2">
        <a-col :span="6"><a-statistic title="设备总数" :value="displayTotalDevices" /></a-col>
        <a-col :span="6"><a-statistic title="在线设备" :value="deviceStats.status_dist?.online || 0" /></a-col>
        <a-col :span="6"><a-statistic title="离线设备" :value="deviceStats.status_dist?.offline || 0" /></a-col>
      </a-row>
      <a-row :gutter="16">
        
        <a-col :span="24">
          <div class="toolbar">
            <a-select v-model:value="selectedDevice" style="width: 220px" :options="staticDeviceOptions" placeholder="选择设备" @change="fetchAndRenderDeviceMetrics" />
            <a-range-picker v-model:value="selectedRange" style="margin-left: 12px" :show-time="{ format: 'HH:mm' }" format="YYYY-MM-DD HH:mm" @change="fetchAndRenderDeviceMetrics" />
            <a-segmented
              style="margin-left: 12px;"
              :options="[
                { label: '今日', value: 'today' },
                { label: '近7天', value: '7d' },
                { label: '近30天', value: '30d' },
                { label: '近90天', value: '90d' },
                { label: '本周', value: 'week' },
                { label: '本月', value: 'month' },
              ]"
              @change="onQuickRangeChange"
            />
            <a-switch style="margin-left: 12px;" v-model:checked="showAvgLine" checked-children="均值" un-checked-children="均值" @change="fetchAndRenderDeviceMetrics" />
            <a-switch style="margin-left: 8px;" v-model:checked="showMaxLine" checked-children="最大" un-checked-children="最大" @change="fetchAndRenderDeviceMetrics" />
            <span style="margin-left:12px; color:#666;">最新数据：{{ latestDataTime || '—' }}</span>
            <a-switch style="margin-left: 12px;" v-model:checked="autoRefresh" checked-children="自动刷新" un-checked-children="手动" />
            <a-select v-model:value="refreshMinutes" style="width:90px; margin-left:8px;" :disabled="!autoRefresh">
              <a-select-option :value="1">1分钟</a-select-option>
              <a-select-option :value="5">5分钟</a-select-option>
              <a-select-option :value="15">15分钟</a-select-option>
            </a-select>
          </div>
          <div ref="deviceLineRef" class="chart"></div>
          <div v-if="noDataHint" class="hint">{{ noDataHint }}</div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, type Ref, computed, watch } from 'vue';
import dayjs, { type Dayjs } from 'dayjs';
import { useECharts } from '/@/hooks/web/useECharts';
import { useMessage } from '/@/hooks/web/useMessage';
import { getDataModelOverview, getDataModelTypeStats, getDataModelCreationTrend, getDataModelDataflow, getDeviceStats, getDeviceMetrics } from '../api';
import StockKlineCard from '/@/views/dataManage/dataModel/components/StockKlineCard.vue';
import DataFlowSankey from '../components/DataFlowSankey.vue';

const { createMessage } = useMessage();

// refs & echarts instances
const typeChartRef = ref<HTMLDivElement | null>(null);
const statusChartRef = ref<HTMLDivElement | null>(null);
const trendChartRef = ref<HTMLDivElement | null>(null);
const deviceLineRef = ref<HTMLDivElement | null>(null);

const { setOptions: setTypeChart } = useECharts(typeChartRef as Ref<HTMLDivElement>);
const { setOptions: setStatusChart } = useECharts(statusChartRef as Ref<HTMLDivElement>);
const { setOptions: setTrendChart } = useECharts(trendChartRef as Ref<HTMLDivElement>);
const { setOptions: setDeviceLine } = useECharts(deviceLineRef as Ref<HTMLDivElement>);

// state
const overviewData = ref({ totalCount: 0, establishedCount: 0, unestablishedCount: 0, interfaceCount: 0 });
const deviceStats = ref<any>({ total_devices: 0, status_dist: {}, devices: [] });
const latestDataTime = ref<string>('');
const autoRefresh = ref<boolean>(false);
const refreshMinutes = ref<number>(5);
let refreshTimer: any = null;
const displayTotalDevices = computed(() => {
  const list = (deviceStats.value?.devices || deviceStats.value?.data?.devices || []) as any[];
  if (Array.isArray(list) && list.length) {
    const ids = new Set<string>();
    list.forEach((d: any) => {
      const id = d.device_id || d.device_num || d.id;
      if (id) ids.add(String(id));
    });
    return ids.size;
  }
  // 兜底：按固定映射应为 5 台
  return 5;
});
// 固定显示顺序的设备名称（来自你的映射）
const staticDeviceNames = ['07室环境监测', '08室环境监测', '09室环境监测', '08室电表', '07室电表'];
const staticDeviceOptions = staticDeviceNames.map((n) => ({ label: n, value: n }));
// 固定映射（如需后续联动可启用）
const selectedDevice = ref<string | undefined>(undefined);
const selectedRange = ref<[Dayjs, Dayjs]>([dayjs().startOf('day'), dayjs().endOf('day')]);
const showAvgLine = ref<boolean>(false);
const showMaxLine = ref<boolean>(false);
const noDataHint = ref<string>('');

function onQuickRangeChange(val: string) {
  const now = dayjs();
  if (val === 'today') selectedRange.value = [now.startOf('day'), now.endOf('day')];
  else if (val === '7d') selectedRange.value = [now.subtract(7, 'day').startOf('day'), now.endOf('day')];
  else if (val === '30d') selectedRange.value = [now.subtract(30, 'day').startOf('day'), now.endOf('day')];
  else if (val === '90d') selectedRange.value = [now.subtract(90, 'day').startOf('day'), now.endOf('day')];
  else if (val === 'week') selectedRange.value = [now.startOf('week'), now.endOf('week')];
  else if (val === 'month') selectedRange.value = [now.startOf('month'), now.endOf('month')];
  fetchAndRenderDeviceMetrics();
}

// （删除）表格与日期格式化相关逻辑

// renderers
function renderModelCharts(typeStats: any[], trend: any[]) {
  // 类型分布 - 饼图
  const typeData = (typeStats || []).map((i) => ({ name: i.type, value: i.count }));
  setTypeChart({ 
    tooltip: { 
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    }, 
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [{ 
      type: 'pie', 
      radius: ['40%', '70%'], 
      center: ['60%', '50%'],
      data: typeData,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }] 
  });

  // 状态分布 - 环形图
  const statusData = [
    { name: '已建立', value: overviewData.value.establishedCount },
    { name: '未建立', value: overviewData.value.unestablishedCount },
  ];
  const totalStatus = statusData.reduce((sum, item) => sum + item.value, 0);
  setStatusChart({ 
    tooltip: { 
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [{ 
      type: 'pie', 
      radius: ['50%', '70%'],
      center: ['60%', '50%'],
      data: statusData,
      label: {
        show: true,
        formatter: '{b}\n{d}%'
      },
      labelLine: {
        show: true
      }
    }],
    graphic: {
      type: 'text',
      left: 'center',
      top: 'center',
      style: {
        text: totalStatus.toString(),
        fill: '#333',
        fontSize: 20,
        fontWeight: 'bold'
      }
    }
  });

  // 创建趋势 - 面积图
  const trendX = (trend || []).map((i) => {
    if (i.year && i.month) {
      return `${i.year}-${String(i.month).padStart(2, '0')}`;
    }
    return i.date || `${i.year}-${i.month}`;
  });
  const trendY = (trend || []).map((i) => i.count);
  setTrendChart({
    tooltip: { 
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: { 
      left: 30, 
      right: 20, 
      top: 20, 
      bottom: 30,
      containLabel: true
    },
    xAxis: { 
      type: 'category', 
      data: trendX,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: { 
      type: 'value',
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [{ 
      type: 'line', 
      smooth: true, 
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 6,
      areaStyle: {
        opacity: 0.3
      },
      lineStyle: {
        width: 3
      },
      data: trendY,
      emphasis: {
        focus: 'series'
      }
    }]
  });
}

// 删除设备优先指标柱状图

// data loaders
async function fetchOverview() {
  const [overviewRes, typeStatsRes, trendRes] = await Promise.all([
    getDataModelOverview(),
    getDataModelTypeStats(),
    getDataModelCreationTrend(),
  ]);
  overviewData.value = {
    totalCount: overviewRes.total || 0,
    establishedCount: overviewRes.established || 0,
    unestablishedCount: overviewRes.unestablished || 0,
    interfaceCount: overviewRes.interfaceCount || 0,
  };
  renderModelCharts(typeStatsRes || [], trendRes || []);
}

// （删除）获取最近创建的模型逻辑

async function fetchDeviceStatsAndList() {
  const [statsRes] = await Promise.allSettled([getDeviceStats()]);

  const statsOk = statsRes.status === 'fulfilled' ? statsRes.value : null;

  // 统计数据
  deviceStats.value = statsOk || { total_devices: 0, status_dist: {}, devices: [] };
  // 不再依赖后端列表，改用固定选项

  // 已移除柱状图渲染

  // 使用固定设备列表；若当前选择无效（或为“温度”等），重置为第一个
  const staticValues = new Set(staticDeviceOptions.map((o) => o.value));
  if (!selectedDevice.value || !staticValues.has(selectedDevice.value)) {
    if (staticDeviceOptions.length) selectedDevice.value = staticDeviceOptions[0].value;
  }
}

function extendStepToRange(seriesData: [number, number][], startMs: number, endMs: number) {
  if (!seriesData.length) return seriesData;
  const first = seriesData[0][1];
  const last = seriesData[seriesData.length - 1][1];
  const extended = [...seriesData];
  extended.unshift([startMs, first]);
  extended.push([endMs, last]);
  return extended;
}

async function fetchAndRenderDeviceMetrics() {
  if (!selectedDevice.value || !selectedRange.value) return;
  // 防止误把“温度/湿度/CO2/PM”当作设备名传给后端
  const metricNames = new Set(['温度', '湿度', '二氧化碳', 'PM2.5', 'PM10', 'CO2', 'TEM', 'RH', 'PM25']);
  if (metricNames.has(String(selectedDevice.value))) {
    if (staticDeviceOptions.length) selectedDevice.value = staticDeviceOptions[0].value;
  }
  const [start, end] = selectedRange.value;
  const startMs = start.valueOf();
  const endMs = end.valueOf();
  console.log('调用 device-metrics:', { deviceName: selectedDevice.value, start: startMs, end: endMs });
  let res = await getDeviceMetrics({ deviceName: selectedDevice.value, start: startMs, end: endMs });
  console.log('device-metrics response:', res);

  const metricOrder = ['CO2', 'PM10', 'PM25', 'TEM', 'RH', 'power'];
  let rawSeries: any[] = [];
  const s1 = (res as any)?.series;
  const s2 = (res as any)?.data?.series;
  const s = s1 ?? s2;
  if (Array.isArray(s)) {
    rawSeries = s;
  } else if (s && typeof s === 'object') {
    // 兼容 { metricName: [[ts,val],...] } 或 { metricName: [{ts,value},...] }
    const pickTs = (obj: any) => obj?.ts ?? obj?.time ?? obj?.timestamp ?? obj?.date ?? obj?.t ?? obj?.x ?? obj?.[0];
    const pickVal = (obj: any) => obj?.value ?? obj?.val ?? obj?.v ?? obj?.y ?? obj?.avg ?? obj?.mean ?? obj?.data ?? obj?.[1];
    rawSeries = Object.entries(s).map(([metric, arr]: any) => {
      const points = (arr || []).map((p: any) =>
        Array.isArray(p)
          ? { ts: p[0], value: p[1] }
          : { ts: pickTs(p), value: pickVal(p) }
      );
      return { metric, points };
    });
  }

  // 若本时间段没有任何点位，自动回退查询近90天的数据
  const totalPoints = rawSeries.reduce((sum, m: any) => sum + ((m.points || []).length), 0);
  if (totalPoints === 0) {
    const altStartMs = dayjs(endMs).subtract(90, 'day').valueOf();
    console.log('无数据，回退90天重试:', { deviceName: selectedDevice.value, start: altStartMs, end: endMs });
    res = await getDeviceMetrics({ deviceName: selectedDevice.value, start: altStartMs, end: endMs });
    const s1b = (res as any)?.series;
    const s2b = (res as any)?.data?.series;
    const sb = s1b ?? s2b;
    rawSeries = [];
    if (Array.isArray(sb)) rawSeries = sb;
    else if (sb && typeof sb === 'object') {
      const pickTs = (obj: any) => obj?.ts ?? obj?.time ?? obj?.timestamp ?? obj?.date ?? obj?.t ?? obj?.x ?? obj?.[0];
      const pickVal = (obj: any) => obj?.value ?? obj?.val ?? obj?.v ?? obj?.y ?? obj?.avg ?? obj?.mean ?? obj?.data ?? obj?.[1];
      rawSeries = Object.entries(sb).map(([metric, arr]: any) => {
        const points = (arr || []).map((p: any) => Array.isArray(p) ? { ts: p[0], value: p[1] } : { ts: pickTs(p), value: pickVal(p) });
        return { metric, points };
      });
    }
  }

  const unitsMap: Record<string, string> = ((res as any)?.units || (res as any)?.data?.units || {}) as any;

  // 仅渲染有数据的指标
  const series = rawSeries
    .sort((a: any, b: any) => metricOrder.indexOf(a.metric) - metricOrder.indexOf(b.metric))
    .filter((m: any) => Array.isArray(m.points) && m.points.length > 0)
    .map((m: any) => {
      const base = {
        name: m.metric,
        type: 'line' as const,
        smooth: true,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 3,
        areaStyle: { opacity: 0.08 },
        data: extendStepToRange((m.points || []).map((p: any) => [p.ts, p.value]), startMs, endMs),
        emphasis: { focus: 'series' as any },
        sampling: 'lttb' as any,
      } as any;

      // 若为“07室电表”的 power 序列：显示每个点数值标签，并标注值为0的点
      const highlightMeters = new Set(['07室电表', '08室电表']);
      if (highlightMeters.has(String(selectedDevice.value)) && String(m.metric).toLowerCase() === 'power') {
        base.symbolSize = 6;
        base.label = {
          show: true,
          color: '#333',
          fontSize: 10,
          formatter: (params: any) => {
            const d = Array.isArray(params?.data) ? params.data[1] : (params?.data?.value ?? params?.data);
            return d === 0 || d === '0' ? '0' : String(d ?? '');
          },
        } as any;
        try {
          const zeroMarks = (m.points || [])
            .filter((p: any) => Number(p?.value) === 0)
            .map((p: any) => ({ coord: [p.ts, 0], value: 0, itemStyle: { color: '#d4380d' }, symbolSize: 12 }));
          if (zeroMarks.length) {
            base.markPoint = { data: zeroMarks } as any;
          }
        } catch {}
      }

      return base;
    });

  // 计算参考线数据
  const flatPoints: number[] = [];
  rawSeries.forEach((m: any) => (m.points || []).forEach((p: any) => { if (typeof p.value === 'number') flatPoints.push(p.value); }));
  // 最新时间显示
  const allTs: number[] = [];
  rawSeries.forEach((m:any)=> (m.points||[]).forEach((p:any)=> { if(p && p.ts) allTs.push(p.ts);}));
  if (allTs.length) {
    const maxTs = Math.max(...allTs);
    latestDataTime.value = dayjs(maxTs).format('YYYY-MM-DD HH:mm');
  }
  const avg = flatPoints.length ? flatPoints.reduce((a, b) => a + b, 0) / flatPoints.length : undefined;
  const max = flatPoints.length ? Math.max(...flatPoints) : undefined;

  setDeviceLine({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const timeStr = dayjs(params[0].axisValue).format('YYYY-MM-DD HH:mm');
        const dev = String(selectedDevice.value || '');
        const lines = params.map((p) => {
          const metric = p.seriesName;
          const val = Array.isArray(p.data) ? p.data[1] : p.data?.value ?? p.data;
          const unit = unitsMap?.[metric] ? ` ${unitsMap[metric]}` : '';
          return `${metric}｜${val}${unit}｜${dev}`;
        });
        return `${timeStr}<br/>` + lines.join('<br/>');
      },
    },
    legend: { type: 'scroll' },
    grid: { left: 48, right: 18, top: 28, bottom: 56, containLabel: true },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 16 as any, bottom: 12 as any, brushSelect: false },
    ],
    xAxis: { type: 'time', min: startMs, max: endMs },
    yAxis: {
      type: 'value',
      boundaryGap: ['8%', '18%'] as any,
      scale: true as any,
      axisLabel: { margin: 10 },
    },
    series: (
      series.length ? [
        ...series,
        ...(showAvgLine.value && avg !== undefined ? [{
          name: '均值', type: 'line' as const, data: [[startMs, avg], [endMs, avg]], symbol: 'none', lineStyle: { type: 'dashed' as const, color: '#999' }, tooltip: { show: false }, emphasis: { disabled: true } as any,
        }] : []),
        ...(showMaxLine.value && max !== undefined ? [{
          name: '最大', type: 'line' as const, data: [[startMs, max], [endMs, max]], symbol: 'none', lineStyle: { type: 'dotted' as const, color: '#c00' }, tooltip: { show: false }, emphasis: { disabled: true } as any,
        }] : []),
      ] : []
    ),
  });

  noDataHint.value = series.length === 0 ? '当前时段无数据，已自动回退近90天再试。' : '';
}

onMounted(async () => {
  try {
    await Promise.all([fetchOverview(), fetchDeviceStatsAndList()]);
    // 数据流向：动态获取并渲染
    try {
      await getDataModelDataflow();
      // 如需使用动态数据：将返回值存入 dataflowNodes/dataflowLinks，并传给 DataFlowSankey 组件
    } catch (e) {
      console.warn('数据流向获取失败，使用默认示例');
    }
    await fetchAndRenderDeviceMetrics();

    // 自动刷新定时器
    const setupTimer = () => {
      if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
      if (autoRefresh.value) {
        const ms = Math.max(1, refreshMinutes.value) * 60 * 1000;
        refreshTimer = setInterval(() => {
          // 将结束时间更新为当前，起点保持与当前窗口同跨度（默认1小时）
          const end = dayjs();
          const start = (selectedRange.value?.[0]) ? end.subtract(end.diff(selectedRange.value[0], 'minute'), 'minute') : end.subtract(60, 'minute');
          selectedRange.value = [start, end] as any;
          fetchAndRenderDeviceMetrics();
        }, ms);
      }
    };
    watch([autoRefresh, refreshMinutes], setupTimer, { immediate: true });
  } catch (e) {
    console.error(e);
    createMessage.error('看板加载失败');
  }
});
</script>

<style scoped>
.p-4 { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.chart { height: 300px; }
.toolbar { display: flex; align-items: center; margin-bottom: 8px; }

/* 新增样式 */
.chart-container {
  position: relative;
  height: 300px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 16px;
  background: #fafafa;
}

.chart-title {
  position: absolute;
  top: 8px;
  left: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  z-index: 10;
}

.table-container {
  margin-top: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;
}

.table-title {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
  background: #fff;
  border-radius: 6px 6px 0 0;
}

:deep(.ant-table) {
  background: transparent;
}

:deep(.ant-table-thead > tr > th) {
  background: #f5f5f5;
  border-bottom: 1px solid #e8e8e8;
}

:deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background: #f5f5f5;
}
</style>
