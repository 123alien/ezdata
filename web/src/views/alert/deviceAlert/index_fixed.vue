<template>
  <div class="device-alert-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h2>设备告警管理</h2>
        <p>管理电表和环境监测设备的阈值告警策略</p>
      </div>
      <div class="header-actions">
        <a-button type="primary" @click="createDefaultStrategies" :loading="creating">
          <Icon icon="ant-design:plus-outlined" />
          创建默认策略
        </a-button>
        <a-button @click="checkAlerts" :loading="checking">
          <Icon icon="ant-design:warning-outlined" />
          手动检查告警
        </a-button>
        <a-dropdown>
          <a-button>
            <Icon icon="ant-design:notification-outlined" />
            测试通知
            <Icon icon="ant-design:down-outlined" />
          </a-button>
          <template #overlay>
            <a-menu @click="handleNotificationTest">
              <a-menu-item key="platform">平台通知</a-menu-item>
              <a-menu-item key="sms">短信预警</a-menu-item>
              <a-menu-item key="email">邮件通知</a-menu-item>
              <a-menu-item key="wechat">微信通知</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 告警策略卡片 -->
    <div class="strategy-cards">
      <div class="strategy-card" v-for="strategy in strategies" :key="strategy.id">
        <div class="card-header">
          <div class="strategy-info">
            <h3>{{ strategy.name }}</h3>
            <a-tag :color="strategy.status === 1 ? 'green' : 'red'">
              {{ strategy.status === 1 ? '启用' : '禁用' }}
            </a-tag>
          </div>
          <div class="strategy-actions">
            <a-button size="small" @click="editStrategy(strategy)">编辑</a-button>
            <a-button size="small" @click="toggleStrategy(strategy)">
              {{ strategy.status === 1 ? '禁用' : '启用' }}
            </a-button>
          </div>
        </div>
        
        <div class="card-content">
          <div class="strategy-description">
            <p>{{ strategy.description || '暂无描述' }}</p>
          </div>
          
          <div class="thresholds" v-if="strategy.trigger_conf">
            <h4>阈值配置：</h4>
            <div class="threshold-list">
              <div v-for="(value, key) in strategy.trigger_conf" :key="key" class="threshold-item">
                <span class="threshold-label">{{ getThresholdLabel(key) }}:</span>
                <span class="threshold-value">{{ formatThresholdValue(value) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 告警历史 -->
    <div class="alert-history">
      <h3>最近告警</h3>
      <BasicTable @register="registerTable" />
    </div>

    <!-- 策略编辑弹窗 -->
    <AlertStrategyModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { BasicTable, useTable } from '/@/components/Table'
import { useModal } from '/@/components/Modal'
import { Icon } from '/@/components/Icon'
import AlertStrategyModal from './components/AlertStrategyModal.vue'
import { columns, searchFormSchema } from './deviceAlert.data'
import { 
        getAlertStrategyList, 
        createDefaultStrategies as createDefaultStrategiesApi, 
        checkDeviceAlerts,
        testNotification,
        getAlertList 
      } from './deviceAlert.api'

const strategies = ref([])
const creating = ref(false)
const checking = ref(false)

// 注册表格
const [registerTable, { reload }] = useTable({
  title: '告警历史',
  api: getAlertList,
  columns,
  canResize: false,
  formConfig: {
    schemas: searchFormSchema,
    autoSubmitOnEnter: true,
    showAdvancedButton: true,
  },
  actionColumn: {
    width: 200,
    fixed: 'right',
  },
})

// 注册弹窗
const [registerModal, { openModal }] = useModal()

// 获取策略列表
const fetchStrategies = async () => {
  try {
    const res = await getAlertStrategyList({ template_code: ['device_power_threshold', 'device_environment_threshold'] })
    strategies.value = res.records || []
  } catch (error) {
    console.error('获取告警策略失败:', error)
  }
}

// 创建默认策略
const createDefaultStrategies = async () => {
  creating.value = true
  try {
    await createDefaultStrategiesApi()
    await fetchStrategies()
    console.log('默认策略创建成功')
  } catch (error) {
    console.error('创建默认策略失败:', error)
  } finally {
    creating.value = false
  }
}

// 手动检查告警
const checkAlerts = async () => {
  checking.value = true
  try {
    await checkDeviceAlerts()
    await reload()
    console.log('告警检查完成')
  } catch (error) {
    console.error('检查告警失败:', error)
  } finally {
    checking.value = false
  }
}

// 编辑策略
const editStrategy = (record) => {
  openModal(true, {
    record,
    isUpdate: true,
  })
}

// 切换策略状态
const toggleStrategy = async (record) => {
  try {
    const newStatus = record.status === 1 ? 0 : 1
    await editAlertStrategy({ id: record.id, status: newStatus })
    await fetchStrategies()
    reload()
  } catch (error) {
    console.error('切换策略状态失败:', error)
  }
}

// 处理成功回调
const handleSuccess = () => {
  fetchStrategies()
  reload()
}

// 测试通知
const handleNotificationTest = async ({ key }) => {
  try {
    await testNotification({ method: key, receiver: 'admin' })
    // 刷新告警历史
    reload()
  } catch (error) {
    console.error('测试通知失败:', error)
  }
}

// 格式化阈值显示
const getThresholdLabel = (key) => {
  const labels = {
    power_threshold: '功率阈值',
    daily_threshold: '日用电量阈值',
    temperature_threshold: '温度阈值',
    humidity_threshold: '湿度阈值',
    pm25_threshold: 'PM2.5阈值',
    pm10_threshold: 'PM10阈值',
    co2_threshold: 'CO2阈值',
    level: '告警等级',
  }
  return labels[key] || key
}

const formatThresholdValue = (value) => {
  if (typeof value === 'object' && value !== null) {
    if ('min' in value && 'max' in value) {
      return `${value.min} - ${value.max}`
    } else if ('max' in value) {
      return `< ${value.max}`
    } else if ('min' in value) {
      return `> ${value.min}`
    }
  }
  return value
}

onMounted(() => {
  fetchStrategies()
})
</script>

<style lang="less" scoped>
.device-alert-page {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 80px);

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    background-color: #fff;
    padding: 20px 24px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

    .header-content {
      h2 {
        font-size: 28px;
        color: #333;
        margin-bottom: 8px;
      }
      p {
        font-size: 14px;
        color: #666;
      }
    }

    .header-actions {
      .ant-btn {
        margin-left: 12px;
        height: 40px;
        font-size: 15px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        .icon {
          margin-right: 6px;
        }
      }
    }
  }

  .strategy-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 24px;
    margin-bottom: 32px;

    .strategy-card {
      background-color: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      overflow: hidden;
      transition: all 0.3s ease;
      border: 1px solid #e8e8e8;

      &:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        transform: translateY(-3px);
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid #f0f0f0;
        background-color: #fafafa;

        .strategy-info {
          display: flex;
          align-items: center;
          h3 {
            font-size: 18px;
            color: #333;
            margin-bottom: 0;
            margin-right: 10px;
          }
        }

        .strategy-actions {
          .ant-btn {
            margin-left: 8px;
          }
        }
      }

      .card-content {
        padding: 20px;

        .strategy-description {
          font-size: 14px;
          color: #555;
          margin-bottom: 16px;
          line-height: 1.6;
        }

        .thresholds {
          h4 {
            font-size: 15px;
            color: #333;
            margin-bottom: 12px;
            border-left: 3px solid #1890ff;
            padding-left: 8px;
          }

          .threshold-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;

            .threshold-item {
              background-color: #f7f7f7;
              padding: 10px 15px;
              border-radius: 6px;
              display: flex;
              justify-content: space-between;
              align-items: center;
              border: 1px solid #eee;

              .threshold-label {
                font-size: 13px;
                color: #666;
                font-weight: 500;
              }
              .threshold-value {
                font-size: 15px;
                color: #333;
                font-weight: 600;
              }
            }
          }
        }
      }
    }
  }

  .alert-history {
    background-color: #fff;
    padding: 24px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

    h3 {
      font-size: 22px;
      color: #333;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid #eee;
    }
  }
}
</style>
