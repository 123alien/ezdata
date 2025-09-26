// 清空告警队列脚本
console.log('🧹 清空告警队列...')

if (window.globalAlertManager) {
  console.log('✅ 全局告警管理器已存在')
  
  // 检查当前状态
  console.log('📊 清空前状态:')
  console.log('  - 告警队列长度:', window.globalAlertManager.alerts.value.length)
  console.log('  - 是否正在显示:', window.globalAlertManager.isShowing.value)
  
  // 清空所有告警
  window.globalAlertManager.clearAlerts()
  
  console.log('📊 清空后状态:')
  console.log('  - 告警队列长度:', window.globalAlertManager.alerts.value.length)
  console.log('  - 是否正在显示:', window.globalAlertManager.isShowing.value)
  
  console.log('✅ 告警队列已清空')
} else {
  console.error('❌ 全局告警管理器未初始化')
}

console.log('📍 当前页面:', window.location.pathname)
