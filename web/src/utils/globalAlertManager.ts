import { ref, reactive } from 'vue'
import { Modal } from 'ant-design-vue'
import dayjs from 'dayjs'

export interface GlobalAlert {
  id: string
  title: string
  content: string
  level: number // 0: 低, 1: 中, 2: 高, 3: 紧急
  source: string
  metric: string
  currentValue: number
  threshold: number
  unit: string
  createTime: string
  deviceType: 'power' | 'environment'
}

class GlobalAlertManager {
  private alerts = ref<GlobalAlert[]>([])
  private isShowing = ref(false)
  private currentModal = ref<any>(null)
  private checkInterval: NodeJS.Timeout | null = null
  private isMonitoring = ref(false)
  private pendingAlerts: { [key: string]: { alert: GlobalAlert; timestamp: number } } = reactive({}) // 存储"稍后处理"的告警
  private processedAlerts: { [key: string]: number } = reactive({}) // 存储已处理告警的时间戳，用于去重

  constructor() {
    console.log('🚨 全局告警管理器初始化...')
    this.startMonitoring()
    
    // 确保在路由切换时保持监控状态
    this.ensureMonitoring()
  }

  /**
   * 开始实时监控
   */
  startMonitoring() {
    if (this.isMonitoring.value) return
    
    this.isMonitoring.value = true
    console.log('🚨 开始全局告警监控...')
    
    // 每10秒检查一次设备数据（测试用，生产环境可以改为30秒）
    this.checkInterval = setInterval(async () => {
      await this.checkDeviceAlerts()
    }, 10000)
  }

