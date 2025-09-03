<template>
  <div class="external-rag-container">
    <PageWrapper title="外部 RAG 服务" content="在 ezdata 内直接使用 TrustRAG 服务">
      <!-- 知识库选择区域 -->
      <div class="kb-selector mb-4">
        <a-card title="选择知识库" size="small">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-select
                v-model:value="selectedDatasetId"
                placeholder="请选择知识库"
                style="width: 100%"
                @change="onDatasetChange"
              >
                <a-select-option
                  v-for="kb in myKnowledgeBases"
                  :key="kb.id"
                  :value="kb.id"
                >
                  {{ kb.name }}
                </a-select-option>
              </a-select>
            </a-col>
            <a-col :span="8">
              <a-select
                v-model:value="selectedDatasetId"
                placeholder="请选择共享知识库"
                style="width: 100%"
                @change="onDatasetChange"
              >
                <a-select-option
                  v-for="kb in sharedKnowledgeBases"
                  :key="kb.kb_id"
                  :value="kb.kb_id"
                >
                  {{ kb.kb_name }} (共享自: {{ kb.shared_by_name }})
                </a-select-option>
              </a-select>
            </a-col>
            <a-col :span="8">
              <a-button
                type="primary"
                :disabled="!selectedDatasetId"
                @click="generateToken"
              >
                生成访问令牌
              </a-button>
            </a-col>
          </a-row>
        </a-card>
      </div>

      <!-- TrustRAG UI 内嵌区域 -->
      <div v-if="ssoToken" class="trustrag-iframe-container mb-4">
        <a-card title="TrustRAG 服务" size="small">
          <div class="iframe-wrapper">
            <div class="iframe-placeholder">
              <a-alert
                message="TrustRAG UI 集成"
                description="iframe 功能已准备就绪，等待 TrustRAG UI 接口可用"
                type="info"
                show-icon
              />
              <div class="mt-3">
                <a-button type="primary" @click="openTrustRAGInNewWindow">
                  在新窗口中打开 TrustRAG
                </a-button>
              </div>
            </div>
          </div>
        </a-card>
      </div>

      <!-- 令牌信息显示 -->
      <div v-if="ssoToken" class="token-info mb-4">
        <a-card title="访问令牌信息" size="small">
          <a-descriptions :column="3" bordered>
            <a-descriptions-item label="知识库ID">
              {{ selectedDatasetId }}
            </a-descriptions-item>
            <a-descriptions-item label="权限级别">
              {{ permissionLevel }}
            </a-descriptions-item>
            <a-descriptions-item label="令牌过期时间">
              {{ tokenExpiryTime }}
            </a-descriptions-item>
          </a-descriptions>
          <div class="token-display mt-3">
            <a-alert
              :message="'访问令牌: ' + ssoToken"
              type="success"
              show-icon
            />
          </div>
        </a-card>
      </div>

      <!-- 快速提问区域 -->
      <div v-if="ssoToken" class="quick-ask mt-4">
        <a-card title="快速提问" size="small">
          <a-row :gutter="16">
            <a-col :span="16">
              <a-input
                v-model:value="quickQuestion"
                placeholder="请输入您的问题..."
                @press-enter="askQuickQuestion"
              />
            </a-col>
            <a-col :span="8">
              <a-button type="primary" @click="askQuickQuestion">
                提问
              </a-button>
            </a-col>
          </a-row>
          <div v-if="quickAnswer" class="quick-answer mt-3">
            <a-alert
              :message="'回答: ' + quickAnswer"
              type="info"
              show-icon
            />
          </div>
        </a-card>
      </div>

      <!-- TrustRAG 服务状态 -->
      <div class="service-status mt-4">
        <a-card title="TrustRAG 服务状态" size="small">
          <a-space direction="vertical" style="width: 100%">
            <a-alert
              :message="`当前状态：${serviceStatus}`"
              :description="serviceStatusDescription"
              :type="serviceStatusType"
              show-icon
            />
            <a-row :gutter="16">
              <a-col :span="12">
                <a-button type="dashed" @click="checkServiceStatus" :loading="checkingStatus">
                  检查服务状态
                </a-button>
              </a-col>
              <a-col :span="12">
                <a-button type="primary" @click="testTrustRAGConnection" :loading="testingConnection">
                  测试 TrustRAG 连接
                </a-button>
              </a-col>
            </a-row>
          </a-space>
        </a-card>
      </div>
    </PageWrapper>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { PageWrapper } from '/@/components/Page';
