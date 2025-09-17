<template>
  <a-card title="金融数据（AkShare 股票K线）" size="small">
    <a-form layout="inline" :model="form" class="mb-2">
      <a-form-item label="数据接口">
        <a-select v-model:value="selectedModelId" style="width:280px" :options="modelOptions" placeholder="选择 AkShare 财经数据接口" allowClear @change="onModelChange" />
      </a-form-item>
      <a-form-item label="代码">
        <a-input v-model:value="form.symbol" style="width:140px" placeholder="000001.SZ" />
      </a-form-item>
      <a-form-item label="复权">
        <a-select v-model:value="form.adjust" style="width:110px">
          <a-select-option value="qfq">前复权</a-select-option>
          <a-select-option value="hfq">后复权</a-select-option>
          <a-select-option value="none">不复权</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="起始">
        <a-date-picker v-model:value="form.start" value-format="YYYYMMDD" />
      </a-form-item>
      <a-form-item label="截止">
        <a-date-picker v-model:value="form.end" value-format="YYYYMMDD" />
      </a-form-item>
      <a-form-item>
        <a-space>
          <a-button type="primary" :loading="loading" @click="fetchKline">绘制</a-button>
          <a-button @click="loadDefaults">恢复默认</a-button>
          <a-button @click="saveDefaults">保存为默认</a-button>
        </a-space>
      </a-form-item>
    </a-form>
    <div ref="chartRef" style="height:420px;width:100%"></div>
  </a-card>
  
</template>

