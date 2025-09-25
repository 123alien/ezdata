<template>
  <div class="notification-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h2>通知配置管理</h2>
        <p>配置告警通知方式、接收人员和频次设置</p>
      </div>
    </div>

    <!-- 通知方式配置 -->
    <div class="config-section">
      <h3>通知方式配置</h3>
      <div class="config-cards">
        <div class="config-card">
          <div class="card-header">
            <Icon icon="ant-design:notification-outlined" />
            <h4>平台通知</h4>
            <a-switch v-model:checked="configs.platform.enabled" />
          </div>
          <div class="card-content">
            <p>系统内消息通知，实时显示在用户界面</p>
            <div class="config-item">
              <label>通知标题模板：</label>
              <a-input v-model:value="configs.platform.titleTemplate" placeholder="【{level}级告警】{title}" />
            </div>
          </div>
        </div>

        <div class="config-card">
          <div class="card-header">
            <Icon icon="ant-design:message-outlined" />
            <h4>短信预警</h4>
            <a-switch v-model:checked="configs.sms.enabled" />
          </div>
          <div class="card-content">
            <p>通过短信服务商发送预警信息</p>
            <div class="config-item">
              <label>短信服务商：</label>
              <a-select v-model:value="configs.sms.provider" style="width: 200px">
                <a-select-option value="aliyun">阿里云短信</a-select-option>
                <a-select-option value="tencent">腾讯云短信</a-select-option>
                <a-select-option value="huawei">华为云短信</a-select-option>
              </a-select>
            </div>
            <div class="config-item">
              <label>API密钥：</label>
              <a-input-password v-model:value="configs.sms.apiKey" placeholder="请输入API密钥" />
            </div>
            <div class="config-item">
              <label>短信签名：</label>
              <a-input v-model:value="configs.sms.signature" placeholder="数字金融实验室" />
            </div>
          </div>
        </div>

        <div class="config-card">
          <div class="card-header">
            <Icon icon="ant-design:mail-outlined" />
            <h4>邮件通知</h4>
            <a-switch v-model:checked="configs.email.enabled" />
          </div>
          <div class="card-content">
            <p>通过SMTP服务器发送邮件通知</p>
            <div class="config-item">
              <label>SMTP服务器：</label>
              <a-input v-model:value="configs.email.smtpServer" placeholder="smtp.qq.com" />
            </div>
            <div class="config-item">
              <label>端口：</label>
              <a-input-number v-model:value="configs.email.port" :min="1" :max="65535" style="width: 100px" />
            </div>
            <div class="config-item">
              <label>发送邮箱：</label>
              <a-input v-model:value="configs.email.username" placeholder="your_email@qq.com" />
            </div>
            <div class="config-item">
              <label>邮箱密码：</label>
              <a-input-password v-model:value="configs.email.password" placeholder="请输入邮箱密码" />
            </div>
          </div>
        </div>

        <div class="config-card">
          <div class="card-header">
            <Icon icon="ant-design:wechat-outlined" />
            <h4>微信通知</h4>
            <a-switch v-model:checked="configs.wechat.enabled" />
          </div>
          <div class="card-content">
            <p>通过企业微信机器人发送通知</p>
            <div class="config-item">
              <label>Webhook地址：</label>
              <a-input v-model:value="configs.wechat.webhookUrl" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send" />
            </div>
            <div class="config-item">
              <label>机器人密钥：</label>
              <a-input-password v-model:value="configs.wechat.key" placeholder="请输入机器人密钥" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 接收人员配置 -->
    <div class="config-section">
      <h3>接收人员配置</h3>
      <div class="receivers-config">
        <div class="receiver-group">
          <h4>系统管理员</h4>
          <div class="receiver-info">
            <a-input v-model:value="receivers.admin.name" placeholder="姓名" style="width: 120px" />
            <a-input v-model:value="receivers.admin.phone" placeholder="手机号" style="width: 150px" />
            <a-input v-model:value="receivers.admin.email" placeholder="邮箱" style="width: 200px" />
            <a-input v-model:value="receivers.admin.wechat" placeholder="微信号" style="width: 150px" />
          </div>
        </div>

        <div class="receiver-group">
          <h4>运维人员</h4>
          <div class="receiver-info">
            <a-input v-model:value="receivers.operator.name" placeholder="姓名" style="width: 120px" />
            <a-input v-model:value="receivers.operator.phone" placeholder="手机号" style="width: 150px" />
            <a-input v-model:value="receivers.operator.email" placeholder="邮箱" style="width: 200px" />
            <a-input v-model:value="receivers.operator.wechat" placeholder="微信号" style="width: 150px" />
          </div>
        </div>

        <div class="receiver-group">
          <h4>设备管理员</h4>
          <div class="receiver-info">
            <a-input v-model:value="receivers.device_manager.name" placeholder="姓名" style="width: 120px" />
            <a-input v-model:value="receivers.device_manager.phone" placeholder="手机号" style="width: 150px" />
            <a-input v-model:value="receivers.device_manager.email" placeholder="邮箱" style="width: 200px" />
            <a-input v-model:value="receivers.device_manager.wechat" placeholder="微信号" style="width: 150px" />
          </div>
        </div>

        <div class="receiver-group">
          <h4>安全负责人</h4>
          <div class="receiver-info">
            <a-input v-model:value="receivers.security_manager.name" placeholder="姓名" style="width: 120px" />
            <a-input v-model:value="receivers.security_manager.phone" placeholder="手机号" style="width: 150px" />
            <a-input v-model:value="receivers.security_manager.email" placeholder="邮箱" style="width: 200px" />
            <a-input v-model:value="receivers.security_manager.wechat" placeholder="微信号" style="width: 150px" />
          </div>
        </div>
      </div>
    </div>

    <!-- 频次设置 -->
    <div class="config-section">
      <h3>告警频次设置</h3>
      <div class="frequency-config">
        <div class="frequency-item">
          <label>默认告警频次：</label>
          <a-select v-model:value="frequencyConfig.default" style="width: 200px">
            <a-select-option value="immediate">立即通知</a-select-option>
            <a-select-option value="5min">每5分钟</a-select-option>
            <a-select-option value="15min">每15分钟</a-select-option>
            <a-select-option value="30min">每30分钟</a-select-option>
            <a-select-option value="1hour">每小时</a-select-option>
            <a-select-option value="1day">每天一次</a-select-option>
          </a-select>
        </div>
        <div class="frequency-item">
          <label>静默时间：</label>
          <a-input-number v-model:value="frequencyConfig.silenceHours" :min="0" :max="24" style="width: 100px" />
          <span>小时</span>
        </div>
        <div class="frequency-item">
          <label>最大重试次数：</label>
          <a-input-number v-model:value="frequencyConfig.maxRetries" :min="1" :max="10" style="width: 100px" />
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <a-button type="primary" @click="saveConfig" :loading="saving">
        <Icon icon="ant-design:save-outlined" />
        保存配置
      </a-button>
      <a-button @click="testAllNotifications" :loading="testing">
        <Icon icon="ant-design:notification-outlined" />
        测试所有通知
      </a-button>
      <a-button @click="resetConfig">
        <Icon icon="ant-design:reload-outlined" />
        重置配置
      </a-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { Icon } from '/@/components/Icon'
