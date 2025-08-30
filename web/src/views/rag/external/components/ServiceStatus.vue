<template>
  <div class="service-status">
    <a-card title="TrustRAG 服务状态" :bordered="false" size="small">
      <template #extra>
        <a-space>
          <a-button 
            type="primary" 
            size="small" 
            :loading="refreshing"
            @click="refreshStatus"
          >
            刷新状态
          </a-button>
          <a-button 
            type="default" 
            size="small" 
            :loading="initializing"
            @click="initializeService"
          >
            初始化服务
          </a-button>
          <a-button 
            type="default" 
            size="small" 
            :loading="testing"
            @click="testConnection"
          >
            测试连接
          </a-button>
        </a-space>
      </template>
      
      <a-row :gutter="16">
        <a-col :span="8">
          <a-statistic 
            title="服务状态" 
            :value="statusTextMap[serviceStatus?.health?.status || 'error']"
            :value-style="{ color: statusColorMap[serviceStatus?.health?.status || 'error'] }"
          />
        </a-col>
        <a-col :span="8">
          <a-statistic 
            title="版本" 
            :value="serviceStatus?.health?.version || '未知'"
          />
        </a-col>
        <a-col :span="8">
          <a-statistic 
            title="更新时间" 
            :value="formatTime(serviceStatus?.timestamp)"
          />
        </a-col>
      </a-row>
      
      <a-divider />
      
      <a-row :gutter="16">
        <a-col :span="24">
          <a-descriptions title="组件状态" :column="3" size="small">
            <a-descriptions-item label="RAG系统">
              <a-tag :color="serviceStatus?.health?.components?.rag_system ? 'green' : 'red'">
                {{ serviceStatus?.health?.components?.rag_system ? '就绪' : '未就绪' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="文档分块">
              <a-tag :color="serviceStatus?.health?.components?.chunks_loaded ? 'green' : 'red'">
                {{ serviceStatus?.health?.components?.chunks_loaded ? '已加载' : '未加载' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="检索索引">
              <a-tag :color="serviceStatus?.health?.components?.index_ready ? 'green' : 'red'">
                {{ serviceStatus?.health?.components?.index_ready ? '就绪' : '未就绪' }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-col>
      </a-row>
      
      <a-divider />
      
      <a-row :gutter="16">
        <a-col :span="24">
          <a-descriptions title="服务端点" :column="2" size="small">
            <a-descriptions-item 
              v-for="(url, name) in serviceStatus?.endpoints" 
              :key="name"
              :label="getEndpointLabel(name)"
            >
              <a-tag color="blue">{{ url }}</a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-col>
      </a-row>
      
      <a-divider v-if="testResult" />
      
      <div v-if="testResult" class="test-result">
        <a-alert
          :message="`连接测试结果 - ${getTestStatusText()}`"
          :type="getTestStatusType()"
          show-icon
        >
          <template #description>
            <a-space direction="vertical" size="small">
              <div v-for="(test, key) in testResult" :key="key">
                <strong>{{ getTestLabel(key) }}:</strong>
                <a-tag :color="test.status === 'success' ? 'green' : 'red'">
                  {{ test.status === 'success' ? '成功' : '失败' }}
                </a-tag>
                <span v-if="test.error" class="error-text">{{ test.error }}</span>
              </div>
            </a-space>
          </template>
        </a-alert>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { 
  getStatus, 
  initializeRAG, 
  testConnection as testConnectionAPI
} from '../api/external-rag.api';
import { 
  TrustRAGStatus, 
  ConnectionTestResult,
  statusTextMap,
  statusColorMap
} from '../data/external-rag.data';

const serviceStatus = ref<TrustRAGStatus | null>(null);
const testResult = ref<ConnectionTestResult | null>(null);
const refreshing = ref(false);
const initializing = ref(false);
const testing = ref(false);

// 获取服务状态
const refreshStatus = async () => {
  try {
    refreshing.value = true;
    const response = await getStatus();
    if (response.code === 200) {
      serviceStatus.value = response.data;
      message.success('状态刷新成功');
    } else {
      message.error('状态刷新失败');
    }
  } catch (error) {
    message.error('状态刷新失败: ' + error);
  } finally {
    refreshing.value = false;
  }
};

// 初始化服务
const initializeService = async () => {
  try {
    initializing.value = true;
    const response = await initializeRAG();
    if (response.code === 200) {
      message.success('服务初始化成功');
      await refreshStatus();
    } else {
      message.error('服务初始化失败');
    }
  } catch (error) {
    message.error('服务初始化失败: ' + error);
  } finally {
    initializing.value = false;
  }
};

// 测试连接
const testConnection = async () => {
  try {
    testing.value = true;
    const response = await testConnectionAPI();
    if (response.code === 200) {
      testResult.value = response.data;
      message.success('连接测试完成');
    } else {
      message.error('连接测试失败');
    }
  } catch (error) {
    message.error('连接测试失败: ' + error);
  } finally {
    testing.value = false;
  }
};

// 格式化时间
const formatTime = (timestamp: string) => {
  if (!timestamp) return '未知';
  try {
    return new Date(timestamp).toLocaleString('zh-CN');
  } catch {
    return timestamp;
  }
};

// 获取端点标签
const getEndpointLabel = (name: string) => {
  const labelMap: Record<string, string> = {
    health: '健康检查',
    chat: '聊天接口',
    text: '文本查询',
    openai: 'OpenAI兼容',
    initialize: '初始化'
  };
  return labelMap[name] || name;
};

// 获取测试标签
const getTestLabel = (key: string) => {
  const labelMap: Record<string, string> = {
    health: '健康检查',
    chat: '聊天功能',
    text: '文本查询'
  };
  return labelMap[key] || key;
};

// 获取测试状态文本
const getTestStatusText = () => {
  if (!testResult.value) return '';
  const allSuccess = Object.values(testResult.value).every(test => test.status === 'success');
  return allSuccess ? '全部成功' : '部分失败';
};

// 获取测试状态类型
const getTestStatusType = () => {
  if (!testResult.value) return 'info';
  const allSuccess = Object.values(testResult.value).every(test => test.status === 'success');
  return allSuccess ? 'success' : 'warning';
};

onMounted(() => {
  refreshStatus();
});
</script>

<style scoped>
.service-status {
  margin-bottom: 16px;
}

.test-result {
  margin-top: 16px;
}

.error-text {
  color: #ff4d4f;
  margin-left: 8px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
}
</style>
