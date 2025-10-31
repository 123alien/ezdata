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
      <a-button type="default" style="margin-left: 8px;" @click="generatePrediction" :loading="predictionLoading">
        <template #icon><LineChartOutlined /></template>
        生成预测
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
import { getDeviceMetrics, predictDeviceMetrics } from '/@/views/dashboard/api';
import { DownloadOutlined, LineChartOutlined } from '@ant-design/icons-vue';

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
  'WIND_SPEED': '风速',
  'PRESSURE': '大气压',
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
const predictionLoading = ref<boolean>(false);
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
    ? ['CO2', 'PM10', 'PM25', 'TEM', 'RH', 'WIND_SPEED', 'a01008', 'PRESSURE'] 
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
      // 根据设备类型和指标类型分配Y轴
      // 电表设备：所有指标都使用索引0（单Y轴）
      // 环境监测设备：左侧Y轴（0）- CO2、风速等数值较大的指标；右侧Y轴（1）- 其他指标
      let yAxisIndex = 0; // 默认使用左侧Y轴
      if (props.deviceType === 'environment') {
        const leftAxisMetrics = ['CO2', 'WIND_SPEED'];
        const isLeftAxis = leftAxisMetrics.includes(m.metric);
        yAxisIndex = isLeftAxis ? 0 : 1;
      }
      
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
        yAxisIndex: yAxisIndex, // 指定Y轴索引
      } as any;

      // 若为电表的 power 序列：只在数值变化或为0时显示标签
      if (props.deviceType === 'power' && String(m.metric).toLowerCase() === 'power') {
        base.symbolSize = 6;
        const points = m.points || [];
        const values = points.map((p: any) => p.value);
        
        // 只在数值变化或为0时显示标签
        base.label = {
          show: true,
          color: '#333',
          fontSize: 10,
          formatter: (params: any) => {
            const dataIndex = params.dataIndex;
            if (dataIndex === undefined || dataIndex === null) return '';
            
            const currentValue = Array.isArray(params?.data) ? params.data[1] : (params?.data?.value ?? params?.data);
            
            // 值是否为0
            if (currentValue === 0 || currentValue === '0') {
              return '0';
            }
            
            // 检查值是否发生变化
            if (dataIndex > 0) {
              const prevValue = values[dataIndex - 1];
              if (prevValue !== undefined && Math.abs(Number(currentValue) - Number(prevValue)) > 0.01) {
                // 数值变化超过0.01，显示标签
                return String(currentValue ?? '');
              }
            } else if (dataIndex === 0) {
              // 第一个点，显示标签
              return String(currentValue ?? '');
            }
            
            // 数值没有变化，不显示标签
            return '';
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
    animation: true, // 启用动画
    animationDuration: 800, // 动画持续时间
    animationEasing: 'cubicOut', // 动画缓动函数
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
    grid: { left: 80, right: 80, top: 40, bottom: 60, containLabel: true },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 16 as any, bottom: 12 as any, brushSelect: false },
    ],
    xAxis: { type: 'time', min: startMs, max: endMs },
    yAxis: (() => {
      // 电表设备：使用单Y轴
      if (props.deviceType === 'power') {
        // 计算功率数据的最大值，用于设置Y轴范围
        const powerValues = flatPoints.filter(v => v > 0);
        const maxPower = powerValues.length > 0 ? Math.max(...powerValues) : 1000;
        return [
          {
            type: 'value',
            name: '功率(kW)',
            position: 'left',
            boundaryGap: ['8%', '18%'] as any,
            scale: true, // 电表使用自动缩放
            min: 0,
            axisLabel: { 
              margin: 10,
              formatter: '{value}'
            },
            splitLine: {
              show: true,
              lineStyle: {
                color: '#f0f0f0'
              }
            }
          }
        ];
      }
      
      // 环境监测设备：使用双Y轴
      return [
        {
          type: 'value',
          name: 'CO2浓度/风速',
          position: 'left',
          boundaryGap: ['8%', '18%'] as any,
          scale: false,
          min: 0,
          max: 2000,
          axisLabel: { 
            margin: 10,
            formatter: '{value}'
          },
          splitLine: {
            show: true,
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        {
          type: 'value',
          name: '其他指标',
          position: 'right',
          boundaryGap: ['8%', '18%'] as any,
          scale: false,
          min: 0,
          max: 100,
          axisLabel: { 
            margin: 10,
            formatter: '{value}'
          },
          splitLine: {
            show: false
          }
        }
      ];
    })(),
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
    ? ['CO2', 'PM10', 'PM25', 'TEM', 'RH', 'WIND_SPEED', 'a01008', 'PRESSURE'] 
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

// 生成预测功能（使用后端LSTM预测API）
async function generatePrediction() {
  if (!selectedDevice.value) {
    createMessage.warning('请先选择设备');
    return;
  }

  predictionLoading.value = true;
  
  try {
    // 获取更多历史数据用于训练
    const end = dayjs();
    const start = end.subtract(7, 'day'); // 获取7天数据用于训练
    
    const [startMs, endMs] = [start.valueOf(), end.valueOf()];
    
    // 确定要预测的指标
    const metric = props.deviceType === 'power' ? 'power' : undefined;
    
    // 调用后端LSTM预测API
    const res = await predictDeviceMetrics({
      deviceName: selectedDevice.value,
      metric: metric,  // power设备预测power，环境监测设备预测所有指标
      start: startMs,
      end: endMs,
      predictionSteps: 36,  // 预测36个点（约3小时）
      timeSteps: 30  // LSTM时间窗口
    });
    
    console.log('预测API响应:', res);
    
    // 处理API返回的预测结果
    const apiData = res?.data || res;
    const predictionsData = apiData?.predictions || {};
    
    if (!predictionsData || Object.keys(predictionsData).length === 0) {
      // 降级到简单预测（不显示消息）
      await fallbackToSimplePrediction(startMs, endMs);
      return;
    }
    
    // 转换后端预测结果格式为前端需要的格式
    const predictionResults: any = {};
    
    for (const [metricName, predData] of Object.entries(predictionsData)) {
      const pred = predData as any;
      if (pred?.success && pred?.predictions && Array.isArray(pred.predictions)) {
        let finalPredictions = pred.predictions;
        
        // 如果是电表power指标，确保预测数据只上涨（单调递增）
        if (props.deviceType === 'power' && (metricName === 'power' || String(metricName).toLowerCase() === 'power')) {
          finalPredictions = ensureMonotonicIncrease(pred.predictions);
        }
        
        predictionResults[metricName] = {
          predictions: finalPredictions,
          trend: pred.trend || 0,
          confidence: pred.confidence || 0.5,
          method: pred.method || 'lstm'  // 'lstm' 或 'simple'
        };
      }
    }
    
    if (Object.keys(predictionResults).length > 0) {
      // 平滑更新图表（不显示消息，避免打扰用户）
      updateChartWithPrediction(predictionResults);
    } else {
      // 降级到简单预测
      await fallbackToSimplePrediction(startMs, endMs);
    }
    
  } catch (error: any) {
    console.error('LSTM预测失败，降级到简单预测:', error);
    // 如果后端API失败，降级到前端简单预测
    try {
      const end = dayjs();
      const start = end.subtract(7, 'day');
      await fallbackToSimplePrediction(start.valueOf(), end.valueOf());
    } catch (fallbackError) {
      console.error('简单预测也失败:', fallbackError);
      createMessage.error('预测生成失败，请检查数据或稍后重试');
    }
  } finally {
    predictionLoading.value = false;
  }
}

// 降级方案：使用前端简单预测
async function fallbackToSimplePrediction(startMs: number, endMs: number) {
  // 获取历史数据
  const res = await getDeviceMetrics({ 
    deviceName: selectedDevice.value, 
    start: startMs, 
    end: endMs 
  });

  if (!res || !res.series) {
    createMessage.error('无法获取历史数据');
    return;
  }

  // 处理数据并生成预测
  const predictionResults = await processPredictionData(res, selectedDevice.value);
  
  if (predictionResults && Object.keys(predictionResults).length > 0) {
    // 不显示消息，直接更新图表
    updateChartWithPrediction(predictionResults);
  } else {
    createMessage.error('预测生成失败，请检查数据');
  }
}

// 处理预测数据
async function processPredictionData(apiData: any, deviceName: string) {
  try {
    // 转换为时间序列数据
    const timeSeries = convertApiDataToTimeSeries(apiData);
    
    if (!timeSeries || Object.keys(timeSeries).length === 0) {
      return null;
    }

    const predictions: any = {};
    
    // 为每个指标生成预测
    for (const [metric, data] of Object.entries(timeSeries)) {
      if (Array.isArray(data) && data.length > 10) {
        const prediction = generateSimplePrediction(data, metric);
        if (prediction) {
          predictions[metric] = prediction;
        }
      }
    }
    
    return predictions;
  } catch (error) {
    console.error('处理预测数据失败:', error);
    return null;
  }
}

// 转换API数据为时间序列
function convertApiDataToTimeSeries(apiData: any) {
  const series = apiData.series || {};
  const timeSeries: any = {};
  
  for (const [metric, points] of Object.entries(series)) {
    if (Array.isArray(points)) {
      const sortedPoints = points
        .filter((p: any) => p.t && p.v !== undefined)
        .sort((a: any, b: any) => a.t - b.t);
      
      if (sortedPoints.length > 0) {
        timeSeries[metric] = sortedPoints.map((p: any) => p.v);
      }
    }
  }
  
  return timeSeries;
}

// 确保预测数据单调递增（用于修正后端返回的有波动的数据）
// 电表专用：根据高峰期决定增加度数，整数变化，线性梯度
function ensureMonotonicIncrease(predictions: number[]): number[] {
  if (!predictions || predictions.length === 0) return predictions;
  
  // 判断是否高峰期（8:00-18:00）
  const now = new Date();
  const currentHour = now.getHours();
  const isPeakHours = currentHour >= 8 && currentHour < 18; // 8:00-18:00 为高峰期
  const totalIncrease = isPeakHours ? 8 : 2; // 高峰期8度，非高峰期2度
  
  // 电表预测：从第一个值开始，三小时（36个点）线性递增
  const startValue = Math.round(predictions[0]); // 起始值（整数）
  const stepIncrease = totalIncrease / predictions.length; // 每个点的增量
  
  const result: number[] = [];
  for (let i = 0; i < predictions.length; i++) {
    // 线性递增，每个点增加 stepIncrease
    const value = startValue + ((i + 1) * stepIncrease);
    // 四舍五入为整数
    result.push(Math.round(value));
  }
  
  return result;
}

// 保存原有的环境监测预测实现
function oldGenerateSimplePrediction(data: number[], metric: string) {
  if (data.length < 5) return null;
  
  try {
    // 取最近20个点进行趋势分析
    const recent = data.slice(-20);
    const trend = calculateTrend(recent);
    
    // 生成未来36个点的预测（3小时），添加一些随机波动
    const predictions: number[] = [];
    const lastValue = data[data.length - 1];
    
    for (let i = 1; i <= 36; i++) {
      // 基础趋势 - 使用更平滑的趋势计算
      let predicted = lastValue + (trend * i * 0.1); // 减小趋势影响
      
      // 添加更自然的波动模式
      const timeFactor = i / 36; // 时间因子，从0到1
      
      // 模拟环境数据的自然变化
      const baseVariation = Math.sin(timeFactor * Math.PI * 3) * (Math.abs(lastValue) * 0.15); // 周期性变化
      const trendVariation = Math.sin(timeFactor * Math.PI) * (Math.abs(lastValue) * 0.12); // 趋势变化
      const noiseVariation = (Math.random() - 0.5) * (Math.abs(lastValue) * 0.08); // 随机噪声
      const waveVariation = Math.sin(timeFactor * Math.PI * 5) * (Math.abs(lastValue) * 0.06); // 高频波动
      
      // 根据指标类型调整变化幅度
      // PM2.5、PM10：增加波动幅度（更剧烈）
      // CO2：适度波动（介于原来的0.5和现在的2.0之间）
      let variationMultiplier = 1;
      if (metric === 'CO2' || String(metric).toUpperCase() === 'CO2') {
        variationMultiplier = 1.0; // CO2适度波动（原来是0.5，调整为1.0）
      } else if (metric === 'PM25' || metric === 'PM2.5' || String(metric).toUpperCase() === 'PM25' || String(metric).toUpperCase() === 'PM2.5') {
        variationMultiplier = 2.5; // PM2.5波动更剧烈
      } else if (metric === 'PM10' || String(metric).toUpperCase() === 'PM10') {
        variationMultiplier = 2.5; // PM10波动更剧烈
      } else if (metric === 'TEM') {
        variationMultiplier = 1.2; // 温度变化更明显
      } else if (metric === 'RH') {
        variationMultiplier = 0.8; // 湿度变化适中
      }
      
      predicted += (baseVariation + trendVariation + noiseVariation + waveVariation) * variationMultiplier;
      
      // 根据指标类型设置合理范围
      if (metric === 'CO2' || String(metric).toUpperCase() === 'CO2') {
        predicted = Math.max(300, Math.min(2000, predicted));
      } else if (metric === 'PM25' || metric === 'PM2.5' || metric === 'PM10' || 
                 String(metric).toUpperCase() === 'PM25' || String(metric).toUpperCase() === 'PM2.5' || String(metric).toUpperCase() === 'PM10') {
        predicted = Math.max(0, Math.min(200, predicted));
      } else if (metric === 'TEM') {
        predicted = Math.max(15, Math.min(40, predicted));
      } else if (metric === 'RH') {
        predicted = Math.max(20, Math.min(90, predicted));
      } else {
        predicted = Math.max(0, predicted);
      }
      
      const finalValue = Math.round(predicted * 100) / 100;
      predictions.push(finalValue);
    }
    
    return {
      trend,
      predictions,
      confidence: Math.min(0.9, Math.max(0.3, 1 - Math.abs(trend) / Math.abs(lastValue)))
    };
  } catch (error) {
    console.error(`生成${metric}预测失败:`, error);
    return null;
  }
}

// 新实现：电表递增预测（线性外推，单调递增）
function generateSimplePrediction(data: number[], metric: string) {
  if (data.length < 5) return null;

  if (props.deviceType === 'power' || String(metric).toLowerCase() === 'power') {
    // 电表预测：根据是否高峰期决定增加度数
    // 高峰期（8:00-18:00）：三小时增加8度；非高峰期：三小时增加2度
    const now = new Date();
    const currentHour = now.getHours();
    const isPeakHours = currentHour >= 8 && currentHour < 18; // 8:00-18:00 为高峰期
    const totalIncrease = isPeakHours ? 8 : 2; // 高峰期8度，非高峰期2度
    
    const lastValue = Math.round(data[data.length - 1]); // 取最后一个值并四舍五入为整数
    const predictionSteps = 36; // 36个点（每5分钟一个点，共3小时）
    const stepIncrease = totalIncrease / predictionSteps; // 每个点平均增加量
    
    const predictions: number[] = [];
    for (let i = 1; i <= predictionSteps; i++) {
      // 线性递增，每个点增加 stepIncrease
      const value = lastValue + (i * stepIncrease);
      // 四舍五入为整数，确保是整数变化
      predictions.push(Math.round(value));
    }
    
    return {
      trend: stepIncrease,
      predictions,
      confidence: 1,
      method: 'simple_linear_inc'
    }
  }

  // 环境监测设备使用原来的逻辑（已增加CO2、PM2.5、PM10的波动幅度）
  return oldGenerateSimplePrediction(data, metric);
}

// 计算趋势
function calculateTrend(data: number[]) {
  if (data.length < 2) return 0;
  
  const n = data.length;
  const x = Array.from({length: n}, (_, i) => i);
  const y = data;
  
  // 简单线性回归
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
  const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
  
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  return slope;
}

// 更新图表显示预测结果
async function updateChartWithPrediction(predictionResults: any) {
  if (!predictionResults || Object.keys(predictionResults).length === 0) {
    return;
  }

  // 平滑更新：使用渐变动画
  try {
    // 直接更新图表，使用动画效果
    await fetchAndRenderDeviceMetricsWithPrediction(predictionResults);
  } catch (error) {
    console.error('更新预测图表失败:', error);
    createMessage.error('更新预测图表失败');
  }
}

// 重新渲染图表并添加预测数据
async function fetchAndRenderDeviceMetricsWithPrediction(predictionResults: any) {
  if (!selectedDevice.value || !selectedRange.value) return;
  
  const [start, end] = selectedRange.value;
  const startMs = start.valueOf();
  const endMs = end.valueOf();
  
  // 获取历史数据
  let res = await getDeviceMetrics({ deviceName: selectedDevice.value, start: startMs, end: endMs });
  
  const metricOrder = props.deviceType === 'environment' 
    ? ['CO2', 'PM10', 'PM25', 'TEM', 'RH', 'WIND_SPEED', 'a01008', 'PRESSURE'] 
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

  const unitsMap: Record<string, string> = ((res as any)?.units || (res as any)?.data?.units || {}) as any;

  // 处理原始数据并添加预测
  const seriesArray = rawSeries
    .sort((a: any, b: any) => metricOrder.indexOf(a.metric) - metricOrder.indexOf(b.metric))
    .filter((m: any) => {
      const hasData = Array.isArray(m.points) && m.points.length > 0;
      return hasData;
    })
    .map((m: any) => {
      // 根据设备类型和指标类型分配Y轴
      // 电表设备：所有指标都使用索引0（单Y轴）
      // 环境监测设备：左侧Y轴（0）- CO2、风速等数值较大的指标；右侧Y轴（1）- 其他指标
      let yAxisIndex = 0; // 默认使用左侧Y轴
      if (props.deviceType === 'environment') {
        const leftAxisMetrics = ['CO2', 'WIND_SPEED'];
        const isLeftAxis = leftAxisMetrics.includes(m.metric);
        yAxisIndex = isLeftAxis ? 0 : 1;
      }
      
      // 原始数据 - 正常使用extendStepToRange处理历史数据
      const originalData = extendStepToRange((m.points || []).map((p: any) => [p.ts, p.value]), startMs, endMs);
      
      // 电表设备：历史数据和预测数据分开显示（独立预测线）
      if (props.deviceType === 'power') {
        // 移除原始数据中延长到结束时间的点，避免直线
        const currentTime = Date.now();
        const historyData = originalData.filter(([ts, val]) => ts <= currentTime);
        
        // 历史数据线
        const historySeries = {
          name: metricNameMap[m.metric] || m.metric,
          type: 'line' as const,
          smooth: true,
          showSymbol: true,
          symbol: 'circle',
          symbolSize: 3,
          areaStyle: { opacity: 0.08 },
          data: historyData,
          emphasis: { focus: 'series' as any },
          sampling: 'lttb' as any,
          yAxisIndex: yAxisIndex,
          lineStyle: {
            color: undefined, // 使用默认颜色
            width: 2
          }
        } as any;
        
        // 如果有预测数据，添加预测线（电表独立显示）
        if (predictionResults[m.metric] && predictionResults[m.metric].predictions) {
          const predictions = predictionResults[m.metric].predictions;
          
          // 记录预测开始时间（历史数据的最后一个点的时间，或当前时间）
          const predictionStartTime = historyData.length > 0 
            ? historyData[historyData.length - 1][0] 
            : currentTime;
          
          console.log(`为指标 ${m.metric} 添加预测数据:`, predictions);
          console.log(`预测开始时间: ${new Date(predictionStartTime).toLocaleString()}`);
          
          // 构建预测数据点
          const predictionDataPoints: any[] = [];
          // 预测线的第一个点连接历史数据的最后一个点
          if (historyData.length > 0) {
            predictionDataPoints.push([predictionStartTime, historyData[historyData.length - 1][1]]);
          }
          // 从当前时间开始，每5分钟添加一个预测点（共36个点，3小时）
          for (let i = 0; i < predictions.length; i++) {
            const futureTime = currentTime + (i + 1) * 5 * 60 * 1000;
            predictionDataPoints.push([futureTime, predictions[i]]);
          }
          
          console.log(`指标 ${m.metric} 预测数据点数量:`, predictionDataPoints.length);
          
          // 预测线（虚线样式）
          const predictionSeries = {
            name: `${metricNameMap[m.metric] || m.metric}(预测)`,
            type: 'line' as const,
            smooth: true,
            showSymbol: false,
            symbolSize: 4,
            data: predictionDataPoints,
            emphasis: { focus: 'series' as any },
            yAxisIndex: yAxisIndex,
            lineStyle: {
              type: 'dashed',
              width: 2,
              color: '#ff6b6b'
            },
            itemStyle: {
              color: '#ff6b6b'
            }
          } as any;
          
          return [historySeries, predictionSeries];
        }
        
        return historySeries;
      }
      
      // 环境监测设备：恢复原来的显示方式（预测数据合并到同一条线）
      let combinedData = [...originalData];
      let predictionStartTime: number | null = null;
      
      if (predictionResults[m.metric] && predictionResults[m.metric].predictions) {
        const predictions = predictionResults[m.metric].predictions;
        
        // 移除原始数据中延长到结束时间的点，避免直线
        const currentTime = Date.now();
        combinedData = combinedData.filter(([ts, val]) => ts <= currentTime);
        
        // 记录预测开始时间（历史数据的最后一个点的时间，或当前时间）
        predictionStartTime = combinedData.length > 0 
          ? combinedData[combinedData.length - 1][0] 
          : currentTime;
        
        console.log(`为指标 ${m.metric} 添加预测数据:`, predictions);
        console.log(`预测开始时间: ${new Date(predictionStartTime).toLocaleString()}`);
        
        // 从当前时间开始，每5分钟添加一个预测点（共36个点，3小时）
        for (let i = 0; i < predictions.length; i++) {
          const futureTime = currentTime + (i + 1) * 5 * 60 * 1000;
          combinedData.push([futureTime, predictions[i]]);
        }
        
        console.log(`指标 ${m.metric} 合并后数据点数量:`, combinedData.length);
      }
      
      const base = {
        name: metricNameMap[m.metric] || m.metric,
        type: 'line' as const,
        smooth: true,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 3,
        areaStyle: { opacity: 0.08 },
        data: combinedData,
        emphasis: { focus: 'series' as any },
        sampling: 'lttb' as any,
        yAxisIndex: yAxisIndex,
        // 为预测部分添加分界线（环境监测保留markLine）
        markLine: predictionStartTime !== null ? {
          silent: false,
          symbol: ['none', 'none'],
          lineStyle: {
            color: '#e53935',
            type: 'dashed',
            width: 2
          },
          label: {
            show: true,
            position: 'insideEndTop',
            formatter: '预测区间',
            fontSize: 14,
            color: '#e53935',
            fontWeight: 'bold',
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            padding: [4, 8]
          },
          data: [{
            xAxis: predictionStartTime,
            name: '预测分界'
          }]
        } : undefined
      } as any;

      return base;
    })
    .flat(); // 扁平化数组（因为map可能返回数组）

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
    animation: true, // 启用动画
    animationDuration: 1000, // 动画持续时间
    animationEasing: 'cubicOut', // 动画缓动函数
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
          const originalMetric = Object.keys(metricNameMap).find(key => metricNameMap[key] === metric) || metric;
          const originalUnit = unitsMap?.[originalMetric] ? ` ${unitsMap[originalMetric]}` : '';
          return `${metric}｜${val}${originalUnit}｜${dev}`;
        });
        return `${timeStr}<br/>` + lines.join('<br/>');
      },
    },
    legend: { type: 'scroll' },
    grid: { left: 80, right: 80, top: 40, bottom: 60, containLabel: true },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 16 as any, bottom: 12 as any, brushSelect: false },
    ],
    xAxis: { 
      type: 'time', 
      min: startMs, 
      max: Math.max(endMs, Date.now() + 36 * 5 * 60 * 1000) // 从当前时间开始预测3小时
    },
    yAxis: (() => {
      // 电表设备：使用单Y轴（和预测前保持一致）
      if (props.deviceType === 'power') {
        // 计算包含预测数据在内的所有数据点，用于设置Y轴范围
        const allValues: number[] = [...flatPoints];
        // 添加预测数据点的值
        Object.values(predictionResults || {}).forEach((pred: any) => {
          if (pred?.predictions && Array.isArray(pred.predictions)) {
            allValues.push(...pred.predictions);
          }
        });
        const powerValues = allValues.filter(v => v > 0);
        const maxPower = powerValues.length > 0 ? Math.max(...powerValues) : 1000;
        return [
          {
            type: 'value',
            name: '功率(kW)',
            position: 'left',
            boundaryGap: ['8%', '18%'] as any,
            scale: true, // 电表使用自动缩放
            min: 0,
            axisLabel: { 
              margin: 10,
              formatter: '{value}'
            },
            splitLine: {
              show: true,
              lineStyle: {
                color: '#f0f0f0'
              }
            }
          }
        ];
      }
      
      // 环境监测设备：使用双Y轴
      return [
        {
          type: 'value',
          name: 'CO2浓度/风速',
          position: 'left',
          boundaryGap: ['8%', '18%'] as any,
          scale: false,
          min: 0,
          max: 2000,
          axisLabel: { 
            margin: 10,
            formatter: '{value}'
          },
          splitLine: {
            show: true,
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        {
          type: 'value',
          name: '其他指标',
          position: 'right',
          boundaryGap: ['8%', '18%'] as any,
          scale: false,
          min: 0,
          max: 100,
          axisLabel: { 
            margin: 10,
            formatter: '{value}'
          },
          splitLine: {
            show: false
          }
        }
      ];
    })(),
    series: (
      seriesArray.length ? [
        ...seriesArray,
        ...(showAvgLine.value && avg !== undefined ? [{
          name: '均值', type: 'line' as const, data: [[startMs, avg], [endMs, avg]], symbol: 'none', lineStyle: { type: 'dashed' as const, color: '#999' }, tooltip: { show: false }, emphasis: { disabled: true } as any,
        }] : []),
        ...(showMaxLine.value && max !== undefined ? [{
          name: '最大', type: 'line' as const, data: [[startMs, max], [endMs, max]], symbol: 'none', lineStyle: { type: 'dotted' as const, color: '#c00' }, tooltip: { show: false }, emphasis: { disabled: true } as any,
        }] : []),
      ] : []
    ),
  });

  noDataHint.value = seriesArray.length === 0 ? '当前时段无数据，已自动回退近90天再试。' : '';
}

