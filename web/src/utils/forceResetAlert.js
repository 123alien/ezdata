// 强制重置告警弹窗状态
console.log('🔧 强制重置告警弹窗状态...')

if (window.globalAlertManager) {
  console.log('当前状态检查:')
  console.log('  - isShowing:', window.globalAlertManager.isShowing?.value)
  console.log('  - currentModal:', window.globalAlertManager.currentModal?.value)
  console.log('  - 告警队列长度:', window.globalAlertManager.alerts?.value?.length)
  
  // 强制重置状态
  window.globalAlertManager.isShowing.value = false
  window.globalAlertManager.currentModal.value = null
  
  console.log('重置后状态:')
  console.log('  - isShowing:', window.globalAlertManager.isShowing?.value)
  console.log('  - currentModal:', window.globalAlertManager.currentModal?.value)
  
  // 如果有待处理的告警，立即显示
  if (window.globalAlertManager.alerts?.value?.length > 0) {
    console.log('🚨 发现待处理告警，立即显示...')
    window.globalAlertManager.showNextAlert()
  } else {
    console.log('✅ 当前无待处理告警')
  }
} else {
  console.error('❌ 全局告警管理器不存在')
}