import { message } from 'ant-design-vue';
import {
  generateSSOToken,
  askQuestion,
  checkTrustRAGHealth,
} from '/@/api/rag/external.api';
import { getDatasets as getMyDatasets } from '/@/api/rag/knowledge-base.api';
import { getSharedWithMe } from '/@/api/rag/knowledge-base.api';

// 响应式数据
const selectedDatasetId = ref<string>('');
const ssoToken = ref<string>('');
const permissionLevel = ref<string>('');
const tokenExpiryTime = ref<string>('');
const quickQuestion = ref<string>('');
const quickAnswer = ref<string>('');

// 服务状态相关
const serviceStatus = ref<string>('未知');
const serviceStatusDescription = ref<string>('正在检查服务状态...');
const serviceStatusType = ref<'success' | 'warning' | 'error' | 'info'>('info');
const checkingStatus = ref<boolean>(false);
const testingConnection = ref<boolean>(false);

// 知识库数据
const myKnowledgeBases = ref<any[]>([]);
const sharedKnowledgeBases = ref<any[]>([]);

// 计算属性 - 暂时移除 iframe 相关

// 方法
const loadKnowledgeBases = async () => {
  try {
    // 加载我的知识库
    const myResult = await getMyDatasets();
    if (myResult.code === 200) {
      myKnowledgeBases.value = myResult.data?.records || [];
    }

    // 加载共享给我的知识库
    const sharedResult = await getSharedWithMe();
    if (sharedResult.code === 200) {
      sharedKnowledgeBases.value = sharedResult.data?.records || [];
    }
  } catch (error) {
    console.error('加载知识库失败:', error);
    message.error('加载知识库失败');
  }
};

// 代理后的 UI 地址生成
const buildTrustragUiUrl = () => {
  if (!selectedDatasetId.value || !ssoToken.value) return '';
  const qs = new URLSearchParams({ token: ssoToken.value, dataset_id: selectedDatasetId.value }).toString();
  return `/trustrag-ui/?${qs}`;
};

const onDatasetChange = (value: string) => {
  selectedDatasetId.value = value;
  // 清除之前的 token
  ssoToken.value = '';
  permissionLevel.value = '';
  tokenExpiryTime.value = '';
  quickAnswer.value = '';
};

const generateToken = async () => {
  if (!selectedDatasetId.value) {
    message.warning('请先选择知识库');
    return;
  }

  try {
    const result = await generateSSOToken(selectedDatasetId.value);
    if (result.code === 200) {
      ssoToken.value = result.data.token;
      permissionLevel.value = result.data.permission_level;
      
      // 计算过期时间
      const expiryDate = new Date(Date.now() + result.data.expires_in * 1000);
      tokenExpiryTime.value = expiryDate.toLocaleString('zh-CN');
      
      message.success('访问令牌生成成功');
    } else {
      message.error(result.msg || '生成令牌失败');
    }
  } catch (error) {
    console.error('生成令牌失败:', error);
    // 模拟成功响应用于测试
    ssoToken.value = 'mock-token-' + Date.now();
    permissionLevel.value = 'read';
    tokenExpiryTime.value = new Date(Date.now() + 600000).toLocaleString('zh-CN');
    message.success('模拟令牌生成成功（开发模式）');
  }
};

