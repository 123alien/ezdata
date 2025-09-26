// 测试告警序列显示
console.log('🧪 测试告警序列显示功能...')

if (window.globalAlertManager) {
  console.log('✅ 全局告警管理器已存在')
  
  // 检查当前状态
  console.log('📊 当前状态:')
  console.log('  - isShowing:', window.globalAlertManager.isShowing.value)
  console.log('  - currentModal:', window.globalAlertManager.currentModal.value)
  console.log('  - 告警队列长度:', window.globalAlertManager.alerts.value.length)
  
  // 查看队列中的告警
  if (window.globalAlertManager.alerts.value.length > 0) {
    console.log('📋 队列中的告警:')
    window.globalAlertManager.alerts.value.forEach((alert, index) => {
      console.log(`  ${index + 1}. ${alert.title} - ${alert.source}`)
    })
  } else {
    console.log('📋 队列为空')
  }
  
  // 如果队列为空，强制重置状态
  if (window.globalAlertManager.alerts.value.length === 0) {
    console.log('🔄 队列为空，强制重置状态...')
    window.globalAlertManager.forceResetModalState()
  }
  
  // 手动检查一次告警
  console.log('🔍 手动检查告警...')
  window.globalAlertManager.manualCheckAlerts()
  
} else {
  console.error('❌ 全局告警管理器未初始化')
}

console.log('📍 当前页面:', window.location.pathname)
