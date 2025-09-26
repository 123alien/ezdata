// 路由守卫 - 确保全局告警监控在所有页面都保持活跃
import { Router } from 'vue-router'

export function setupAlertRouteGuard(router: Router) {
  router.afterEach((to, from) => {
    console.log(`🔄 路由切换: ${from.path} -> ${to.path}`)
    
    // 延迟执行，确保页面完全加载
    setTimeout(() => {
      // 检查全局告警管理器是否存在
      if ((window as any).globalAlertManager) {
        const manager = (window as any).globalAlertManager
        console.log('📊 告警管理器状态检查:')
        console.log('  - 监控状态:', manager.isMonitoring?.value)
        console.log('  - 告警队列长度:', manager.alerts?.value?.length)
        console.log('  - 是否正在显示:', manager.isShowing?.value)
        
        // 确保监控状态
        if (!manager.isMonitoring?.value) {
          console.log('🔄 路由切换后重新启动告警监控...')
          manager.startMonitoring()
        }
        
        // 检查是否有待处理的告警
        if (manager.alerts?.value?.length > 0) {
          console.log(`📋 发现 ${manager.alerts.value.length} 个待处理告警`)
          if (!manager.isShowing?.value) {
            console.log('🔄 显示待处理告警...')
            manager.showNextAlert()
          } else {
            console.log('⏳ 当前已有弹窗显示，等待处理完成')
          }
        } else {
          console.log('✅ 当前无待处理告警')
        }
        
        // 强制显示告警（防止路由切换后丢失）
        manager.forceShowAlerts()
      } else {
        console.warn('⚠️ 全局告警管理器不存在，尝试重新初始化...')
        // 重新初始化全局告警管理器
        import('/@/utils/globalAlertManager').then(({ globalAlertManager }) => {
          (window as any).globalAlertManager = globalAlertManager
          console.log('✅ 全局告警管理器重新初始化成功')
        })
      }
    }, 1000) // 延迟1秒执行
  })
}