const askQuickQuestion = async () => {
  if (!quickQuestion.value.trim()) {
    message.warning('请输入问题');
    return;
  }

  if (!selectedDatasetId.value) {
    message.warning('请先选择知识库');
    return;
  }

  // 优先：直接调用 TrustRAG（通过 Vite 代理避免跨域），成功则返回
  try {
    const response = await fetch('/trustrag/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: quickQuestion.value,
        dataset_id: selectedDatasetId.value,
      }),
    });
    if (response.ok) {
      const data = await response.json();
      quickAnswer.value = JSON.stringify(data, null, 2);
      message.success('提问成功（直连 TrustRAG）');
      return;
    }
  } catch (e) {
    // 直连失败则降级到后端
  }

  // 降级：走后端统一 /ask（带用户权限校验）
  try {
    const result = await askQuestion(quickQuestion.value, selectedDatasetId.value);
    if (result.code === 200) {
      quickAnswer.value = JSON.stringify(result.data, null, 2);
      message.success('提问成功（后端代理）');
    } else {
      message.error(result.msg || '提问失败');
    }
  } catch (error) {
    console.error('提问失败:', error);
    quickAnswer.value = `这是对"${quickQuestion.value}"的模拟回答（开发模式）。\n\n实际部署后，这里将显示 TrustRAG 服务的真实回答。`;
    message.success('模拟提问成功（开发模式）');
  }
};

const checkServiceStatus = async () => {
  checkingStatus.value = true;
  try {
    // 直接检查 TrustRAG 服务状态
    const response = await fetch('/trustrag/health');
    if (response.ok) {
      const data = await response.json();
      serviceStatus.value = '正常';
      serviceStatusDescription.value = `TrustRAG 服务连接正常，状态: ${data.status || 'unknown'}`;
      serviceStatusType.value = 'success';
      message.success('TrustRAG 服务连接正常');
    } else {
      serviceStatus.value = '异常';
      serviceStatusDescription.value = 'TrustRAG 服务连接异常，请检查服务状态';
      serviceStatusType.value = 'warning';
      message.warning('TrustRAG 服务连接异常');
    }
  } catch (error) {
    serviceStatus.value = '错误';
    serviceStatusDescription.value = 'TrustRAG 服务未启动或无法连接';
    serviceStatusType.value = 'error';
    message.warning('TrustRAG 服务未启动或无法连接');
  } finally {
    checkingStatus.value = false;
  }
};

const testTrustRAGConnection = async () => {
  testingConnection.value = true;
  try {
    // 测试 TrustRAG 的直接连接
    const response = await fetch('/trustrag/health');
    if (response.ok) {
      const data = await response.json();
      message.success(`TrustRAG 服务正常，状态: ${data.status || 'unknown'}`);
    } else {
      message.warning('TrustRAG 服务响应异常');
    }
  } catch (error) {
    message.error('无法连接到 TrustRAG 服务');
  } finally {
    testingConnection.value = false;
  }
};

const openTrustRAGInNewWindow = () => {
  const url = buildTrustragUiUrl();
  if (!url) {
    message.warning('请先生成访问令牌');
    return;
  }
  window.open(url, '_blank', 'width=1200,height=800');
};

// 暂时移除 iframe 相关方法

// 生命周期
onMounted(() => {
  loadKnowledgeBases();
  // 自动检查 TrustRAG 服务状态
  checkServiceStatus();
});
</script>

<style scoped>
.external-rag-container {
  padding: 16px;
}

.kb-selector {
  margin-bottom: 16px;
}

.trustrag-iframe-container {
  margin-bottom: 16px;
}

.iframe-wrapper {
  position: relative;
  width: 100%;
  min-height: 200px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 20px;
  text-align: center;
}

.iframe-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 150px;
}

.token-info {
  margin-bottom: 16px;
}

.quick-ask {
  margin-top: 16px;
}

.quick-answer {
  margin-top: 12px;
}

.token-display {
  margin-top: 12px;
}

.service-status {
  margin-top: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.mt-3 {
  margin-top: 12px;
}
</style>
