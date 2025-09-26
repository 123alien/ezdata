// 测试全局告警管理器
console.log('🧪 测试全局告警管理器...')

// 检查全局告警管理器是否存在
if (window.globalAlertManager) {
  console.log('✅ 全局告警管理器已存在')
  console.log('监控状态:', window.globalAlertManager.isMonitoring)
  
  // 测试触发一个告警
  console.log('🚨 测试触发告警...')
  window.globalAlertManager.triggerTestAlert()
} else {
  console.log('❌ 全局告警管理器不存在')
}

// 检查当前页面
console.log('📍 当前页面:', window.location.pathname)
