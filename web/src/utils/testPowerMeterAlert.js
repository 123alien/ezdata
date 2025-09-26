// 测试电表告警功能
console.log('⚡ 测试电表告警功能...')

if (window.globalAlertManager) {
  console.log('✅ 全局告警管理器已存在')
  
  // 手动检查一次告警（包括电表设备）
  console.log('🔍 手动检查告警（包括电表设备）...')
  window.globalAlertManager.manualCheckAlerts()
  
  // 等待2秒后检查结果
  setTimeout(() => {
    console.log('📊 检查结果:')
    console.log('  - 告警队列长度:', window.globalAlertManager.alerts.value.length)
    console.log('  - 队列中的告警:')
    window.globalAlertManager.alerts.value.forEach((alert, index) => {
      console.log(`    ${index + 1}. ${alert.title} - ${alert.source} (${alert.deviceType})`)
    })
  }, 2000)
  
} else {
  console.error('❌ 全局告警管理器未初始化')
}

console.log('📍 当前页面:', window.location.pathname)
