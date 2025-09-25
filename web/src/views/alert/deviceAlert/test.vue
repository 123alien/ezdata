<template>
  <div class="test-page">
    <h1>设备告警管理测试页面</h1>
    <p>这是一个测试页面，用于验证告警管理模块是否正常工作。</p>
    
    <div class="test-actions">
      <a-button type="primary" @click="testCreateStrategies" :loading="creating">
        测试创建默认策略
      </a-button>
      <a-button @click="testCheckAlerts" :loading="checking">
        测试检查告警
      </a-button>
    </div>
    
    <div class="test-results" v-if="testResult">
      <h3>测试结果：</h3>
      <pre>{{ testResult }}</pre>
    </div>
    
    <div class="test-info">
      <h3>功能说明：</h3>
      <ul>
        <li><strong>创建默认策略</strong>：创建电表和环境监测的默认告警策略</li>
        <li><strong>检查告警</strong>：手动触发设备告警检查</li>
        <li><strong>访问地址</strong>：<code>http://localhost:5179/alert/device-alert</code></li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { createDefaultStrategies, checkDeviceAlerts } from './deviceAlert.api'

const testResult = ref('')
const creating = ref(false)
const checking = ref(false)

const testCreateStrategies = async () => {
  creating.value = true
  try {
    testResult.value = '正在创建默认策略...'
    await createDefaultStrategies()
    testResult.value = '✅ 默认策略创建成功！'
  } catch (error) {
    testResult.value = `❌ 创建默认策略失败：${error}`
  } finally {
    creating.value = false
  }
}

const testCheckAlerts = async () => {
  checking.value = true
  try {
    testResult.value = '正在检查告警...'
    await checkDeviceAlerts()
    testResult.value = '✅ 告警检查完成！'
  } catch (error) {
    testResult.value = `❌ 检查告警失败：${error}`
  } finally {
    checking.value = false
  }
}
</script>

<style scoped>
.test-page {
  padding: 24px;
}

.test-actions {
  margin: 20px 0;
  display: flex;
  gap: 12px;
}

.test-results {
  margin-top: 20px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 6px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
