/**
 * 告警通知管理器
 */
import { ref, reactive } from 'vue'
import { Modal } from 'ant-design-vue'

export interface AlertNotification {
  id: string
  title: string
  content: string
  level: number
  source: string
  metric: string
  create_time: string
}

class AlertNotificationManager {
  private notifications = ref<AlertNotification[]>([])
  private currentModal = ref<any>(null)
  private isShowing = ref(false)

  /**
   * 添加新的告警通知
   */
  addNotification(notification: AlertNotification) {
    // 检查是否已存在相同ID的通知
    const exists = this.notifications.value.find(n => n.id === notification.id)
    if (exists) {
      return
    }

    this.notifications.value.unshift(notification)
    
    // 如果当前没有显示通知，立即显示
    if (!this.isShowing.value) {
      this.showNextNotification()
    }
  }

  /**
   * 显示下一个通知
   */
  private showNextNotification() {
    if (this.notifications.value.length === 0) {
      this.isShowing.value = false
      return
    }

    const notification = this.notifications.value[0]
    this.showNotificationModal(notification)
  }

  /**
   * 显示通知弹窗
   */
  private showNotificationModal(notification: AlertNotification) {
    this.isShowing.value = true
    
    // 根据告警级别设置不同的弹窗样式
    const modalProps = this.getModalProps(notification.level)
    
    // 创建简洁的标题
    const titleHtml = `🔔 ${notification.title}`
    
    // 创建简洁的内容
    const contentHtml = this.renderSimpleNotificationContent(notification)
    
    this.currentModal.value = Modal.confirm({
      title: titleHtml,
      content: contentHtml,
      width: 500,
      maskClosable: false,
      closable: true,
      okText: '已处理',
      cancelText: '稍后处理',
      onOk: () => this.handleNotificationAction(notification.id, 'read'),
      onCancel: () => this.handleNotificationAction(notification.id, 'later'),
      ...modalProps
    })
  }

  /**
   * 根据告警级别获取弹窗属性
   */
  private getModalProps(level: number) {
    const levelColor = this.getLevelColor(level)
    
    return {
      okType: 'primary',
      icon: null,
      className: 'modern-alert-modal',
      style: {
        '--alert-color': levelColor
      }
    }
  }

  /**
   * 渲染纯文本通知内容
   */
  private renderSimpleNotificationContent(notification: AlertNotification) {
    const suggestions = this.getSuggestions(notification.metric)
    
    let content = `⚠️ ${notification.content}\n\n`
    content += `设备：${notification.source}\n`
    if (notification.metric) {
      content += `指标：${notification.metric}\n`
    }
    content += `时间：${this.formatTime(notification.create_time)}\n\n`
    
    if (notification.level >= 2) {
      content += `💡 建议操作：\n`
      suggestions.slice(0, 2).forEach(suggestion => {
        content += `• ${suggestion}\n`
      })
    }
    
    return content
  }

  /**
   * 获取操作建议
   */
  private getSuggestions(metric: string) {
    const suggestions = []
    
    if (metric?.includes('温度')) {
      suggestions.push('检查空调系统运行状态')
    }
    if (metric?.includes('湿度')) {
      suggestions.push('检查除湿设备或通风系统')
    }
    if (metric?.includes('功率')) {
      suggestions.push('检查设备负载情况')
    }
    if (metric?.includes('PM')) {
      suggestions.push('检查空气净化设备')
    }
    
    suggestions.push('联系相关技术人员进行现场检查')
    return suggestions
  }

  /**
   * 处理通知操作
   */
  private handleNotificationAction(id: string, action: 'read' | 'later') {
    // 移除当前通知
    this.notifications.value = this.notifications.value.filter(n => n.id !== id)
    
    if (action === 'read') {
      // 标记为已读的逻辑
      console.log('标记告警为已读:', id)
    }
    
    // 显示下一个通知
    this.isShowing.value = false
    setTimeout(() => {
      this.showNextNotification()
    }, 500)
  }

  /**
   * 获取告警级别文本
   */
  private getLevelText(level: number) {
    const texts = { 0: '低', 1: '中', 2: '高', 3: '紧急' }
    return texts[level] || '未知'
  }

  /**
   * 获取告警级别颜色
   */
  private getLevelColor(level: number) {
    const colors = { 
      0: '#52c41a',  // 绿色 - 低
      1: '#faad14',  // 橙色 - 中  
      2: '#ff4d4f',  // 红色 - 高
      3: '#722ed1'   // 紫色 - 紧急
    }
    return colors[level] || colors[0]
  }

  /**
   * 格式化时间
   */
  private formatTime(timeStr: string) {
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

  /**
   * 获取所有通知
   */
  getNotifications() {
    return this.notifications.value
  }

  /**
   * 清空所有通知
   */
  clearAll() {
    this.notifications.value = []
    this.isShowing.value = false
    if (this.currentModal.value) {
      this.currentModal.value.destroy()
      this.currentModal.value = null
    }
  }
}

// 创建全局实例
export const alertNotificationManager = new AlertNotificationManager()

// 导出类型和实例
export type { AlertNotification }
export { alertNotificationManager as default }
