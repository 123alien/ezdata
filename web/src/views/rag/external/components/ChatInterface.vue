<template>
  <div class="chat-interface">
    <a-card title="TrustRAG 智能问答" :bordered="false">
      <template #extra>
        <a-space>
          <a-button 
            type="default" 
            size="small" 
            @click="clearChat"
          >
            清空对话
          </a-button>
          <a-button 
            type="primary" 
            size="small" 
            @click="exportChat"
          >
            导出对话
          </a-button>
        </a-space>
      </template>
      
      <!-- 预设问题 -->
      <div class="preset-questions">
        <a-divider orientation="left">预设问题</a-divider>
        <a-space wrap>
          <a-tag
            v-for="question in presetQuestions"
            :key="question"
            class="question-tag"
            @click="askQuestion(question)"
          >
            {{ question }}
          </a-tag>
        </a-space>
      </div>
      
      <!-- 聊天记录 -->
      <div class="chat-messages" ref="chatContainer">
        <div
          v-for="(message, index) in chatMessages"
          :key="index"
          :class="['message', message.role]"
        >
          <div class="message-header">
            <a-avatar :size="32" :style="{ backgroundColor: message.role === 'user' ? '#1890ff' : '#52c41a' }">
              {{ message.role === 'user' ? 'U' : 'A' }}
            </a-avatar>
            <span class="role-text">{{ message.role === 'user' ? '用户' : 'AI助手' }}</span>
            <span class="time-text">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-content">
            <div v-if="message.role === 'user'" class="user-content">
              {{ message.content }}
            </div>
            <div v-else class="assistant-content">
              <div class="content-text" v-html="formatContent(message.content)"></div>
              <div class="message-actions">
                <a-button 
                  type="link" 
                  size="small" 
                  @click="copyContent(message.content)"
                >
                  复制
                </a-button>
                <a-button 
                  type="link" 
                  size="small" 
                  @click="regenerateResponse(index)"
                >
                  重新生成
                </a-button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="message assistant">
          <div class="message-header">
            <a-avatar :size="32" style="background-color: #52c41a">A</a-avatar>
            <span class="role-text">AI助手</span>
          </div>
          <div class="message-content">
            <div class="loading-content">
              <a-spin size="small" />
              <span style="margin-left: 8px">正在思考中...</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="chat-input">
        <a-divider />
        <a-row :gutter="16">
          <a-col :span="20">
            <a-textarea
              v-model:value="inputMessage"
              placeholder="请输入你的问题..."
              :rows="3"
              :disabled="loading"
              @keydown.enter.ctrl="sendMessage"
            />
          </a-col>
          <a-col :span="4">
            <a-space direction="vertical" style="width: 100%">
              <a-button
                type="primary"
                :loading="loading"
                :disabled="!inputMessage.trim()"
                @click="sendMessage"
                style="width: 100%"
              >
                发送
              </a-button>
              <a-tooltip title="Ctrl + Enter 发送">
                <span class="help-text">Ctrl + Enter</span>
              </a-tooltip>
            </a-space>
          </a-col>
        </a-row>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { chat } from '../api/external-rag.api';
import { ChatMessage, presetQuestions } from '../data/external-rag.data';

const chatMessages = ref<ChatMessage[]>([]);
const inputMessage = ref('');
const loading = ref(false);
const chatContainer = ref<HTMLElement>();

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
    
    if (response.code === 200) {
      const aiMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString()
      };
      chatMessages.value.push(aiMessage);
    } else {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `抱歉，处理您的请求时出现错误：${response.msg}`,
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

onMounted(() => {
  // 添加欢迎消息
  chatMessages.value.push({
    role: 'assistant',
    content: '你好！我是基于 TrustRAG 的 AI 助手，可以回答关于汽车保养、维护等方面的问题。请随时向我提问！',
    timestamp: new Date().toISOString()
  });
});
</script>

<style scoped>
.chat-interface {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preset-questions {
  margin-bottom: 16px;
}

.question-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.question-tag:hover {
  background-color: #1890ff;
  color: white;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  max-height: 500px;
  padding: 16px 0;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background-color: #fafafa;
}

.message {
  margin-bottom: 16px;
  padding: 0 16px;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.role-text {
  margin-left: 8px;
  font-weight: 500;
  color: #333;
}

.time-text {
  margin-left: auto;
  font-size: 12px;
  color: #999;
}

.message-content {
  margin-left: 40px;
}

.user-content {
  background-color: #e6f7ff;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid #1890ff;
}

.assistant-content {
  background-color: white;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid #52c41a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.content-text {
  line-height: 1.6;
  margin-bottom: 8px;
}

.message-actions {
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
  text-align: right;
}

.loading-content {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: white;
  border-radius: 8px;
  border-left: 4px solid #52c41a;
}

.chat-input {
  margin-top: 16px;
}

.help-text {
  font-size: 12px;
  color: #999;
  text-align: center;
  display: block;
}

:deep(.ant-card-body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
