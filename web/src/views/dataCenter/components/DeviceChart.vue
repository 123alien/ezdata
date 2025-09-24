<template>
  <div class="device-chart-container">
    <div class="toolbar">
      <a-select v-model:value="selectedDevice" style="width: 220px" :options="deviceOptions" placeholder="选择设备" @change="fetchAndRenderDeviceMetrics" />
      <a-range-picker v-model:value="selectedRange" style="margin-left: 12px" :show-time="{ format: 'HH:mm' }" format="YYYY-MM-DD HH:mm" @change="fetchAndRenderDeviceMetrics" />
      <a-segmented
        style="margin-left: 12px;"
        :options="[
          { label: '今日', value: 'today' },
          { label: '近7天', value: '7d' },
          { label: '近30天', value: '30d' },
          { label: '小时', value: 'hour' },
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
      <a-button type="primary" style="margin-left: 12px;" @click="exportDeviceData" :loading="exportLoading">
        <template #icon><DownloadOutlined /></template>
        导出数据报表
      </a-button>
    </div>
    <div ref="deviceLineRef" class="chart"></div>
    <div v-if="noDataHint" class="hint">{{ noDataHint }}</div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, type Ref, computed, watch, onUnmounted } from 'vue';
import dayjs, { type Dayjs } from 'dayjs';
import { useECharts } from '/@/hooks/web/useECharts';
import { useMessage } from '/@/hooks/web/useMessage';
import { getDeviceMetrics } from '/@/views/dashboard/api';
import { DownloadOutlined } from '@ant-design/icons-vue';

interface Props {
  deviceOptions: Array<{ label: string; value: string }>;
  deviceType: 'environment' | 'power';
}

const props = defineProps<Props>();

const { createMessage } = useMessage();

// 指标代码到中文名称的映射
const metricNameMap: Record<string, string> = {
  'a01001': '温度',
  'a01002': '湿度', 
  'a01006': '大气压',
  'a01007': '风速',
  'a01008': '风向',
  'a34002': 'PM10',
  'a34004': 'PM2.5',
  'CO2': 'CO2',
  'PM10': 'PM10',
  'PM25': 'PM2.5',
  'TEM': '温度',
  'RH': '湿度',
  'power': '功率'
};

// refs & echarts instances
const deviceLineRef = ref<HTMLDivElement | null>(null);
const { setOptions: setDeviceLine } = useECharts(deviceLineRef as Ref<HTMLDivElement>);

// 响应式数据
const selectedDevice = ref<string | undefined>(undefined);
const selectedRange = ref<[Dayjs, Dayjs]>([dayjs().startOf('day'), dayjs().endOf('day')]);
const showAvgLine = ref<boolean>(false);
const showMaxLine = ref<boolean>(false);
const noDataHint = ref<string>('');
const exportLoading = ref<boolean>(false);
const latestDataTime = ref<string>('');
const autoRefresh = ref<boolean>(false);
const refreshMinutes = ref<number>(5);

let refreshTimer: any = null;

// 监听自动刷新
watch([autoRefresh, refreshMinutes], () => {
  setupTimer();
});

// 组件卸载时清理定时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
});

function onQuickRangeChange(val: string) {
  const now = dayjs();
  if (val === 'today') selectedRange.value = [now.startOf('day'), now.endOf('day')];
  else if (val === '7d') selectedRange.value = [now.subtract(7, 'day').startOf('day'), now.endOf('day')];
  else if (val === '30d') selectedRange.value = [now.subtract(30, 'day').startOf('day'), now.endOf('day')];
  else if (val === 'hour') selectedRange.value = [now.subtract(1, 'hour'), now];
  else if (val === 'week') selectedRange.value = [now.startOf('week'), now.endOf('week')];
  else if (val === 'month') selectedRange.value = [now.startOf('month'), now.endOf('month')];
  fetchAndRenderDeviceMetrics();
}

function extendStepToRange(points: number[][], startMs: number, endMs: number) {
  if (!Array.isArray(points) || points.length === 0) return [];
  const sorted = [...points].sort((a, b) => a[0] - b[0]);
  const result: number[][] = [];
  const seenTimestamps = new Set<number>();
  
  // 添加起始点
  if (sorted.length > 0) {
    const firstVal = sorted[0][1];
    result.push([startMs, firstVal]);
    seenTimestamps.add(startMs);
  }
  
  // 添加实际数据点，避免重复时间戳
  for (const [ts, val] of sorted) {
    if (!seenTimestamps.has(ts)) {
      result.push([ts, val]);
      seenTimestamps.add(ts);
    }
  }
  
  // 添加结束点
  if (sorted.length > 0) {
    const lastVal = sorted[sorted.length - 1][1];
    if (!seenTimestamps.has(endMs)) {
      result.push([endMs, lastVal]);
    }
  }
  
  return result;
}

