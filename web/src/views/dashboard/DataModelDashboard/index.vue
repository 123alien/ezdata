<template>
  <div class="p-4">
    <!-- 顶部统计卡 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :span="6"><a-card><a-statistic title="总模型数" :value="overviewData.totalCount" /></a-card></a-col>
      <a-col :span="6"><a-card><a-statistic title="已建立" :value="overviewData.establishedCount" /></a-card></a-col>
      <a-col :span="6"><a-card><a-statistic title="未建立" :value="overviewData.unestablishedCount" /></a-card></a-col>
      <a-col :span="6"><a-card><a-statistic title="可接口" :value="overviewData.interfaceCount" /></a-card></a-col>
    </a-row>

    <!-- 模型分布与趋势 -->
    <a-card title="数据模型分布" class="mb-4">
      <a-row :gutter="16">
        <a-col :span="8"><div ref="typeChartRef" class="chart"></div></a-col>
        <a-col :span="8"><div ref="statusChartRef" class="chart"></div></a-col>
        <a-col :span="8"><div ref="trendChartRef" class="chart"></div></a-col>
      </a-row>
    </a-card>

    <!-- 物联网设备概览与多指标折线图（单轴） -->
    <a-card title="物联网设备概览" class="mb-4">
      <a-row :gutter="16" class="mb-2">
        <a-col :span="6"><a-statistic title="设备总数" :value="deviceStats.total_devices" /></a-col>
        <a-col :span="6"><a-statistic title="在线设备" :value="deviceStats.status_dist?.online || 0" /></a-col>
        <a-col :span="6"><a-statistic title="离线设备" :value="deviceStats.status_dist?.offline || 0" /></a-col>
      </a-row>
      <a-row :gutter="16">
        
        <a-col :span="24">
          <div class="toolbar">
            <a-select v-model:value="selectedDevice" style="width: 220px" :options="staticDeviceOptions" placeholder="选择设备" @change="fetchAndRenderDeviceMetrics" />
            <a-range-picker v-model:value="selectedRange" style="margin-left: 12px" :show-time="{ format: 'HH:mm' }" format="YYYY-MM-DD HH:mm" @change="fetchAndRenderDeviceMetrics" />
          </div>
          <div ref="deviceLineRef" class="chart"></div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, type Ref } from 'vue';
import dayjs, { type Dayjs } from 'dayjs';
import { useECharts } from '/@/hooks/web/useECharts';
import { useMessage } from '/@/hooks/web/useMessage';
import { getDataModelOverview, getDataModelTypeStats, getDataModelCreationTrend, getDeviceStats, getDeviceMetrics } from '../api';

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
// 固定显示顺序的设备名称（来自你的映射）
const staticDeviceNames = ['07室环境监测', '08室环境监测', '09室环境监测', '08室电表', '07室电表'];
const staticDeviceOptions = staticDeviceNames.map((n) => ({ label: n, value: n }));
// 固定映射（如需后续联动可启用）
const selectedDevice = ref<string | undefined>(undefined);
const selectedRange = ref<[Dayjs, Dayjs]>([dayjs().startOf('day'), dayjs().endOf('day')]);

// renderers
function renderModelCharts(typeStats: any[], trend: any[]) {
  const typeData = (typeStats || []).map((i) => ({ name: i.type, value: i.count }));
  setTypeChart({ tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: '60%', data: typeData }] });

  const statusData = [
    { name: '已建立', value: overviewData.value.establishedCount },
    { name: '未建立', value: overviewData.value.unestablishedCount },
  ];
  setStatusChart({ tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: '60%', data: statusData }] });

  const trendX = (trend || []).map((i) => i.date);
  const trendY = (trend || []).map((i) => i.count);
  setTrendChart({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trendX },
    yAxis: { type: 'value' },
    grid: { left: 28, right: 8, top: 24, bottom: 20 },
    series: [{ type: 'line', smooth: true, showSymbol: false, data: trendY }],
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
    .map((m: any) => ({
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
    }));

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
    grid: { left: 48, right: 18, top: 40, bottom: 72, containLabel: true },
    dataZoom: [{ type: 'inside' }, { type: 'slider' }],
    xAxis: { type: 'time', min: startMs, max: endMs },
    yAxis: {
      type: 'value',
      boundaryGap: ['5%', '10%'] as any,
      axisLabel: { margin: 10 },
    },
    series: series.length ? series : [],
  });
}

onMounted(async () => {
  try {
    await Promise.all([fetchOverview(), fetchDeviceStatsAndList()]);
    await fetchAndRenderDeviceMetrics();
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
.chart-title { margin-bottom: 8px; font-weight: 500; }
</style>
