<template>
  <div class="simple-test">
    <h1>环境监测设备 - 简化测试</h1>
    <a-button @click="testAPI" type="primary">测试API调用</a-button>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">错误: {{ error }}</div>
    
    <div v-if="data" class="data-display">
      <h3>API响应数据:</h3>
      <pre>{{ JSON.stringify(data, null, 2) }}</pre>
      
      <h3>设备统计:</h3>
      <p>总设备数: {{ data.total_devices || 0 }}</p>
      <p>在线设备: {{ data.status_distribution?.find(s => s.name === '在线')?.value || 0 }}</p>
      
      <h3>设备列表:</h3>
      <ul>
        <li v-for="device in (data.recent_devices || [])" :key="device.device_id">
          {{ device.device_name }} - {{ device.status }} - {{ device.last_update }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { getDeviceStats } from '/@/views/dashboard/api';

const loading = ref(false);
const error = ref('');
const data = ref(null);

async function testAPI() {
  loading.value = true;
  error.value = '';
  data.value = null;
  
  try {
    console.log('开始调用API...');
    const res = await getDeviceStats();
    console.log('API响应:', res);
    data.value = res;
  } catch (err) {
    console.error('API调用失败:', err);
    error.value = err.message || 'API调用失败';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.simple-test {
  padding: 20px;
}

.loading {
  color: blue;
  margin: 10px 0;
}

.error {
  color: red;
  margin: 10px 0;
}

.data-display {
  margin-top: 20px;
}

pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