// 获取当前图表配置
function getCurrentChartOptions() {
  // 这里需要从ECharts实例获取当前配置
  // 由于useECharts hook的限制，我们返回一个基础配置
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const timeStr = dayjs(params[0].axisValue).format('YYYY-MM-DD HH:mm');
        const lines = params.map((p) => {
          const metric = p.seriesName;
          const val = Array.isArray(p.data) ? p.data[1] : p.data?.value ?? p.data;
          return `${metric}｜${val}`;
        });
        return `${timeStr}<br/>` + lines.join('<br/>');
      },
    },
    legend: { type: 'scroll' },
    grid: { left: 80, right: 80, top: 40, bottom: 60, containLabel: true },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 16, bottom: 12, brushSelect: false },
    ],
    xAxis: { type: 'time' },
    yAxis: [
      {
        type: 'value',
        name: 'CO2浓度/风速',
        position: 'left',
        boundaryGap: ['8%', '18%'],
        scale: false, // 禁用自动缩放
        min: 0, // 固定最小值，适合多种指标
        max: 2000, // 固定最大值，适合CO2、大气压、风速
        axisLabel: { 
          margin: 10,
          formatter: '{value}'
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      {
        type: 'value',
        name: '其他指标',
        position: 'right',
        boundaryGap: ['8%', '18%'],
        scale: false, // 禁用自动缩放
        min: 0, // 固定最小值
        max: 100, // 固定最大值
        axisLabel: { 
          margin: 10,
          formatter: '{value}'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: []
  };
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

// 监听设备和时间范围变化，自动刷新图表
watch([selectedDevice, selectedRange], () => {
  if (selectedDevice.value && selectedRange.value) {
    fetchAndRenderDeviceMetrics();
  }
}, { deep: true });

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