<script lang="ts" setup>
import { onMounted, ref, reactive, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { CandlestickChart, BarChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, DataZoomComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import dayjs from 'dayjs';
import { message } from 'ant-design-vue';
import { getStockDefaults, saveStockDefaults, getStockKline, allList } from '../datamodel.api';

echarts.use([CandlestickChart, BarChart, LineChart, GridComponent, TooltipComponent, DataZoomComponent, LegendComponent, CanvasRenderer]);

const chartRef = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

const loading = ref(false);
const selectedModelId = ref<string | number | undefined>(undefined);
const modelOptions = ref<{label:string; value:string|number}[]>([]);
const form = reactive<{symbol:string; adjust:'qfq'|'hfq'|'none'; start:string; end:string}>({
  symbol: '000001.SZ', adjust: 'qfq',
  start: dayjs().add(-365, 'day').format('YYYYMMDD'),
  end: dayjs().format('YYYYMMDD'),
});

function ma(series:number[], period:number) {
  const out:number[] = [];
  for (let i=0;i<series.length;i++){
    if (i < period-1) { out.push(NaN); continue; }
    let sum=0; for (let j=0;j<period;j++) sum += series[i-j];
    out.push(sum/period);
  }
  return out;
}

async function loadDefaults() {
  const res:any = await getStockDefaults();
  const d = res?.data || res?.result || res;
  if (d) {
    form.symbol = d.symbol || form.symbol;
    form.adjust = d.adjust || form.adjust;
    form.start = d.start || form.start;
    form.end = d.end || form.end;
    // 不在这里调用 fetchKline()，因为 selectedModelId 可能还没有设置
  }
}

async function saveDefaults() {
  await saveStockDefaults({ ...form });
}

async function fetchKline() {
  if (!selectedModelId.value) {
    message.warning('请先选择数据接口函数');
    return;
  }
  loading.value = true;
  try {
    // 找到选中的函数对应的模型ID
    const selectedOption = modelOptions.value.find(opt => opt.value === selectedModelId.value);
    const modelId = selectedOption?.modelId;
    
    if (!modelId) {
      message.error('未找到对应的数据模型');
      return;
    }
    
    // 调用后端API，传递函数名
    const res:any = await getStockKline({ 
      function_name: selectedModelId.value, // 传递函数名
      symbol: form.symbol,
      adjust: form.adjust,
      start: form.start,
      end: form.end
    });
    const rows = (res?.data || res?.result || res || []) as Array<any>;
    
    // 验证数据格式
    if (!Array.isArray(rows)) {
      console.error('返回的数据不是数组:', rows);
      message.error('数据格式错误，请检查后端API');
      return;
    }
    
    if (rows.length === 0) {
      message.warning('没有获取到数据，请检查股票代码或时间范围');
      return;
    }
    
    console.log('获取到的数据:', rows.slice(0, 3)); // 打印前3条数据用于调试
    renderKline(rows);
  } catch (e: any) {
    message.error(e?.message || '获取K线数据失败');
  } finally {
    loading.value = false;
  }
}

function normalizeRows(rows:any[]): {dates:string[]; o:number[]; h:number[]; l:number[]; c:number[]; v:number[]} {
  if (!Array.isArray(rows)) {
    console.error('normalizeRows: 输入不是数组:', rows);
    return {dates:[], o:[], h:[], l:[], c:[], v:[]};
  }
  
  const pick = (obj:any, keys:string[]) => keys.find(k=>obj[k]!==undefined);
  const out = {dates:[] as string[], o:[] as number[], h:[] as number[], l:[] as number[], c:[] as number[], v:[] as number[]};
  const dateKeys = ['date','日期','time','时间'];
  const openKeys = ['open','开盘'];
  const highKeys = ['high','最高'];
  const lowKeys = ['low','最低'];
  const closeKeys = ['close','收盘'];
  const volKeys = ['volume','成交量','vol'];
  
  rows.forEach((r, index) => {
    if (!r || typeof r !== 'object') {
      console.warn(`normalizeRows: 第${index}行数据无效:`, r);
      return;
    }
    
    const dKey = pick(r, dateKeys); 
    const oKey = pick(r, openKeys); 
    const hKey = pick(r, highKeys);
    const lKey = pick(r, lowKeys); 
    const cKey = pick(r, closeKeys); 
    const vKey = pick(r, volKeys);
    
    if (dKey && oKey && hKey && lKey && cKey) {
      out.dates.push(String(r[dKey]));
      out.o.push(Number(r[oKey]));
      out.h.push(Number(r[hKey]));
      out.l.push(Number(r[lKey]));
      out.c.push(Number(r[cKey]));
      out.v.push(Number(vKey? r[vKey]: 0));
    } else {
      console.warn(`normalizeRows: 第${index}行缺少必要字段:`, r);
    }
  });
  
  console.log(`normalizeRows: 处理了${rows.length}行数据，成功解析${out.dates.length}行`);
  return out;
}

function renderKline(rows:any[]) {
  const {dates,o,h,l,c,v} = normalizeRows(rows);
  const k = c.map((_,i)=>[o[i],c[i],l[i],h[i]]);
  const option: echarts.EChartsOption = {
    grid: [{ left: 40, right: 20, top: 30, height: 240 }, { left: 40, right: 20, top: 300, height: 90 }],
    legend: { top: 0, data: ['K线','MA5','MA10','MA20'] },
    tooltip: { trigger: 'axis' },
    dataZoom: [{ type: 'inside', xAxisIndex: [0,1] }, { type: 'slider', xAxisIndex: [0,1] }],
    xAxis: [{ type:'category', data: dates, boundaryGap: true }, { type:'category', data: dates, gridIndex:1, boundaryGap:true }],
    yAxis: [{ scale:true }, { gridIndex:1, scale:true }],
    series: [
      { name:'K线', type:'candlestick', data:k },
      { name:'MA5', type:'line', data:ma(c,5), smooth:true, symbol:'none' },
      { name:'MA10', type:'line', data:ma(c,10), smooth:true, symbol:'none' },
      { name:'MA20', type:'line', data:ma(c,20), smooth:true, symbol:'none' },
      { name:'成交量', type:'bar', data: v, xAxisIndex:1, yAxisIndex:1 }
    ]
  };
  if (!chart && chartRef.value) chart = echarts.init(chartRef.value);
  nextTick(()=> chart?.setOption(option));
}

async function queryByModelId(id:string) {
  // 使用通用查询接口查询模型数据
  const res = await fetch('/api/datamodel/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id })
  });
  const json = await res.json();
  // 兼容后端返回格式
  return (json?.data?.records || json?.data || json?.result || []);
}

async function loadModelOptions() {
  try {
    // 取所有数据模型，筛选 akshare 财经类（按名称或类型包含 akshare）
    const res:any = await allList({});
    const list = (res?.data?.records || res?.data || res || []) as any[];
    
    // 找到股票历史数据接口模型
    const stockModel = list.find((m:any)=> /股票历史数据接口/i.test(m?.name || ''));
    
    if (!stockModel) {
      console.warn('未找到股票历史数据接口模型，使用默认函数列表');
      // 提供默认的函数选项
      const defaultFunctions = [
        'A股日频率数据-东方财富',
        '美股日频率数据-雅虎财经', 
        '港股日频率数据-腾讯'
      ];
      
      const opts = defaultFunctions.map(funcName => ({
        label: funcName,
        value: funcName,
        modelId: 'default'
      }));
      
      modelOptions.value = opts;
      if (!selectedModelId.value && opts.length) {
        selectedModelId.value = opts[0].value;
      }
      return;
    }
    
    // 解析模型配置，获取可用的数据接口函数列表
    const conf = (stockModel.model_conf && typeof stockModel.model_conf === 'string') 
      ? (()=>{try{return JSON.parse(stockModel.model_conf)}catch{return {}}})() 
      : (stockModel.model_conf || {});
    
    // 从配置中提取函数列表
    const functions = conf.functions || conf.api_functions || conf.function_list || [];
    
    let opts = [];
    if (functions.length > 0) {
      opts = functions.map((func:any, index:number) => {
        const funcName = typeof func === 'string' ? func : (func.name || func.function || func.api_function || `函数${index+1}`);
        return { 
          label: funcName, 
          value: funcName,
          modelId: stockModel.id 
        };
      });
    } else {
      // 如果模型配置中没有函数列表，使用默认函数
      const defaultFunctions = [
        'A股日频率数据-东方财富',
        '美股日频率数据-雅虎财经', 
        '港股日频率数据-腾讯'
      ];
      
      opts = defaultFunctions.map(funcName => ({
        label: funcName,
        value: funcName,
        modelId: stockModel.id
      }));
    }
    
    modelOptions.value = opts;
    // 默认选最近修改的一条
    if (!selectedModelId.value && opts.length) {
      selectedModelId.value = opts[0].value;
    }
  } catch (error) {
    console.error('加载数据模型选项失败:', error);
    // 提供默认选项
    const defaultFunctions = [
      'A股日频率数据-东方财富',
      '美股日频率数据-雅虎财经', 
      '港股日频率数据-腾讯'
    ];
    
    const opts = defaultFunctions.map(funcName => ({
      label: funcName,
      value: funcName,
      modelId: 'default'
    }));
    
    modelOptions.value = opts;
    if (!selectedModelId.value && opts.length) {
      selectedModelId.value = opts[0].value;
    }
  }
}

function onModelChange() {
  fetchKline();
}
onMounted(async ()=>{
  if (!chart && chartRef.value) chart = echarts.init(chartRef.value);
  // 先加载模型选项，再加载默认参数，最后自动获取数据
  console.log('开始加载模型选项...');
  await loadModelOptions();
  console.log('模型选项加载完成，selectedModelId:', selectedModelId.value);
  
  console.log('开始加载默认参数...');
  await loadDefaults();
  console.log('默认参数加载完成');
  
  // 如果还没有选择模型，尝试自动获取数据
  if (selectedModelId.value) {
    console.log('自动获取K线数据...');
    await fetchKline();
  } else {
    console.log('没有选择模型，跳过自动获取数据');
  }
  window.addEventListener('resize', ()=> chart?.resize());
});
</script>

<style scoped>
.mb-2 { margin-bottom: 8px; }
</style>


