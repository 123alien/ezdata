<template>
  <a-card :title="title" size="small">
    <div ref="chartRef" class="sankey-chart"></div>
  </a-card>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import { SankeyChart } from 'echarts/charts';
import { TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([SankeyChart, TooltipComponent, LegendComponent, CanvasRenderer]);

const props = defineProps<{ 
  title?: string;
  nodes?: Array<{ name: string }>;
  links?: Array<{ source: string; target: string; value: number }>
}>();

const chartRef = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function getDefaultData() {
  const nodes = [
    { name: '外部数据源' },
    { name: '数据采集' },
    { name: 'ETL/清洗' },
    { name: '对象存储MinIO' },
    { name: '关系型数据库MySQL' },
    { name: '向量索引TrustRAG' },
    { name: '数据模型' },
    { name: '知识库' },
    { name: 'API服务' },
    { name: '仪表盘/应用' },
  ];
  const links = [
    { source: '外部数据源', target: '数据采集', value: 20 },
    { source: '数据采集', target: 'ETL/清洗', value: 20 },
    { source: 'ETL/清洗', target: '对象存储MinIO', value: 12 },
    { source: 'ETL/清洗', target: '关系型数据库MySQL', value: 8 },
    { source: '对象存储MinIO', target: '向量索引TrustRAG', value: 6 },
    { source: '关系型数据库MySQL', target: '数据模型', value: 8 },
    { source: '向量索引TrustRAG', target: '知识库', value: 6 },
    { source: '数据模型', target: 'API服务', value: 6 },
    { source: 'API服务', target: '仪表盘/应用', value: 6 },
    { source: '知识库', target: '仪表盘/应用', value: 4 },
  ];
  return { nodes, links };
}

function render() {
  if (!chart && chartRef.value) chart = echarts.init(chartRef.value);
  const { nodes, links } = (props.nodes && props.links) ? { nodes: props.nodes, links: props.links } : getDefaultData();
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'sankey',
        nodeAlign: 'left',
        emphasis: { focus: 'adjacency' },
        data: nodes,
        links: links,
        lineStyle: { color: 'gradient', curveness: 0.5 },
        label: { color: '#333', fontSize: 12 },
        left: 10,
        right: 10,
        top: 10,
        bottom: 10,
      } as any,
    ],
  };
  nextTick(() => chart?.setOption(option));
}

onMounted(() => {
  render();
  window.addEventListener('resize', () => chart?.resize());
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', () => chart?.resize());
  chart?.dispose();
  chart = null;
});

watch(() => [props.nodes, props.links], () => render(), { deep: true });
</script>

<style scoped>
.sankey-chart {
  width: 100%;
  height: 360px;
}
</style>