  /**
   * 停止监控
   */
  stopMonitoring() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval)
      this.checkInterval = null
    }
    this.isMonitoring.value = false
    console.log('⏹️ 停止全局告警监控')
  }

  /**
   * 确保监控状态（防止路由切换时丢失）
   */
  ensureMonitoring() {
    // 每5秒检查一次监控状态
    setInterval(() => {
      if (!this.isMonitoring.value) {
        console.log('🔄 检测到监控状态丢失，重新启动...')
        this.startMonitoring()
      }
    }, 5000)
  }

  /**
   * 强制显示告警（用于路由切换后）
   */
  forceShowAlerts() {
    console.log('🔄 强制显示告警检查...')
    console.log('当前告警队列长度:', this.alerts.value.length)
    console.log('isShowing 状态:', this.isShowing.value) // 新增日志
    
    if (this.alerts.value.length > 0 && !this.isShowing.value) {
      console.log('🚨 发现待处理告警，强制显示...')
      this.showNextAlert()
    }
  }

  /**
   * 强制重置弹窗状态（用于调试和修复）
   */
  forceResetModalState() {
    console.log('🔄 强制重置弹窗状态...')
    console.log('重置前 isShowing:', this.isShowing.value)
    console.log('重置前 currentModal:', this.currentModal.value)
    
    this.isShowing.value = false
    this.currentModal.value = null
    
    console.log('重置后 isShowing:', this.isShowing.value)
    console.log('重置后 currentModal:', this.currentModal.value)
    
    // 如果有待处理的告警，立即显示
    if (this.alerts.value.length > 0) {
      console.log('🚨 重置后立即显示待处理告警...')
      this.showNextAlert()
    }
  }

  /**
   * 清理积压的告警队列
   */
  clearBacklogAlerts() {
    console.log('🧹 清理积压的告警队列...')
    console.log('清理前队列长度:', this.alerts.value.length)
    
    // 只保留最新的3个告警
    if (this.alerts.value.length > 3) {
      this.alerts.value = this.alerts.value.slice(-3)
      console.log('清理后队列长度:', this.alerts.value.length)
    }
    
    // 强制重置弹窗状态
    this.forceResetModalState()
  }

  /**
   * 检查设备告警
   */
  private async checkDeviceAlerts() {
    try {
      console.log('🔍 开始检查设备告警...')

      // 检查物联网设备告警（环境监测设备）
      await this.checkIotDeviceAlerts()
      
      // 检查电表设备告警
      await this.checkPowerMeterAlerts()

      console.log('✅ 设备告警检查完成')
    } catch (error) {
      console.error('❌ 检查设备告警失败:', error)
    }
  }

  /**
   * 检查物联网设备告警
   */
  private async checkIotDeviceAlerts() {
    try {
      console.log('🌐 检查物联网设备告警...')
      const response = await fetch('/api/datamodel/dashboard/iot-devices')
      const data = await response.json()

      console.log('物联网设备数据响应:', data)

      if (data.code === 200 && data.data) {
        console.log(`找到 ${data.data.length} 个物联网设备:`, data.data)
        for (const device of data.data) {
          await this.checkDeviceThresholds(device)
        }
      } else {
        console.log('未找到物联网设备数据')
      }
    } catch (error) {
      console.error('检查物联网设备告警失败:', error)
    }
  }

  /**
   * 检查电表设备告警
   */
  private async checkPowerMeterAlerts() {
    try {
      console.log('⚡ 检查电表设备告警...')
      const response = await fetch('/api/datamodel/dashboard/power-meter-stats')
      const data = await response.json()

      console.log('电表设备数据响应:', data)

      if (data.code === 200 && data.data && data.data.recent_devices) {
        console.log(`找到 ${data.data.recent_devices.length} 个电表设备:`, data.data.recent_devices)
        for (const device of data.data.recent_devices) {
          await this.checkPowerMeterThresholds(device)
        }
      } else {
        console.log('未找到电表设备数据')
      }
    } catch (error) {
      console.error('检查电表设备告警失败:', error)
    }
  }

  /**
   * 检查环境监测设备告警
   */
  private async checkEnvironmentAlerts() {
    try {
      console.log('🌡️ 检查环境监测设备告警...')
      const response = await fetch('/api/datamodel/dashboard/device-metrics?device_type=environment')
      const data = await response.json()
      
      console.log('环境监测设备数据响应:', data)
      
      if (data.success && data.result?.devices) {
        console.log(`找到 ${data.result.devices.length} 个环境监测设备:`, data.result.devices)
        for (const device of data.result.devices) {
          await this.checkEnvironmentDeviceThresholds(device)
        }
      } else {
        console.log('未找到环境监测设备数据')
      }
    } catch (error) {
      console.error('检查环境监测告警失败:', error)
    }
  }

  /**
   * 检查电表设备阈值
   */
  private async checkPowerMeterThresholds(device: any) {
    console.log(`⚡ 检查电表设备 ${device.device_name} 的阈值...`)
    
    const strategies = await this.getAlertStrategies('power')
    console.log(`电表设备数据:`, device)
    console.log(`电表告警策略:`, strategies)

    for (const strategy of strategies) {
      // 处理trigger_conf，可能是字符串或对象
      let triggerConf = {}
      try {
        if (typeof strategy.trigger_conf === 'string') {
          triggerConf = JSON.parse(strategy.trigger_conf)
        } else if (typeof strategy.trigger_conf === 'object') {
          triggerConf = strategy.trigger_conf
        }
      } catch (e) {
        console.warn(`解析电表策略 ${strategy.name} 的触发配置失败:`, e)
        triggerConf = {}
      }
      console.log(`策略 ${strategy.name} 的触发配置:`, triggerConf)

      // 检查日用电量阈值
      if (triggerConf.daily_threshold && device.today_power !== undefined) {
        const currentDaily = device.today_power
        if (currentDaily > triggerConf.daily_threshold) {
          console.log(`🚨 日用电量超限! 当前: ${currentDaily}kWh, 阈值: ${triggerConf.daily_threshold}kWh`)
          this.addAlert({
            id: `daily-power-${device.device_id}-${Date.now()}`,
            title: '电表日用电量超限告警',
            content: `${device.device_name} 今日用电量 ${currentDaily}kWh 超过设定阈值 ${triggerConf.daily_threshold}kWh`,
            level: strategy.level,
            source: device.device_name,
            metric: '日用电量',
            currentValue: currentDaily,
            threshold: triggerConf.daily_threshold,
            unit: 'kWh',
            createTime: new Date().toISOString(),
            deviceType: 'power'
          })
        }
      }

      // 检查功率阈值（如果有实时功率数据）
      if (triggerConf.power_threshold && device.current_power !== undefined) {
        const currentPower = device.current_power
        if (currentPower > triggerConf.power_threshold) {
          console.log(`🚨 功率超限! 当前: ${currentPower}W, 阈值: ${triggerConf.power_threshold}W`)
          this.addAlert({
            id: `power-${device.device_id}-${Date.now()}`,
            title: '电表功率超限告警',
            content: `${device.device_name} 当前功率 ${currentPower}W 超过设定阈值 ${triggerConf.power_threshold}W`,
            level: strategy.level,
            source: device.device_name,
            metric: '功率',
            currentValue: currentPower,
            threshold: triggerConf.power_threshold,
            unit: 'W',
            createTime: new Date().toISOString(),
            deviceType: 'power'
          })
        }
      }
    }
  }

  /**
   * 检查设备阈值（统一方法）
   */
  private async checkDeviceThresholds(device: any) {
    console.log(`🔍 检查设备 ${device.device_name} 的阈值...`)
    
    // 根据设备类型获取对应的告警策略
    let strategyType = 'environment'
    if (device.device_name?.includes('电表') || device.device_name?.includes('功率')) {
      strategyType = 'power'
    }
    
    const strategies = await this.getAlertStrategies(strategyType)
    console.log(`设备数据:`, device)
    console.log(`告警策略:`, strategies)

    for (const strategy of strategies) {
      // 处理trigger_conf，可能是字符串或对象
      let triggerConf = {}
      try {
        if (typeof strategy.trigger_conf === 'string') {
          triggerConf = JSON.parse(strategy.trigger_conf)
        } else if (typeof strategy.trigger_conf === 'object') {
          triggerConf = strategy.trigger_conf
        }
      } catch (e) {
        console.warn(`解析策略 ${strategy.name} 的触发配置失败:`, e)
        triggerConf = {}
      }
      console.log(`策略 ${strategy.name} 的触发配置:`, triggerConf)

      // 检查设备原始数据
      if (device.raw_data) {
        await this.checkDeviceRawData(device, triggerConf, strategy)
      }
    }
  }

  /**
   * 检查设备原始数据
   */
  private async checkDeviceRawData(device: any, triggerConf: any, strategy: any) {
    const rawData = device.raw_data
    
    // 检查温度
    if (triggerConf.temperature_range && rawData.TEMPERATURE !== undefined) {
      const { min, max } = triggerConf.temperature_range
      const currentTemp = rawData.TEMPERATURE
      if (currentTemp < min || currentTemp > max) {
        console.log(`🚨 温度超限! 当前: ${currentTemp}°C, 范围: ${min}-${max}°C`)
        this.addAlert({
          id: `temp-${device.device_id}-${Date.now()}`,
          title: '环境温度异常告警',
          content: `${device.device_name} 当前温度 ${currentTemp}°C 超出安全范围 ${min}-${max}°C`,
          level: strategy.level,
          source: device.device_name,
          metric: '温度',
          currentValue: currentTemp,
          threshold: { min, max },
          unit: '°C',
          createTime: new Date().toISOString(),
          deviceType: 'environment'
        })
      }
    }

    // 检查湿度
    if (triggerConf.humidity_range && rawData.HUMIDITY !== undefined) {
      const { min, max } = triggerConf.humidity_range
      const currentHumidity = rawData.HUMIDITY
      if (currentHumidity < min || currentHumidity > max) {
        console.log(`🚨 湿度超限! 当前: ${currentHumidity}%, 范围: ${min}-${max}%`)
        this.addAlert({
          id: `humidity-${device.device_id}-${Date.now()}`,
          title: '环境湿度异常告警',
          content: `${device.device_name} 当前湿度 ${currentHumidity}% 超出安全范围 ${min}-${max}%`,
          level: strategy.level,
          source: device.device_name,
          metric: '湿度',
          currentValue: currentHumidity,
          threshold: { min, max },
          unit: '%',
          createTime: new Date().toISOString(),
          deviceType: 'environment'
        })
      }
    }

    // 检查PM2.5
    if (triggerConf.pm25_threshold && rawData.PM25 !== undefined) {
      const currentPM25 = rawData.PM25
      if (currentPM25 > triggerConf.pm25_threshold) {
        console.log(`🚨 PM2.5超限! 当前: ${currentPM25}μg/m³, 阈值: ${triggerConf.pm25_threshold}μg/m³`)
        this.addAlert({
          id: `pm25-${device.device_id}-${Date.now()}`,
          title: 'PM2.5浓度超限告警',
          content: `${device.device_name} 当前PM2.5浓度 ${currentPM25}μg/m³ 超过设定阈值 ${triggerConf.pm25_threshold}μg/m³`,
          level: strategy.level,
          source: device.device_name,
          metric: 'PM2.5',
          currentValue: currentPM25,
          threshold: triggerConf.pm25_threshold,
          unit: 'μg/m³',
          createTime: new Date().toISOString(),
          deviceType: 'environment'
        })
      }
    }

    // 检查PM10
    if (triggerConf.pm10_threshold && rawData.PM10 !== undefined) {
      const currentPM10 = rawData.PM10
      if (currentPM10 > triggerConf.pm10_threshold) {
        console.log(`🚨 PM10超限! 当前: ${currentPM10}μg/m³, 阈值: ${triggerConf.pm10_threshold}μg/m³`)
        this.addAlert({
          id: `pm10-${device.device_id}-${Date.now()}`,
          title: 'PM10浓度超限告警',
          content: `${device.device_name} 当前PM10浓度 ${currentPM10}μg/m³ 超过设定阈值 ${triggerConf.pm10_threshold}μg/m³`,
          level: strategy.level,
          source: device.device_name,
          metric: 'PM10',
          currentValue: currentPM10,
          threshold: triggerConf.pm10_threshold,
          unit: 'μg/m³',
          createTime: new Date().toISOString(),
          deviceType: 'environment'
        })
      }
    }

    // 检查CO2
    if (triggerConf.co2_threshold && rawData.CO2 !== undefined) {
      const currentCO2 = rawData.CO2
      if (currentCO2 > triggerConf.co2_threshold) {
        console.log(`🚨 CO2超限! 当前: ${currentCO2}ppm, 阈值: ${triggerConf.co2_threshold}ppm`)
        this.addAlert({
          id: `co2-${device.device_id}-${Date.now()}`,
          title: 'CO2浓度超限告警',
          content: `${device.device_name} 当前CO2浓度 ${currentCO2}ppm 超过设定阈值 ${triggerConf.co2_threshold}ppm`,
          level: strategy.level,
          source: device.device_name,
          metric: 'CO2',
          currentValue: currentCO2,
          threshold: triggerConf.co2_threshold,
          unit: 'ppm',
          createTime: new Date().toISOString(),
          deviceType: 'environment'
        })
      }
    }
  }

  /**
   * 检查电表设备阈值（保留用于兼容）
   */
  private async checkPowerDeviceThresholds(device: any) {
    console.log(`🔍 检查电表设备 ${device.device_name} 的阈值...`)
    const strategies = await this.getAlertStrategies('power')
    
    console.log(`设备数据:`, device)
    console.log(`告警策略:`, strategies)
    
    for (const strategy of strategies) {
      const triggerConf = JSON.parse(strategy.trigger_conf || '{}')
      console.log(`策略 ${strategy.name} 的触发配置:`, triggerConf)
      
      // 检查功率阈值
      if (triggerConf.power_threshold && device.power > triggerConf.power_threshold) {
        console.log(`🚨 功率超限! 当前: ${device.power}W, 阈值: ${triggerConf.power_threshold}W`)
        this.addAlert({
          id: `power-${device.device_id}-${Date.now()}`,
          title: '电表功率超限告警',
          content: `${device.device_name} 当前功率 ${device.power}W 超过设定阈值 ${triggerConf.power_threshold}W`,
          level: strategy.level,
          source: device.device_name,
          metric: '功率',
          currentValue: device.power,
          threshold: triggerConf.power_threshold,
          unit: 'W',
          createTime: new Date().toISOString(),
          deviceType: 'power'
        })
      } else {
        console.log(`✅ 功率正常: ${device.power}W <= ${triggerConf.power_threshold}W`)
      }
      
      // 检查日用电量阈值
      if (triggerConf.daily_threshold && device.daily_power > triggerConf.daily_threshold) {
        console.log(`🚨 日用电量超限! 当前: ${device.daily_power}kWh, 阈值: ${triggerConf.daily_threshold}kWh`)
        this.addAlert({
          id: `daily-${device.device_id}-${Date.now()}`,
          title: '日用电量超限告警',
          content: `${device.device_name} 今日用电量 ${device.daily_power}kWh 超过设定阈值 ${triggerConf.daily_threshold}kWh`,
          level: strategy.level,
          source: device.device_name,
          metric: '日用电量',
          currentValue: device.daily_power,
          threshold: triggerConf.daily_threshold,
          unit: 'kWh',
          createTime: new Date().toISOString(),
          deviceType: 'power'
        })
      } else {
        console.log(`✅ 日用电量正常: ${device.daily_power}kWh <= ${triggerConf.daily_threshold}kWh`)
      }
    }
  }

  /**
   * 检查环境监测设备阈值
   */
  private async checkEnvironmentDeviceThresholds(device: any) {
    const strategies = await this.getAlertStrategies('environment')
    
    for (const strategy of strategies) {
      const triggerConf = JSON.parse(strategy.trigger_conf || '{}')
      
      // 检查各项环境指标
      const metrics = [
        { key: 'temperature', name: '温度', unit: '°C' },
        { key: 'humidity', name: '湿度', unit: '%' },
        { key: 'pm25', name: 'PM2.5', unit: 'μg/m³' },
        { key: 'pm10', name: 'PM10', unit: 'μg/m³' },
        { key: 'co2', name: 'CO2', unit: 'ppm' }
      ]
      
      for (const metric of metrics) {
        const value = device[metric.key]
        if (value !== undefined && value !== null) {
          // 检查范围阈值
          const rangeKey = `${metric.key}_range`
          if (triggerConf[rangeKey]) {
            const range = triggerConf[rangeKey]
            if (value < range.min || value > range.max) {
              this.addAlert({
                id: `${metric.key}-${device.device_id}-${Date.now()}`,
                title: `${metric.name}超限告警`,
                content: `${device.device_name} 当前${metric.name} ${value}${metric.unit} 超出安全范围 [${range.min}-${range.max}]${metric.unit}`,
                level: strategy.level,
                source: device.device_name,
                metric: metric.name,
                currentValue: value,
                threshold: value < range.min ? range.min : range.max,
                unit: metric.unit,
                createTime: new Date().toISOString(),
                deviceType: 'environment'
              })
            }
          }
          
          // 检查单一阈值
          const thresholdKey = `${metric.key}_threshold`
          if (triggerConf[thresholdKey] && value > triggerConf[thresholdKey]) {
            this.addAlert({
              id: `${metric.key}-${device.device_id}-${Date.now()}`,
              title: `${metric.name}超限告警`,
              content: `${device.device_name} 当前${metric.name} ${value}${metric.unit} 超过设定阈值 ${triggerConf[thresholdKey]}${metric.unit}`,
              level: strategy.level,
              source: device.device_name,
              metric: metric.name,
              currentValue: value,
              threshold: triggerConf[thresholdKey],
              unit: metric.unit,
              createTime: new Date().toISOString(),
              deviceType: 'environment'
            })
          }
        }
      }
    }
  }

  /**
   * 获取告警策略
   */
  private async getAlertStrategies(deviceType: string) {
    try {
      // 使用动态导入来避免循环依赖
      const { defHttp } = await import('/@/utils/http/axios')
      
      const response = await defHttp.get({ 
        url: '/alert_strategy/list',
        params: {
          pageNo: 1,
          pageSize: 100,
          status: 1  // 只获取启用状态的策略
        }
      })
      
      console.log('获取告警策略响应:', response)
      
      if (response.records) {
        console.log('所有告警策略:', response.records)
        const strategies = response.records.filter((strategy: any) => {
          // 首先检查策略状态，只处理启用状态的策略
          if (strategy.status !== 1) {
            console.log(`⚠️ 跳过禁用策略: ${strategy.name} (状态: ${strategy.status})`)
            return false
          }
          
          const isEnvironmentStrategy = strategy.name.includes('环境') || strategy.name.includes('监测')
          const isPowerStrategy = strategy.name.includes('电表') || strategy.name.includes('功率')
          
          if (deviceType === 'power') {
            return isPowerStrategy
          } else {
            return isEnvironmentStrategy
          }
        })
        console.log(`找到 ${strategies.length} 个${deviceType}告警策略:`, strategies)
        return strategies
      }
      return []
    } catch (error) {
      console.error('获取告警策略失败:', error)
      return []
    }
  }

  /**
   * 添加告警
   */
  addAlert(alert: GlobalAlert) {
    // 智能去重：相同设备相同指标5分钟内只保留一个
    const existingAlert = this.alerts.value.find(a => 
      a.source === alert.source && 
      a.metric === alert.metric && 
      dayjs(alert.createTime).diff(dayjs(a.createTime), 'minute') < 5
    )
    
    if (existingAlert) {
      console.log('⚠️ 告警去重: 相同设备相同指标5分钟内已存在', alert.title)
      return
    }
    
    // 检查是否在5分钟内已处理过相同告警
    const alertKey = `${alert.source}-${alert.metric}`
    const lastProcessedTime = this.processedAlerts[alertKey]
    if (lastProcessedTime && (Date.now() - lastProcessedTime) < 5 * 60 * 1000) {
      console.log('⚠️ 告警去重: 相同设备相同指标5分钟内已处理过', alert.title)
      return
    }
    
    // 限制队列长度，避免积压过多
    if (this.alerts.value.length >= 10) {
      console.log('⚠️ 告警队列已满(10个)，丢弃新告警:', alert.title)
      return
    }
    
    this.alerts.value.push(alert)
    console.log('🚨 新增告警:', alert.title, '当前队列长度:', this.alerts.value.length)
    console.log('addAlert - isShowing 状态:', this.isShowing.value)
    
    if (!this.isShowing.value) {
      console.log('📋 准备显示告警弹窗...')
      this.showNextAlert()
    } else {
      console.log('⏳ 当前已有弹窗显示，告警已加入队列')
    }
  }

  /**
   * 显示下一个告警
   */
  private showNextAlert() {
    console.log('showNextAlert - isShowing 状态:', this.isShowing.value) // 新增日志
    if (this.alerts.value.length === 0) {
      this.isShowing.value = false // 队列为空时确保重置
      console.log('✅ 告警队列为空，isShowing 重置为 false') // 新增日志
      return
    }

    if (this.isShowing.value) {
      console.log('⏳ 弹窗已在显示中，等待当前弹窗关闭') // 新增日志
      return
    }

    const alert = this.alerts.value[0]
    this.showAlertModal(alert)
  }

  /**
   * 显示告警弹窗
   */
  private showAlertModal(alert: GlobalAlert) {
    console.log('🚨 准备显示告警弹窗:', alert.title)
    this.isShowing.value = true // 在创建弹窗前设置为 true
    console.log('showAlertModal - isShowing 设置为 true') // 新增日志
    
    const levelColors = {
      0: '#52c41a', // 绿色 - 低
      1: '#faad14', // 橙色 - 中  
      2: '#ff4d4f', // 红色 - 高
      3: '#722ed1'  // 紫色 - 紧急
    }
    
    const levelTexts = {
      0: '低',
      1: '中',
      2: '高',
      3: '紧急'
    }
    
    const levelColor = levelColors[alert.level as keyof typeof levelColors] || levelColors[1]
    const levelText = levelTexts[alert.level as keyof typeof levelTexts] || '中'
    
    // 创建告警内容
    const content = `🚨 ${alert.content}\n\n` +
      `📊 当前值: ${alert.currentValue}${alert.unit}\n` +
      `⚠️ 阈值: ${alert.threshold}${alert.unit}\n` +
      `🕐 时间: ${dayjs(alert.createTime).format('YYYY-MM-DD HH:mm:ss')}\n\n` +
      `💡 建议: 请立即检查设备状态，必要时联系运维人员`
    
    this.currentModal.value = Modal.confirm({
      title: `🔔 ${levelText}级告警 - ${alert.title}`,
      content: content,
      width: 600,
      maskClosable: false,
      closable: true,
      okText: '已处理',
      cancelText: '稍后处理',
      onOk: () => this.handleAlertAction(alert.id, 'resolved'),
      onCancel: () => this.handleAlertAction(alert.id, 'pending'),
      afterClose: () => { // 新增 afterClose 钩子
        console.log(`Modal ${alert.id} 完全关闭，isShowing 重置为 false`)
        this.isShowing.value = false
        this.currentModal.value = null
        // 注意：不在这里自动显示下一个告警，让 handleAlertAction 方法处理
        console.log('✅ 弹窗已完全关闭，等待 handleAlertAction 处理下一个告警')
      },
      style: {
        '--alert-color': levelColor
      },
      className: 'global-alert-modal'
    })
    
    console.log('✅ 告警弹窗已创建:', this.currentModal.value)
  }

  /**
   * 处理告警操作
   */
  private handleAlertAction(alertId: string, action: 'resolved' | 'pending') {
    console.log(`处理告警 ${alertId}，操作: ${action}`) // 新增日志
    
    if (action === 'resolved') {
      // 已处理：直接从队列中移除
      const alert = this.alerts.value.find(a => a.id === alertId)
      if (alert) {
        // 记录已处理告警的时间戳，用于去重
        const alertKey = `${alert.source}-${alert.metric}`
        this.processedAlerts[alertKey] = Date.now()
        console.log(`告警 ${alertId} 已处理，记录处理时间用于去重`)
      }
      
      this.alerts.value = this.alerts.value.filter(a => a.id !== alertId)
      console.log(`告警 ${alertId} 已处理，从队列中移除`)
      
      // 强制重置弹窗状态
      console.log('🔄 已处理后强制重置弹窗状态...')
      this.isShowing.value = false
      this.currentModal.value = null
      
      // 显示下一个告警（如果有的话）
      setTimeout(() => {
        console.log('🔄 检查是否有下一个告警需要显示...')
        if (this.alerts.value.length > 0) {
          console.log(`📋 发现 ${this.alerts.value.length} 个待处理告警，准备显示下一个`)
          this.showNextAlert()
        } else {
          console.log('✅ 当前无待处理告警')
        }
      }, 500) // 延迟500ms确保弹窗完全关闭
      
    } else if (action === 'pending') {
      // 稍后处理：保存到待处理列表，1分钟后重新检查
      const alert = this.alerts.value.find(a => a.id === alertId)
      if (alert) {
        this.pendingAlerts[alertId] = {
          alert: alert,
          timestamp: Date.now()
        }
        console.log(`告警 ${alertId} 稍后处理，已保存到待处理列表，10分钟后重新检查`)
        
        // 设置10分钟后重新检查的定时器
        setTimeout(() => {
          this.recheckPendingAlert(alertId)
        }, 600000) // 10分钟 = 600000毫秒
      }
      
      // 从当前队列中移除，但保留在待处理列表中
      this.alerts.value = this.alerts.value.filter(a => a.id !== alertId)
      
      // 强制重置弹窗状态
      console.log('🔄 稍后处理后强制重置弹窗状态...')
      this.isShowing.value = false
      this.currentModal.value = null
      
      // 稍后处理：不立即显示下一个告警，等待10分钟后重新检查
      console.log('⏳ 稍后处理完成，等待10分钟后重新检查阈值')
    }
    
    console.log(`告警 ${alertId} ${action === 'resolved' ? '已处理' : '稍后处理'}`)
  }

  /**
   * 重新检查待处理的告警
   */
  private async recheckPendingAlert(alertId: string) {
    console.log(`🔄 重新检查待处理告警: ${alertId}`)
    
    const pendingAlert = this.pendingAlerts[alertId]
    if (!pendingAlert) {
      console.log(`⚠️ 待处理告警 ${alertId} 不存在，可能已被处理`)
      return
    }
    
    try {
      // 重新获取设备数据，检查阈值是否仍然超限
      const response = await fetch('/api/datamodel/dashboard/iot-devices')
      const data = await response.json()
      
      if (data.code === 200 && data.data) {
        // 找到对应的设备
        const device = data.data.find((d: any) => d.device_name === pendingAlert.alert.source)
        if (device && device.raw_data) {
          const rawData = device.raw_data
          const metric = pendingAlert.alert.metric
          
          // 检查对应的指标是否仍然超限
          let isStillExceeded = false
          let currentValue = 0
          
          if (metric === 'PM2.5' && rawData.PM25 !== undefined) {
            currentValue = rawData.PM25
            // 这里需要获取阈值配置，暂时使用硬编码的阈值3
            isStillExceeded = currentValue > 3
          } else if (metric === 'PM10' && rawData.PM10 !== undefined) {
            currentValue = rawData.PM10
            isStillExceeded = currentValue > 3
          } else if (metric === 'CO2' && rawData.CO2 !== undefined) {
            currentValue = rawData.CO2
            isStillExceeded = currentValue > 50
          }
          
          if (isStillExceeded) {
            console.log(`🚨 告警 ${alertId} 仍然超限！当前值: ${currentValue}，重新添加到队列`)
            
            // 更新告警的当前值和时间
            const updatedAlert = {
              ...pendingAlert.alert,
              currentValue: currentValue,
              createTime: new Date().toISOString(),
              id: `${pendingAlert.alert.id}-recheck-${Date.now()}` // 生成新的ID避免重复
            }
            
            // 重新添加到告警队列
            this.alerts.value.push(updatedAlert)
            
            // 如果当前没有弹窗显示，立即显示
            if (!this.isShowing.value) {
              this.showNextAlert()
            }
          } else {
            console.log(`✅ 告警 ${alertId} 已恢复正常，当前值: ${currentValue}`)
          }
        }
      }
      
      // 从待处理列表中移除
      delete this.pendingAlerts[alertId]
      
    } catch (error) {
      console.error(`❌ 重新检查告警 ${alertId} 失败:`, error)
    }
  }

  /**
   * 获取当前告警列表
   */
  getAlerts() {
    return this.alerts.value
  }

  /**
   * 清空所有告警
   */
  clearAlerts() {
    this.alerts.value = []
    if (this.currentModal.value) {
      this.currentModal.value.destroy()
      this.currentModal.value = null
    }
    this.isShowing.value = false
  }

  /**
   * 手动触发测试告警
   */
  triggerTestAlert() {
    console.log('🚨 手动触发测试告警...')
    this.addAlert({
      id: 'test-' + Date.now(),
      title: '测试告警',
      content: '这是一个测试告警，用于验证全局告警系统是否正常工作',
      level: 2,
      source: '测试设备',
      metric: '测试指标',
      currentValue: 100,
      threshold: 80,
      unit: '单位',
      createTime: new Date().toISOString(),
      deviceType: 'power'
    })
  }

  /**
   * 手动检查一次告警（用于调试）
   */
  async manualCheckAlerts() {
    console.log('🔍 手动检查告警...')
    await this.checkDeviceAlerts()
  }
}

// 创建全局实例
export const globalAlertManager = new GlobalAlertManager()

// 导出类型
export type { GlobalAlert }
