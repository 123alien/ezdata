<template>
  <div class="trustrag-ui-container">
    <PageWrapper title="TrustRAG UI" content="TrustRAG 用户界面">
      <!-- 用户信息显示 -->
      <div v-if="userInfo" class="user-info mb-4">
        <a-card title="用户信息" size="small">
          <a-descriptions :column="3" bordered>
            <a-descriptions-item label="用户ID">
              {{ userInfo.user_id }}
            </a-descriptions-item>
            <a-descriptions-item label="租户ID">
              {{ userInfo.tenant_id }}
            </a-descriptions-item>
            <a-descriptions-item label="权限级别">
              {{ userInfo.permission }}
            </a-descriptions-item>
            <a-descriptions-item label="数据集ID">
              {{ userInfo.dataset_id }}
            </a-descriptions-item>
            <a-descriptions-item label="命名空间">
              {{ userInfo.namespace }}
            </a-descriptions-item>
            <a-descriptions-item label="令牌状态">
              <a-tag :color="tokenValid ? 'green' : 'red'">
                {{ tokenValid ? '有效' : '无效' }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </div>

      <!-- 接口配置 -->
      <div class="api-config mb-4">
        <a-card title="接口配置" size="small">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-input
                v-model:value="apiBaseUrl"
                placeholder="TrustRAG API 基础地址"
                addon-before="API 地址"
              />
            </a-col>
            <a-col :span="6">
              <a-button @click="testConnection" :loading="testingConnection">
                测试连接
              </a-button>
            </a-col>
            <a-col :span="6">
              <a-tag :color="connectionStatus === 'success' ? 'green' : connectionStatus === 'error' ? 'red' : 'default'">
                {{ connectionStatus === 'success' ? '连接正常' : connectionStatus === 'error' ? '连接失败' : '未测试' }}
              </a-tag>
            </a-col>
          </a-row>
        </a-card>
      </div>

      <!-- 聊天界面 -->
      <div class="chat-interface">
        <a-card title="TrustRAG 聊天" size="small">
          <div class="chat-container">
            <!-- 消息历史 -->
            <div class="message-history" ref="messageHistory">
              <div
                v-for="(message, index) in messages"
                :key="index"
                :class="['message', message.type]"
              >
                <div class="message-content">
                  <div class="message-text">{{ message.content }}</div>
                  <div class="message-time">{{ message.time }}</div>
                </div>
              </div>
            </div>

            <!-- 输入区域 -->
            <div class="input-area">
              <a-row :gutter="8">
                <a-col :span="18">
                  <a-input
                    v-model:value="currentMessage"
                    placeholder="请输入您的问题..."
                    @press-enter="sendMessage"
                    :disabled="loading"
                  />
                </a-col>
                <a-col :span="6">
                  <a-space>
                    <a-select
                      v-model:value="selectedMode"
                      style="width: 100px"
                      :disabled="loading"
                    >
                      <a-select-option value="auto">自动</a-select-option>
                      <a-select-option value="extract">抽取</a-select-option>
                      <a-select-option value="generate">生成</a-select-option>
                    </a-select>
                    <a-button
                      type="primary"
                      @click="sendMessage"
                      :loading="loading"
                      :disabled="!currentMessage.trim()"
                    >
                      发送
                    </a-button>
                  </a-space>
                </a-col>
              </a-row>
            </div>
          </div>
        </a-card>
      </div>
    </PageWrapper>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { PageWrapper } from '/@/components/Page';

interface Message {
  type: 'user' | 'assistant';
  content: string;
  time: string;
}

interface UserInfo {
  user_id: string;
  tenant_id: number;
  dataset_id: string;
  namespace: string;
  permission: string;
}

const route = useRoute();
const messages = ref<Message[]>([]);
const currentMessage = ref('');
const selectedMode = ref('auto');
const loading = ref(false);
const userInfo = ref<UserInfo | null>(null);
const tokenValid = ref(false);
const messageHistory = ref<HTMLElement>();

// API 配置
const apiBaseUrl = ref('http://localhost:8217');
const connectionStatus = ref<'success' | 'error' | 'default'>('default');
const testingConnection = ref(false);

// 解析 URL 参数
const parseUrlParams = () => {
  const token = route.query.token as string;
  const datasetId = route.query.dataset_id as string;
  const namespace = route.query.namespace as string;

  if (!token) {
    message.error('缺少访问令牌');
    return;
  }

  try {
    // 解析 JWT token
    const payload = JSON.parse(atob(token.split('.')[1]));
    userInfo.value = {
      user_id: payload.user_id,
      tenant_id: payload.tenant_id,
      dataset_id: datasetId || payload.dataset_id,
      namespace: namespace || payload.namespace,
      permission: payload.permission,
    };
    tokenValid.value = payload.exp > Date.now() / 1000;
  } catch (error) {
    message.error('令牌解析失败');
    console.error('Token parse error:', error);
  }
};

// 测试连接
const testConnection = async () => {
  testingConnection.value = true;
  connectionStatus.value = 'default';
  
  try {
    const response = await fetch(`${apiBaseUrl.value}/health`, {
      method: 'GET',
      timeout: 5000,
    } as any);
    
    if (response.ok) {
      connectionStatus.value = 'success';
      message.success('连接测试成功');
    } else {
      connectionStatus.value = 'error';
      message.error(`连接测试失败: ${response.status}`);
    }
  } catch (error) {
    connectionStatus.value = 'error';
    message.error(`连接测试失败: ${error}`);
  } finally {
    testingConnection.value = false;
  }
};

// 发送消息
const sendMessage = async () => {
  if (!currentMessage.value.trim() || loading.value) return;

  const userMessage: Message = {
    type: 'user',
    content: currentMessage.value,
    time: new Date().toLocaleTimeString(),
  };

  messages.value.push(userMessage);
  const question = currentMessage.value;
  currentMessage.value = '';
  loading.value = true;

  // 滚动到底部
  await nextTick();
  scrollToBottom();

  try {
    const token = route.query.token as string;
    const response = await fetch(`${apiBaseUrl.value}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        message: question,
        namespace: userInfo.value?.namespace,
        mode: selectedMode.value,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      const assistantMessage: Message = {
        type: 'assistant',
        content: data.response || '无响应内容',
        time: new Date().toLocaleTimeString(),
      };
      messages.value.push(assistantMessage);
    } else {
      const errorMessage: Message = {
        type: 'assistant',
        content: `错误: ${response.status} ${response.statusText}`,
        time: new Date().toLocaleTimeString(),
      };
      messages.value.push(errorMessage);
    }
  } catch (error) {
    const errorMessage: Message = {
      type: 'assistant',
      content: `网络错误: ${error}`,
      time: new Date().toLocaleTimeString(),
    };
    messages.value.push(errorMessage);
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messageHistory.value) {
    messageHistory.value.scrollTop = messageHistory.value.scrollHeight;
  }
};

// 生命周期
onMounted(() => {
  parseUrlParams();
  if (userInfo.value) {
    const welcomeMessage: Message = {
      type: 'assistant',
      content: `欢迎使用 TrustRAG！您当前在命名空间 "${userInfo.value.namespace}" 中。请提出您的问题。`,
      time: new Date().toLocaleTimeString(),
    };
    messages.value.push(welcomeMessage);
  }
});
</script>

<style scoped>
.trustrag-ui-container {
  padding: 20px;
}

.user-info {
  margin-bottom: 20px;
}

.api-config {
  margin-bottom: 20px;
}

.chat-interface {
  height: 600px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.message-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  margin-bottom: 16px;
  background-color: #fafafa;
}

.message {
  margin-bottom: 16px;
}

.message.user {
  text-align: right;
}

.message.assistant {
  text-align: left;
}

.message-content {
  display: inline-block;
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 8px;
  word-wrap: break-word;
}

.message.user .message-content {
  background-color: #1890ff;
  color: white;
}

.message.assistant .message-content {
  background-color: white;
  border: 1px solid #d9d9d9;
}

.message-text {
  margin-bottom: 4px;
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
}

.input-area {
  padding: 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background-color: white;
}
</style>