import { message } from 'ant-design-vue'

// 通知配置
const configs = reactive({
  platform: {
    enabled: true,
    titleTemplate: '【{level}级告警】{title}'
  },
  sms: {
    enabled: false,
    provider: 'aliyun',
    apiKey: '',
    signature: '数字金融实验室'
  },
  email: {
    enabled: false,
    smtpServer: 'smtp.qq.com',
    port: 587,
    username: '',
    password: ''
  },
  wechat: {
    enabled: false,
    webhookUrl: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
    key: ''
  }
})

// 接收人员配置
const receivers = reactive({
  admin: {
    name: '系统管理员',
    phone: '13800138000',
    email: 'admin@example.com',
    wechat: 'admin_wx'
  },
  operator: {
    name: '运维人员',
    phone: '13800138001',
    email: 'operator@example.com',
    wechat: 'operator_wx'
  },
  device_manager: {
    name: '设备管理员',
    phone: '13800138002',
    email: 'device@example.com',
    wechat: 'device_wx'
  },
  security_manager: {
    name: '安全负责人',
    phone: '13800138003',
    email: 'security@example.com',
    wechat: 'security_wx'
  }
})

// 频次配置
const frequencyConfig = reactive({
  default: 'immediate',
  silenceHours: 2,
  maxRetries: 3
})

