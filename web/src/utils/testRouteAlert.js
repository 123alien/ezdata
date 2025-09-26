// 测试路由切换后的告警弹窗
console.log('🧪 测试路由切换后的告警弹窗...')

// 检查全局告警管理器状态
if (window.globalAlertManager) {
  console.log('✅ 全局告警管理器存在')
  console.log('监控状态:', window.globalAlertManager.isMonitoring?.value)
  console.log('告警队列长度:', window.globalAlertManager.alerts?.value?.length)
  console.log('是否正在显示:', window.globalAlertManager.isShowing?.value)
  
  // 手动触发测试告警
  console.log('🚨 手动触发测试告警...')
  window.globalAlertManager.triggerTestAlert()
  
  // 等待2秒后检查状态
  setTimeout(() => {
    console.log('📊 2秒后状态检查:')
    console.log('告警队列长度:', window.globalAlertManager.alerts?.value?.length)
    console.log('是否正在显示:', window.globalAlertManager.isShowing?.value)
    
    if (window.globalAlertManager.alerts?.value?.length > 0) {
      console.log('📋 待处理告警:')
      window.globalAlertManager.alerts.value.forEach((alert, index) => {
        console.log(`  ${index + 1}. ${alert.title} - ${alert.source}`)
      })
      
      // 手动显示下一个告警
      if (!window.globalAlertManager.isShowing?.value) {
        console.log('🔄 手动显示下一个告警...')
        window.globalAlertManager.showNextAlert()
      }
    }
  }, 2000)
  
} else {
  console.error('❌ 全局告警管理器不存在')
}

// 检查当前页面路径
console.log('📍 当前页面:', window.location.pathname)
