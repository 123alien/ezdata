<template>
  <div class="external-rag-container">
    <PageWrapper title="外部 RAG 服务" content="在数字金融实验室内直接使用 TrustRAG 服务">
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
              <a-input
                v-model:value="namespace"
                placeholder="可选：TrustRAG namespace（不绑定时可直接填写）"
              />
            </a-col>
            <a-col :span="8">
              <a-button
                type="primary"
                :disabled="!selectedDatasetId && !namespace"
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
            <div style="display: flex; align-items: center; gap: 8px;">
              <a-alert
                :message="'访问令牌: ' + ssoToken"
                type="success"
                show-icon
                style="flex: 1;"
              />
              <a-button
                type="primary"
                :icon="h(CopyOutlined)"
                @click="copyToken"
              >
                复制令牌
              </a-button>
            </div>
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
import { ref, onMounted, h } from 'vue';
import { PageWrapper } from '/@/components/Page';
import { message } from 'ant-design-vue';
import { CopyOutlined } from '@ant-design/icons-vue';
import {
  generateSSOToken,
  askQuestion,
} from '/@/api/rag/external.api';
import { getDatasets as getMyDatasets } from '/@/api/rag/knowledge-base.api';
import { getSharedWithMe } from '/@/api/rag/knowledge-base.api';
import { getKnowledgeBaseBinding } from '/@/api/rag/kb-binding.api';

// 响应式数据
const selectedDatasetId = ref<string>('');
const namespace = ref<string>('');
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

// 打开外部 NextChat 实例
const buildTrustragUiUrl = () => {
  return 'http://1118qg49520ma.vicp.fun';
};

const onDatasetChange = async (value: string) => {
  selectedDatasetId.value = value;
  // 清除之前的 token
  ssoToken.value = '';
  permissionLevel.value = '';
  tokenExpiryTime.value = '';
  quickAnswer.value = '';
  
  // 如果选择了知识库，尝试自动获取绑定的namespace
  if (value) {
    try {
      const res = await getKnowledgeBaseBinding({ kid: value });
      if (res.success && res.result) {
        namespace.value = res.result.namespace;
        message.info(`已自动填入绑定的namespace: ${res.result.namespace}`);
      } else {
        // 没有绑定信息，清空namespace
        namespace.value = '';
      }
    } catch (error) {
      console.error('获取绑定信息失败:', error);
      namespace.value = '';
    }
  }
};



const generateToken = async () => {
  if (!selectedDatasetId.value && !namespace.value) {
    message.warning('请先选择知识库或填写 namespace');
    return;
  }

  try {
    const result = await generateSSOToken(selectedDatasetId.value || undefined, namespace.value || undefined);
    if (result.code === 200) {
      ssoToken.value = result.data.token;
      permissionLevel.value = result.data.permission_level;
      
      const expiryDate = new Date(Date.now() + result.data.expires_in * 1000);
      tokenExpiryTime.value = expiryDate.toLocaleString('zh-CN');
      
      message.success('访问令牌生成成功');
    } else {
      message.error(result.msg || '生成令牌失败');
    }
  } catch (error) {
    console.error('生成令牌失败:', error);
    message.error('生成令牌失败');
  }
};

const askQuickQuestion = async () => {
  if (!quickQuestion.value.trim()) {
    message.warning('请输入问题');
    return;
  }

  if (!selectedDatasetId.value && !namespace.value) {
    message.warning('请先选择知识库或填写 namespace');
    return;
  }

  // 优先直连 TrustRAG（使用 SSO Token，并按 JSON 解析 response 字段）
  try {
    const isDefinitionQuestion = /是什么|定义|概念|又称|亦称|是指/.test(quickQuestion.value);
    const mode = isDefinitionQuestion ? 'extract' : 'auto';
    const response = await fetch('/trustrag/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(ssoToken.value ? { Authorization: `Bearer ${ssoToken.value}` } : {}),
      },
      body: JSON.stringify({
        message: quickQuestion.value,
        dataset_id: selectedDatasetId.value || null,
        namespace: namespace.value || null,
        mode,
      }),
    });
    if (response.ok) {
      const data = await response.json();
      quickAnswer.value = data?.response ?? JSON.stringify(data, null, 2);
      message.success(`提问成功（直连 TrustRAG，模式: ${mode}）`);
      return;
    }
  } catch {}

  // 降级走后端（代理）
  try {
    const result = await askQuestion(
      quickQuestion.value, 
      selectedDatasetId.value || undefined, 
      namespace.value || undefined
    );
    if (result.code === 200) {
      if (result.data && result.data.result && result.data.result.response) {
        quickAnswer.value = result.data.result.response;
      } else if (result.data && result.data.response) {
        quickAnswer.value = result.data.response;
      } else {
        quickAnswer.value = JSON.stringify(result.data, null, 2);
      }
      message.success('提问成功（后端代理）');
    } else {
      message.error(result.msg || '提问失败');
    }
  } catch (error) {
    console.error('提问失败:', error);
    message.error('提问失败');
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

const copyToken = async () => {
  if (!ssoToken.value) {
    message.warning('没有可复制的令牌');
    return;
  }
  
  try {
    await navigator.clipboard.writeText(ssoToken.value);
    message.success('令牌已复制到剪贴板');
  } catch (error) {
    // 降级方案：使用传统方法
    const textarea = document.createElement('textarea');
    textarea.value = ssoToken.value;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    message.success('令牌已复制到剪贴板');
  }
};

const openTrustRAGInNewWindow = () => {
  const url = buildTrustragUiUrl();
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
