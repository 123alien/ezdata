<template>
  <a-modal
    v-model:open="visible"
    :title="notification.title"
    :width="500"
    :footer="null"
    :maskClosable="false"
    :closable="true"
    class="alert-notification-modal"
  >
    <div class="notification-content">
      <!-- 告警级别指示器 -->
      <div class="alert-level-indicator" :class="`level-${notification.level}`">
        <Icon :icon="getLevelIcon(notification.level)" />
        <span class="level-text">{{ getLevelText(notification.level) }}</span>
      </div>

      <!-- 告警内容 -->
      <div class="alert-content">
        <div class="alert-message">
          <Icon icon="ant-design:warning-outlined" />
          <span>{{ notification.content }}</span>
        </div>
        
        <!-- 设备信息 -->
        <div class="device-info" v-if="notification.source">
          <div class="info-item">
            <Icon icon="ant-design:desktop-outlined" />
            <span class="label">设备：</span>
            <span class="value">{{ notification.source }}</span>
          </div>
          <div class="info-item" v-if="notification.metric">
            <Icon icon="ant-design:line-chart-outlined" />
            <span class="label">指标：</span>
            <span class="value">{{ notification.metric }}</span>
          </div>
          <div class="info-item">
            <Icon icon="ant-design:clock-circle-outlined" />
            <span class="label">时间：</span>
            <span class="value">{{ formatTime(notification.create_time) }}</span>
          </div>
        </div>

        <!-- 操作建议 -->
        <div class="action-suggestions" v-if="notification.level >= 2">
          <div class="suggestion-title">
            <Icon icon="ant-design:bulb-outlined" />
            <span>建议操作</span>
          </div>
          <ul class="suggestion-list">
            <li v-if="notification.metric?.includes('温度')">检查空调系统运行状态</li>
            <li v-if="notification.metric?.includes('湿度')">检查除湿设备或通风系统</li>
            <li v-if="notification.metric?.includes('功率')">检查设备负载情况</li>
            <li v-if="notification.metric?.includes('PM')">检查空气净化设备</li>
            <li>联系相关技术人员进行现场检查</li>
          </ul>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="alert-actions">
        <a-button @click="markAsRead" type="primary" :loading="marking">
          <Icon icon="ant-design:check-outlined" />
          已处理
        </a-button>
        <a-button @click="viewDetails" type="default">
          <Icon icon="ant-design:eye-outlined" />
          查看详情
        </a-button>
        <a-button @click="closeModal" type="text">
          <Icon icon="ant-design:close-outlined" />
          稍后处理
        </a-button>
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { Modal as AModal, Button as AButton, message } from 'ant-design-vue'
import { Icon } from '/@/components/Icon'

interface AlertNotification {
  id: string
  title: string
  content: string
  level: number
  source: string
  metric: string
  create_time: string
}

const props = defineProps<{
  notification: AlertNotification
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'mark-read': [id: string]
  'view-details': [id: string]
}>()

const marking = ref(false)

const getLevelIcon = (level: number) => {
  const icons = {
    0: 'ant-design:info-circle-outlined',
    1: 'ant-design:exclamation-circle-outlined', 
    2: 'ant-design:warning-outlined',
    3: 'ant-design:stop-outlined'
  }
  return icons[level] || icons[0]
}

const getLevelText = (level: number) => {
  const texts = {
    0: '低',
    1: '中', 
    2: '高',
    3: '紧急'
  }
  return texts[level] || '未知'
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '未知时间'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const markAsRead = async () => {
  marking.value = true
  try {
    // 这里调用API标记为已读
    await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟API调用
    emit('mark-read', props.notification.id)
    message.success('已标记为已处理')
    closeModal()
  } catch (error) {
    message.error('操作失败，请重试')
  } finally {
    marking.value = false
  }
}

const viewDetails = () => {
  emit('view-details', props.notification.id)
  closeModal()
}

const closeModal = () => {
  emit('update:visible', false)
}
</script>

<style lang="less" scoped>
.alert-notification-modal {
  :deep(.ant-modal-content) {
    border-radius: 12px;
    overflow: hidden;
  }

  :deep(.ant-modal-header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 16px 24px;
    
    .ant-modal-title {
      color: white;
      font-weight: 600;
    }
  }

  :deep(.ant-modal-close) {
    color: white;
    
    &:hover {
      color: rgba(255, 255, 255, 0.8);
    }
  }
}

.notification-content {
  padding: 0;
}

.alert-level-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin: -24px -24px 16px -24px;
  font-weight: 600;
  font-size: 16px;

  &.level-0 {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    color: #1976d2;
  }

  &.level-1 {
    background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 100%);
    color: #f57c00;
  }

  &.level-2 {
    background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
    color: #d32f2f;
  }

  &.level-3 {
    background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
    color: #7b1fa2;
  }
}

.alert-content {
  .alert-message {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 16px;
    color: #333;
  }

  .device-info {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;

    .info-item {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      
      &:last-child {
        margin-bottom: 0;
      }

      .label {
        font-weight: 500;
        color: #666;
        min-width: 50px;
      }

      .value {
        color: #333;
        font-weight: 500;
      }
    }
  }

  .action-suggestions {
    background: #fff7e6;
    border: 1px solid #ffd591;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;

    .suggestion-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #d46b08;
      margin-bottom: 12px;
    }

    .suggestion-list {
      margin: 0;
      padding-left: 20px;
      color: #8c4a00;

      li {
        margin-bottom: 4px;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}

.alert-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;

  .ant-btn {
    border-radius: 6px;
    font-weight: 500;
  }
}
</style>