const saving = ref(false)
const testing = ref(false)

// 保存配置
const saveConfig = async () => {
  saving.value = true
  try {
    // 这里应该调用API保存配置
    await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟API调用
    message.success('配置保存成功')
  } catch (error) {
    message.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

// 测试所有通知
const testAllNotifications = async () => {
  testing.value = true
  try {
    // 这里应该调用API测试所有通知方式
    await new Promise(resolve => setTimeout(resolve, 2000)) // 模拟API调用
    message.success('所有通知测试完成')
  } catch (error) {
    message.error('通知测试失败')
  } finally {
    testing.value = false
  }
}

// 重置配置
const resetConfig = () => {
  // 重置为默认配置
  Object.assign(configs.platform, { enabled: true, titleTemplate: '【{level}级告警】{title}' })
  Object.assign(configs.sms, { enabled: false, provider: 'aliyun', apiKey: '', signature: '数字金融实验室' })
  Object.assign(configs.email, { enabled: false, smtpServer: 'smtp.qq.com', port: 587, username: '', password: '' })
  Object.assign(configs.wechat, { enabled: false, webhookUrl: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send', key: '' })
  
  Object.assign(frequencyConfig, { default: 'immediate', silenceHours: 2, maxRetries: 3 })
  
  message.info('配置已重置')
}

onMounted(() => {
  // 加载配置
})
</script>

<style lang="less" scoped>
.notification-config-page {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 80px);

  .page-header {
    background-color: #fff;
    padding: 20px 24px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 24px;

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
  }

  .config-section {
    background-color: #fff;
    padding: 24px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 24px;

    h3 {
      font-size: 20px;
      color: #333;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid #eee;
    }

    .config-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 20px;

      .config-card {
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        overflow: hidden;
        transition: all 0.3s ease;

        &:hover {
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }

        .card-header {
          display: flex;
          align-items: center;
          padding: 16px 20px;
          background-color: #fafafa;
          border-bottom: 1px solid #f0f0f0;

          .anticon {
            font-size: 20px;
            margin-right: 12px;
            color: #1890ff;
          }

          h4 {
            font-size: 16px;
            color: #333;
            margin: 0;
            flex: 1;
          }
        }

        .card-content {
          padding: 20px;

          p {
            color: #666;
            margin-bottom: 16px;
            font-size: 14px;
          }

          .config-item {
            margin-bottom: 16px;

            label {
              display: block;
              margin-bottom: 6px;
              font-weight: 500;
              color: #333;
            }
          }
        }
      }
    }

    .receivers-config {
      .receiver-group {
        margin-bottom: 24px;
        padding: 16px;
        background-color: #f7f7f7;
        border-radius: 6px;

        h4 {
          font-size: 16px;
          color: #333;
          margin-bottom: 12px;
        }

        .receiver-info {
          display: flex;
          gap: 12px;
          align-items: center;
        }
      }
    }

    .frequency-config {
      .frequency-item {
        display: flex;
        align-items: center;
        margin-bottom: 16px;

        label {
          width: 120px;
          font-weight: 500;
          color: #333;
        }

        span {
          margin-left: 8px;
          color: #666;
        }
      }
    }
  }

  .action-buttons {
    display: flex;
    gap: 12px;
    justify-content: center;
    padding: 24px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

    .ant-btn {
      height: 40px;
      font-size: 15px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;

      .anticon {
        margin-right: 6px;
      }
    }
  }
}
</style>