async function fetchAndRenderDeviceMetrics() {
  if (!selectedDevice.value || !selectedRange.value) return;
  
  const [start, end] = selectedRange.value;
  const startMs = start.valueOf();
  const endMs = end.valueOf();
  console.log('调用 device-metrics:', { deviceName: selectedDevice.value, start: startMs, end: endMs });
  
  let res = await getDeviceMetrics({ deviceName: selectedDevice.value, start: startMs, end: endMs });
  console.log('device-metrics response:', res);

  const metricOrder = props.deviceType === 'environment' 
    ? ['CO2', 'PM10', 'PM25', 'TEM', 'RH'] 
    : ['power'];
    
  let rawSeries: any[] = [];
  const s1 = (res as any)?.series;
  const s2 = (res as any)?.data?.series;
  const s = s1 ?? s2;
  
  if (Array.isArray(s)) {
    rawSeries = s;
  } else if (s && typeof s === 'object') {
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
        name: metricNameMap[m.metric] || m.metric,
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

      // 若为电表的 power 序列：显示每个点数值标签，并标注值为0的点
      if (props.deviceType === 'power' && String(m.metric).toLowerCase() === 'power') {
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
          // 查找原始指标代码对应的单位
          const originalMetric = Object.keys(metricNameMap).find(key => metricNameMap[key] === metric) || metric;
          const originalUnit = unitsMap?.[originalMetric] ? ` ${unitsMap[originalMetric]}` : '';
          return `${metric}｜${val}${originalUnit}｜${dev}`;
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

// 导出设备数据报表
async function exportDeviceData() {
  if (!selectedDevice.value || !selectedRange.value) {
    createMessage.warning('请先选择设备和时间范围');
    return;
  }

  exportLoading.value = true;
  try {
    const [start, end] = selectedRange.value;
    const startMs = start.valueOf();
    const endMs = end.valueOf();
    
    // 获取设备数据
    const res = await getDeviceMetrics({ 
      deviceName: selectedDevice.value, 
      start: startMs, 
      end: endMs 
    });

    let rawSeries: any[] = [];
    const s1 = (res as any)?.series;
    const s2 = (res as any)?.data?.series;
    const s = s1 ?? s2;
    
    if (Array.isArray(s)) {
      rawSeries = s;
    } else if (s && typeof s === 'object') {
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

    if (rawSeries.length === 0) {
      createMessage.warning('当前时段无数据可导出');
      return;
    }

    // 生成CSV数据
    const csvData = generateCSVData(rawSeries, selectedDevice.value);
    
    // 下载文件
    downloadCSV(csvData, selectedDevice.value, start, end);
    
    createMessage.success('数据报表导出成功');
  } catch (error) {
    console.error('导出失败:', error);
    createMessage.error('导出失败，请重试');
  } finally {
    exportLoading.value = false;
  }
}

// 生成CSV数据
function generateCSVData(rawSeries: any[], deviceName: string) {
  const metricOrder = props.deviceType === 'environment' 
    ? ['CO2', 'PM10', 'PM25', 'TEM', 'RH'] 
    : ['power'];
  const unitsMap: Record<string, string> = {
    'CO2': 'ppm',
    'PM10': 'μg/m³',
    'PM25': 'μg/m³',
    'TEM': '℃',
    'RH': '%',
    'power': 'kWh'
  };

  // 收集所有时间点
  const allTimestamps = new Set<number>();
  rawSeries.forEach((series: any) => {
    (series.points || []).forEach((point: any) => {
      if (point.ts) allTimestamps.add(point.ts);
    });
  });

  const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b);

  // 生成CSV头部
  const headers = ['时间', '设备名称', ...metricOrder.map(metric => `${metricNameMap[metric] || metric}(${unitsMap[metric] || ''})`)];
  
  // 生成CSV行数据
  const rows = sortedTimestamps.map(timestamp => {
    const timeStr = dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss');
    const row = [timeStr, deviceName];
    
    metricOrder.forEach(metric => {
      const series = rawSeries.find((s: any) => s.metric === metric);
      const point = series?.points?.find((p: any) => p.ts === timestamp);
      row.push(point?.value ?? '');
    });
    
    return row;
  });

  return [headers, ...rows];
}

// 下载CSV文件
function downloadCSV(data: any[][], deviceName: string, start: Dayjs, end: Dayjs) {
  const csvContent = data.map(row => 
    row.map(cell => `"${cell}"`).join(',')
  ).join('\n');

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  const fileName = `${deviceName}_${start.format('YYYY-MM-DD')}_${end.format('YYYY-MM-DD')}_数据报表.csv`;
  link.setAttribute('href', url);
  link.setAttribute('download', fileName);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 自动刷新定时器
const setupTimer = () => {
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
  if (autoRefresh.value) {
    const ms = Math.max(1, refreshMinutes.value) * 60 * 1000;
    refreshTimer = setInterval(() => {
      // 将结束时间更新为当前，起点保持与当前窗口同跨度（默认1小时）
      const end = dayjs();
      const start = dayjs(selectedRange.value?.[0] || end.subtract(1, 'hour'));
      const span = end.diff(start);
      selectedRange.value = [end.subtract(span), end];
      fetchAndRenderDeviceMetrics();
    }, ms);
  }
};

onMounted(async () => {
  // 默认选择第一个设备
  if (props.deviceOptions.length > 0) {
    selectedDevice.value = props.deviceOptions[0].value;
    await fetchAndRenderDeviceMetrics();
  }
});
</script>

<style scoped>
.device-chart-container {
  padding: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.chart {
  width: 100%;
  height: 400px;
}

.hint {
  text-align: center;
  color: #999;
  margin-top: 20px;
  font-size: 14px;
}
</style>
