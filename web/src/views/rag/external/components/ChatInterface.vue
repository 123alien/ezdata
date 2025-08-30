<template>
  <div class="chat-container">
    <div class="chat-wrapper">
      <!-- 左侧聊天区域 - 占据主要空间 -->
      <div class="chat-main">
        <!-- 顶部品牌栏 -->
        <div class="brand-header">
          <div class="brand-info">
            <div class="logo">🤖</div>
            <div class="brand-text">
              <h1>TrustRAG</h1>
              <p>智能知识问答助手</p>
            </div>
          </div>
          <div class="header-actions">
            <button class="action-btn" @click="refreshChat">🔄</button>
            <button class="action-btn" @click="showSettings = true">⚙️</button>
            <button class="action-btn" @click="exportChat">📤</button>
          </div>
        </div>

        <!-- 聊天消息区域 - 占据大部分空间 -->
        <div class="messages-container" ref="chatContainer">
          <div
            v-for="(message, index) in (chatMessages || [])"
            :key="index"
            :class="['message-wrapper', message.role]"
          >
            <div v-if="message.role === 'user'" class="user-message">
              <div class="message-bubble user">
                {{ message.content }}
              </div>
              <div class="message-time">{{ formatTime(message.timestamp || '') }}</div>
            </div>
            <div v-else class="assistant-message">
              <div class="assistant-avatar">🤖</div>
              <div class="message-bubble assistant">
                <div class="message-content" v-html="formatContent(message.content)"></div>
                <div class="message-actions">
                  <button class="action-link" @click="copyContent(message.content)">复制</button>
                  <button class="action-link" @click="regenerateResponse(index)">重新生成</button>
                </div>
              </div>
              <div class="message-time">{{ formatTime(message.timestamp || '') }}</div>
            </div>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="loading" class="message-wrapper assistant">
            <div class="assistant-avatar">🤖</div>
            <div class="message-bubble assistant loading">
              <div class="loading-content">
                <div class="spinner"></div>
                <span>正在思考中...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-section">
          <div class="input-container">
            <textarea
              v-model="inputMessage"
              placeholder="输入你的问题，按 Enter 发送..."
              :disabled="loading"
              @keydown.enter.ctrl="sendMessage"
              class="message-input"
            ></textarea>
            <button
              :disabled="!inputMessage.trim() || loading"
              @click="sendMessage"
              class="send-btn"
            >
              <span class="send-icon">✈️</span>
              <span class="send-text">发送</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧功能边栏 -->
      <div class="chat-sidebar">
        <!-- 预设问题 -->
        <div class="sidebar-section">
          <h3>💡 预设问题</h3>
          <div class="question-tags">
            <button
              v-for="question in (presetQuestions || [])"
              :key="question"
              class="question-tag"
              @click="askQuestion(question)"
            >
              {{ question }}
            </button>
          </div>
        </div>

        <!-- 对话历史 -->
        <div class="sidebar-section">
          <h3>📚 对话历史</h3>
          <div class="history-cards">
            <div class="history-card active">
              <div class="card-title">汽车保养咨询</div>
              <div class="card-meta">共 {{ chatMessages.length }} 条对话</div>
              <div class="card-time">{{ formatTime(new Date().toISOString()) }}</div>
            </div>
            <div class="history-card">
              <div class="card-title">轮胎维护指南</div>
              <div class="card-meta">共 15 条对话</div>
              <div class="card-time">2025/8/30 14:20:15</div>
            </div>
          </div>
        </div>

        <!-- 控制按钮 -->
        <div class="sidebar-section">
          <h3>🛠️ 操作</h3>
          <div class="control-buttons">
            <button class="control-btn" @click="clearChat">🗑️ 清空对话</button>
            <button class="control-btn primary" @click="exportChat">📥 导出对话</button>
            <button class="control-btn">➕ 新的对话</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置面板 -->
    <div v-if="showSettings" class="settings-overlay" @click="showSettings = false">
      <div class="settings-panel" @click.stop>
        <div class="settings-header">
          <h2>⚙️ 系统设置</h2>
          <button class="close-btn" @click="showSettings = false">✕</button>
        </div>
        
        <div class="settings-content">
          <!-- 服务状态 -->
          <div class="setting-section">
            <h3>🔍 服务状态</h3>
            <div class="status-grid">
              <div class="status-item">
                <div class="status-label">TrustRAG 服务</div>
                <div class="status-value" :class="serviceStatus?.health?.status || 'unknown'">
                  {{ serviceStatus?.health?.status || '未知' }}
                </div>
              </div>
              <div class="status-item">
                <div class="status-label">版本</div>
                <div class="status-value">{{ serviceStatus?.health?.version || '未知' }}</div>
              </div>
              <div class="status-item">
                <div class="status-label">最后更新</div>
                <div class="status-value">{{ formatDateTime(serviceStatus?.timestamp) }}</div>
              </div>
            </div>
          </div>

          <!-- 组件状态 -->
          <div class="setting-section">
            <h3>🧩 组件状态</h3>
            <div class="component-grid">
              <div 
                v-for="(status, component) in (serviceStatus?.health?.components || {})" 
                :key="component"
                class="component-item"
                :class="status ? 'healthy' : 'unhealthy'"
              >
                <div class="component-icon">{{ getComponentIcon(String(component)) }}</div>
                <div class="component-info">
                  <div class="component-name">{{ getComponentName(String(component)) }}</div>
                  <div class="component-status">{{ status ? '正常' : '异常' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 服务端点 -->
          <div class="setting-section">
            <h3>🌐 服务端点</h3>
            <div class="endpoints-list">
              <div 
                v-for="(url, name) in (serviceStatus?.endpoints || {})" 
                :key="name"
                class="endpoint-item"
              >
                <div class="endpoint-info">
                  <div class="endpoint-name">{{ getEndpointName(String(name)) }}</div>
                  <div class="endpoint-url">{{ url }}</div>
                </div>
                <button class="test-btn" @click="testEndpoint(String(name), url)">测试</button>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="setting-section">
            <h3>🔄 服务操作</h3>
            <div class="action-grid">
              <button class="action-btn primary" @click="refreshServiceStatus">
                🔄 刷新状态
              </button>
              <button class="action-btn" @click="initializeService">
                🚀 初始化服务
              </button>
              <button class="action-btn" @click="testConnectionLocal">
                🧪 测试连接
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { chat, healthCheck, initializeRAG, getStatus, testConnection } from '../api/external-rag.api';
import { ChatMessage, presetQuestions } from '../data/external-rag.data';

const chatMessages = ref<ChatMessage[]>([]);
const inputMessage = ref('');
const loading = ref(false);
const chatContainer = ref<HTMLElement>();
const showSettings = ref(false);
const serviceStatus = ref<any>(null);

// 刷新聊天
const refreshChat = () => {
  message.success('聊天界面已刷新');
};

// 刷新服务状态
const refreshServiceStatus = async () => {
  try {
    const response = await getStatus();
    if (response) {
      serviceStatus.value = response;
      message.success('服务状态已刷新');
    }
  } catch (error) {
    message.error('刷新服务状态失败');
  }
};

// 初始化服务
const initializeService = async () => {
  try {
    const response = await initializeRAG();
    if (response) {
      message.success('服务初始化成功');
      await refreshServiceStatus();
    }
  } catch (error) {
    message.error('服务初始化失败');
  }
};

// 测试连接
const testConnectionLocal = async () => {
  try {
    const response = await testConnection();
    if (response) {
      message.success('连接测试成功');
    }
  } catch (error) {
    message.error('连接测试失败');
  }
};

// 测试端点
const testEndpoint = async (name: string, url: string) => {
  try {
    const response = await fetch(url);
    if (response.ok) {
      message.success(`${getEndpointName(name)} 端点正常`);
    } else {
      message.error(`${getEndpointName(name)} 端点异常`);
    }
  } catch (error) {
    message.error(`${getEndpointName(name)} 端点连接失败`);
  }
};

// 获取组件图标
const getComponentIcon = (component: string) => {
  const icons: { [key: string]: string } = {
    chunks_loaded: '📚',
    index_ready: '🔍',
    rag_system: '🤖'
  };
  return icons[component] || '❓';
};

// 获取组件名称
const getComponentName = (component: string) => {
  const names: { [key: string]: string } = {
    chunks_loaded: '数据块加载',
    index_ready: '索引就绪',
    rag_system: 'RAG 系统'
  };
  return names[component] || component;
};

// 获取端点名称
const getEndpointName = (name: string) => {
  const names: { [key: string]: string } = {
    health: '健康检查',
    initialize: '初始化',
    chat: '聊天',
    text: '文本处理',
    openai: 'OpenAI 兼容',
    search: '搜索',
    status: '状态查询',
    test: '连接测试'
  };
  return names[name] || name;
};

// 格式化日期时间
const formatDateTime = (timestamp: string) => {
  if (!timestamp) return '未知';
  try {
    return new Date(timestamp).toLocaleString('zh-CN');
  } catch {
    return timestamp;
  }
};

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return;
  
  const userMessage: ChatMessage = {
    role: 'user',
    content: inputMessage.value.trim(),
    timestamp: new Date().toISOString()
  };
  
  chatMessages.value.push(userMessage);
  const currentMessage = inputMessage.value.trim();
  inputMessage.value = '';
  
  // 滚动到底部
  await nextTick();
  scrollToBottom();
  
  // 发送到AI
  try {
    loading.value = true;
    const response = await chat(currentMessage);
    
    if (response && response.response) {
      const aiMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };
      chatMessages.value.push(aiMessage);
    } else {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `抱歉，处理您的请求时出现错误：${response?.msg || '未知错误'}`,
        timestamp: new Date().toISOString()
      };
      chatMessages.value.push(errorMessage);
    }
  } catch (error) {
    const errorMessage: ChatMessage = {
      role: 'assistant',
      content: `抱歉，网络请求失败：${error}`,
      timestamp: new Date().toISOString()
    };
    chatMessages.value.push(errorMessage);
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

// 点击预设问题
const askQuestion = (question: string) => {
  inputMessage.value = question;
  sendMessage();
};

// 清空对话
const clearChat = () => {
  chatMessages.value = [];
  message.success('对话已清空');
};

// 导出对话
const exportChat = () => {
  if (chatMessages.value.length === 0) {
    message.warning('没有对话内容可导出');
    return;
  }
  
  const content = chatMessages.value
    .map(msg => `${msg.role === 'user' ? '用户' : 'AI助手'}: ${msg.content}`)
    .join('\n\n');
  
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `TrustRAG对话记录_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
  a.click();
  URL.revokeObjectURL(url);
  message.success('对话记录导出成功');
};

// 复制内容
const copyContent = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content);
    message.success('内容已复制到剪贴板');
  } catch (error) {
    message.error('复制失败');
  }
};

// 重新生成响应
const regenerateResponse = async (index: number) => {
  if (index <= 0 || chatMessages.value[index - 1].role !== 'user') {
    message.warning('无法重新生成此响应');
    return;
  }
  
  const userMessage = chatMessages.value[index - 1];
  // 删除当前AI响应
  chatMessages.value.splice(index, 1);
  
  // 重新发送用户消息
  inputMessage.value = userMessage.content;
  await sendMessage();
};

// 滚动到底部
const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

// 格式化时间
const formatTime = (timestamp: string) => {
  if (!timestamp) return '';
  try {
    return new Date(timestamp).toLocaleTimeString('zh-CN');
  } catch {
    return timestamp;
  }
};

// 格式化内容（支持换行）
const formatContent = (content: string) => {
  return content.replace(/\n/g, '<br>');
};

// 监听消息变化，自动滚动
watch(chatMessages, () => {
  nextTick(() => {
    scrollToBottom();
  });
});

onMounted(async () => {
  // 添加欢迎消息
  chatMessages.value.push({
    role: 'assistant',
    content: '你好！我是基于 TrustRAG 的 AI 助手，可以回答关于汽车保养、维护等方面的问题。请随时向我提问！',
    timestamp: new Date().toISOString()
  });
  
  // 获取初始服务状态
  await refreshServiceStatus();
});
</script>

<style scoped>
.chat-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  justify-content: center !important;
  align-items: center !important;
  padding: 20px;
  box-sizing: border-box;
}

.chat-wrapper {
  display: flex;
  max-width: 1400px;
  width: 100%;
  height: 95%;
  gap: 20px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .chat-wrapper {
    max-width: 1200px;
  }
}

@media (max-width: 768px) {
  .chat-wrapper {
    max-width: 100%;
    flex-direction: column;
    height: auto;
  }
  
  .chat-sidebar {
    width: 100%;
    margin-top: 20px;
  }
}

/* 左侧主聊天区域 - 占据大部分空间 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  margin: 0;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  min-width: 0; /* 确保flex子元素可以收缩 */
}

/* 右侧功能边栏 */
.chat-sidebar {
  width: 320px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  margin: 0;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  flex-shrink: 0;
}

/* 品牌头部 */
.brand-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.brand-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  font-size: 40px;
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.brand-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
}

.brand-text p {
  margin: 4px 0 0 0;
  font-size: 16px;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 12px;
  position: relative;
  z-index: 20;
}

.action-btn {
  width: 44px;
  height: 44px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 18px;
  cursor: pointer !important;
  transition: all 0.3s;
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 9999 !important;
  user-select: none;
  pointer-events: auto !important;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

/* 消息容器 - 占据大部分空间 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  background: #f8f9fa;
  min-height: 0; /* 确保flex子元素可以收缩 */
}

.message-wrapper {
  margin-bottom: 24px;
}

.user-message {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.assistant-message {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.assistant-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.message-bubble {
  max-width: 70%;
  padding: 20px 24px;
  border-radius: 20px;
  font-size: 16px;
  line-height: 1.6;
  word-wrap: break-word;
  position: relative;
}

.message-bubble.user {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  border-radius: 20px 20px 4px 20px;
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.3);
}

.message-bubble.assistant {
  background: white;
  color: #333;
  border-radius: 20px 20px 20px 4px;
  border: 1px solid #e9ecef;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.message-content {
  margin-bottom: 16px;
}

.message-actions {
  border-top: 1px solid #e9ecef;
  padding-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.action-link {
  background: none;
  border: none;
  color: #1890ff;
  cursor: pointer !important;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
  position: relative;
  z-index: 9999 !important;
  user-select: none;
  pointer-events: auto !important;
}

.action-link:hover {
  background: #f0f8ff;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.user-message .message-time {
  margin-right: 8px;
}

.assistant-message .message-time {
  margin-left: 64px;
}

/* 加载状态 */
.loading-content {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #666;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e9ecef;
  border-top: 2px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 输入区域 */
.input-section {
  padding: 24px 32px;
  background: white;
  border-top: 1px solid #e9ecef;
  flex-shrink: 0;
}

.input-container {
  display: flex;
  gap: 16px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  border: 2px solid #e1e5e9;
  border-radius: 16px;
  padding: 16px 20px;
  font-size: 16px;
  line-height: 1.6;
  resize: none;
  transition: all 0.3s;
  font-family: inherit;
}

.message-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.1);
}

.send-btn {
  height: 56px;
  padding: 0 32px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer !important;
  transition: all 0.3s;
  position: relative;
  z-index: 9999 !important;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.3);
  position: relative;
  z-index: 9999 !important;
  user-select: none;
  pointer-events: auto !important;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(24, 144, 255, 0.4);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-icon {
  font-size: 18px;
}

/* 右侧边栏样式 */
.sidebar-section {
  margin-bottom: 32px;
}

.sidebar-section:last-child {
  margin-bottom: 0;
}

.sidebar-section h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.question-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-tag {
  padding: 10px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 12px;
  background: white;
  color: #666;
  cursor: pointer !important;
  transition: all 0.3s;
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  width: 100%;
  position: relative;
  z-index: 9999 !important;
  user-select: none;
  pointer-events: auto !important;
}

.question-tag:hover {
  border-color: #1890ff;
  background: #f0f8ff;
  color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.history-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  padding: 16px;
  background: white;
  border: 2px solid #e1e5e9;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.history-card:hover {
  border-color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.history-card.active {
  border-color: #1890ff;
  background: #f0f8ff;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}

.card-meta {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.card-time {
  font-size: 11px;
  color: #999;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-btn {
  padding: 10px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 10px;
  background: white;
  color: #666;
  cursor: pointer !important;
  transition: all 0.3s;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  justify-content: center;
  position: relative;
  z-index: 9999 !important;
  user-select: none;
  pointer-events: auto !important;
}

.control-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.control-btn.primary {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  border-color: #1890ff;
}

.control-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

/* 设置面板样式 */
.settings-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.settings-panel {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px 20px 0 0;
}

.settings-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.close-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: white;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(10px);
  position: relative;
  z-index: 9999 !important;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.settings-content {
  padding: 32px;
}

.setting-section {
  margin-bottom: 32px;
}

.setting-section:last-child {
  margin-bottom: 0;
}

.setting-section h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 服务状态网格 */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.status-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.status-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.status-value {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.status-value.healthy {
  color: #52c41a;
}

.status-value.unhealthy {
  color: #ff4d4f;
}

.status-value.unknown {
  color: #faad14;
}

/* 组件状态网格 */
.component-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.component-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  transition: all 0.2s;
}

.component-item.healthy {
  border-color: #52c41a;
  background: #f6ffed;
}

.component-item.unhealthy {
  border-color: #ff4d4f;
  background: #fff2f0;
}

.component-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
}

.component-info {
  flex: 1;
}

.component-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.component-status {
  font-size: 12px;
  color: #666;
}

/* 服务端点列表 */
.endpoints-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.endpoint-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.endpoint-info {
  flex: 1;
}

.endpoint-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.endpoint-url {
  font-size: 12px;
  color: #666;
  font-family: monospace;
  word-break: break-all;
}

.test-btn {
  padding: 8px 16px;
  border: 1px solid #1890ff;
  border-radius: 8px;
  background: white;
  color: #1890ff;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  white-space: nowrap;
  position: relative;
  z-index: 9999 !important;
}

.test-btn:hover {
  background: #1890ff;
  color: white;
}

/* 操作按钮网格 */
.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.action-btn {
  padding: 12px 20px;
  border: 2px solid #e1e5e9;
  border-radius: 12px;
  background: white;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  position: relative;
  z-index: 9999 !important;
}

.action-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.action-btn.primary {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  border-color: #1890ff;
}

.action-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar,
.chat-sidebar::-webkit-scrollbar,
.settings-panel::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track,
.chat-sidebar::-webkit-scrollbar-track,
.settings-panel::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb,
.chat-sidebar::-webkit-scrollbar-thumb,
.settings-panel::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover,
.chat-sidebar::-webkit-scrollbar-thumb:hover,
.settings-panel::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .chat-sidebar {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }
  
  .chat-main {
    margin: 10px;
  }
  
  .chat-sidebar {
    width: auto;
    margin: 0 10px 10px 10px;
  }
  
  .settings-panel {
    width: 95%;
    margin: 20px;
  }
  
  .settings-content {
    padding: 20px;
  }
  
  .status-grid,
  .component-grid,
  .action-grid {
    grid-template-columns: 1fr;
  }
}
</style>
