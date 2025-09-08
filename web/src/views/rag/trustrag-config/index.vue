<template>
  <div class="trustrag-config-container">
    <PageWrapper title="TrustRAG 接口配置" content="配置 TrustRAG 服务的连接参数">
      
      <!-- 接口配置表单 -->
      <div class="config-form">
        <a-card title="接口配置" size="small">
          <a-form
            :model="configForm"
            :label-col="{ span: 6 }"
            :wrapper-col="{ span: 18 }"
            @finish="saveConfig"
          >
            <a-form-item label="服务名称" name="serviceName">
              <a-input
                v-model:value="configForm.serviceName"
                placeholder="请输入服务名称"
              />
            </a-form-item>

            <a-form-item label="基础地址" name="baseUrl" required>
              <a-input
                v-model:value="configForm.baseUrl"
                placeholder="http://localhost:8217"
                addon-before="http://"
              />
            </a-form-item>

            <a-form-item label="端口" name="port">
              <a-input-number
                v-model:value="configForm.port"
                :min="1"
                :max="65535"
                style="width: 100%"
                placeholder="8217"
              />
            </a-form-item>

            <a-form-item label="API 路径" name="apiPath">
              <a-input
                v-model:value="configForm.apiPath"
                placeholder="/api/v1"
                addon-before="/"
              />
            </a-form-item>

            <a-form-item label="超时时间" name="timeout">
              <a-input-number
                v-model:value="configForm.timeout"
                :min="1000"
                :max="60000"
                :step="1000"
                style="width: 100%"
                addon-after="毫秒"
              />
            </a-form-item>

            <a-form-item label="认证方式" name="authType">
              <a-select v-model:value="configForm.authType" style="width: 100%">
                <a-select-option value="jwt">JWT Token</a-select-option>
                <a-select-option value="api_key">API Key</a-select-option>
                <a-select-option value="basic">Basic Auth</a-select-option>
                <a-select-option value="none">无认证</a-select-option>
              </a-select>
            </a-form-item>

            <!-- JWT Token 配置 -->
            <template v-if="configForm.authType === 'jwt'">
              <a-form-item label="JWT Secret" name="jwtSecret">
                <a-input-password
                  v-model:value="configForm.jwtSecret"
                  placeholder="请输入 JWT 密钥"
                />
              </a-form-item>
              <a-form-item label="Token 过期时间" name="tokenExpiry">
                <a-input-number
                  v-model:value="configForm.tokenExpiry"
                  :min="60"
                  :max="86400"
                  style="width: 100%"
                  addon-after="秒"
                />
              </a-form-item>
            </template>

            <!-- API Key 配置 -->
            <template v-if="configForm.authType === 'api_key'">
              <a-form-item label="API Key" name="apiKey">
                <a-input-password
                  v-model:value="configForm.apiKey"
                  placeholder="请输入 API Key"
                />
              </a-form-item>
              <a-form-item label="Header 名称" name="apiKeyHeader">
                <a-input
                  v-model:value="configForm.apiKeyHeader"
                  placeholder="X-API-Key"
                />
              </a-form-item>
            </template>

            <!-- Basic Auth 配置 -->
            <template v-if="configForm.authType === 'basic'">
              <a-form-item label="用户名" name="username">
                <a-input
                  v-model:value="configForm.username"
                  placeholder="请输入用户名"
                />
              </a-form-item>
              <a-form-item label="密码" name="password">
                <a-input-password
                  v-model:value="configForm.password"
                  placeholder="请输入密码"
                />
              </a-form-item>
            </template>

            <a-form-item label="SSL 验证" name="verifySSL">
              <a-switch v-model:checked="configForm.verifySSL" />
              <span class="ml-2">启用 HTTPS SSL 证书验证</span>
            </a-form-item>

            <a-form-item label="重试次数" name="retryCount">
              <a-input-number
                v-model:value="configForm.retryCount"
                :min="0"
                :max="10"
                style="width: 100%"
                addon-after="次"
              />
            </a-form-item>

            <a-form-item :wrapper-col="{ offset: 6, span: 18 }">
              <a-space>
                <a-button type="primary" html-type="submit" :loading="saving">
                  保存配置
                </a-button>
                <a-button @click="testConnection" :loading="testing">
                  测试连接
                </a-button>
                <a-button @click="resetConfig">重置</a-button>
                <a-button @click="loadDefaultConfig">加载默认配置</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>
      </div>

      <!-- 连接测试结果 -->
      <div class="test-result mt-4" v-if="testResult">
        <a-card title="连接测试结果" size="small">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="连接状态">
              <a-tag :color="testResult.success ? 'green' : 'red'">
                {{ testResult.success ? '成功' : '失败' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="响应时间">
              {{ testResult.responseTime }}ms
            </a-descriptions-item>
            <a-descriptions-item label="HTTP 状态码">
              {{ testResult.statusCode }}
            </a-descriptions-item>
            <a-descriptions-item label="服务版本">
              {{ testResult.version || '未知' }}
            </a-descriptions-item>
          </a-descriptions>
          
          <div v-if="testResult.error" class="mt-3">
            <a-alert
              :message="testResult.error"
              type="error"
              show-icon
            />
          </div>
          
          <div v-if="testResult.details" class="mt-3">
            <a-collapse>
              <a-collapse-panel key="1" header="详细信息">
                <pre>{{ JSON.stringify(testResult.details, null, 2) }}</pre>
              </a-collapse-panel>
            </a-collapse>
          </div>
        </a-card>
      </div>

      <!-- 配置预览 -->
      <div class="config-preview mt-4">
        <a-card title="配置预览" size="small">
          <a-tabs>
            <a-tab-pane key="1" tab="完整配置">
              <pre class="config-json">{{ JSON.stringify(configForm, null, 2) }}</pre>
            </a-tab-pane>
            <a-tab-pane key="2" tab="API 端点">
              <div class="api-endpoints">
                <div class="endpoint-item">
                  <strong>健康检查：</strong>
                  <code>{{ getFullUrl('/health') }}</code>
                </div>
                <div class="endpoint-item">
                  <strong>聊天接口：</strong>
                  <code>{{ getFullUrl('/chat') }}</code>
                </div>
                <div class="endpoint-item">
                  <strong>文档摄入：</strong>
                  <code>{{ getFullUrl('/ingest') }}</code>
                </div>
                <div class="endpoint-item">
                  <strong>文本查询：</strong>
                  <code>{{ getFullUrl('/text') }}</code>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </div>

    </PageWrapper>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { PageWrapper } from '/@/components/Page';

interface ConfigForm {
  serviceName: string;
  baseUrl: string;
  port: number;
  apiPath: string;
  timeout: number;
  authType: 'jwt' | 'api_key' | 'basic' | 'none';
  jwtSecret: string;
  tokenExpiry: number;
  apiKey: string;
  apiKeyHeader: string;
  username: string;
  password: string;
  verifySSL: boolean;
  retryCount: number;
}

interface TestResult {
  success: boolean;
  responseTime: number;
  statusCode: number;
  version?: string;
  error?: string;
  details?: any;
}

const configForm = reactive<ConfigForm>({
  serviceName: 'TrustRAG',
  baseUrl: 'localhost',
  port: 8217,
  apiPath: '',
  timeout: 30000,
  authType: 'jwt',
  jwtSecret: 'erwqefdscweer)qi',
  tokenExpiry: 3600,
  apiKey: '',
  apiKeyHeader: 'X-API-Key',
  username: '',
  password: '',
  verifySSL: false,
  retryCount: 3,
});

const saving = ref(false);
const testing = ref(false);
const testResult = ref<TestResult | null>(null);

// 获取完整 URL
const getFullUrl = (endpoint: string) => {
  const protocol = configForm.verifySSL ? 'https' : 'http';
  const baseUrl = configForm.baseUrl.replace(/^https?:\/\//, '');
  const port = configForm.port ? `:${configForm.port}` : '';
  const apiPath = configForm.apiPath ? `/${configForm.apiPath.replace(/^\//, '')}` : '';
  return `${protocol}://${baseUrl}${port}${apiPath}${endpoint}`;
};

// 生成认证头
const getAuthHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  switch (configForm.authType) {
    case 'jwt':
      // 这里可以生成 JWT token 或使用现有的
      break;
    case 'api_key':
      headers[configForm.apiKeyHeader] = configForm.apiKey;
      break;
    case 'basic':
      const credentials = btoa(`${configForm.username}:${configForm.password}`);
      headers['Authorization'] = `Basic ${credentials}`;
      break;
  }

  return headers;
};

// 保存配置
const saveConfig = async () => {
  saving.value = true;
  try {
    // 这里可以保存到本地存储或发送到后端
    localStorage.setItem('trustrag-config', JSON.stringify(configForm));
    message.success('配置保存成功');
  } catch (error) {
    message.error('配置保存失败');
  } finally {
    saving.value = false;
  }
};

// 测试连接
const testConnection = async () => {
  testing.value = true;
  testResult.value = null;
  
  const startTime = Date.now();
  
  try {
    const response = await fetch(getFullUrl('/health'), {
      method: 'GET',
      headers: getAuthHeaders(),
      signal: AbortSignal.timeout(configForm.timeout),
    });

    const responseTime = Date.now() - startTime;
    const data = await response.json();

    testResult.value = {
      success: response.ok,
      responseTime,
      statusCode: response.status,
      version: data.version,
      details: data,
    };

    if (response.ok) {
      message.success('连接测试成功');
    } else {
      message.error(`连接测试失败: ${response.status}`);
    }
  } catch (error: any) {
    const responseTime = Date.now() - startTime;
    testResult.value = {
      success: false,
      responseTime,
      statusCode: 0,
      error: error.message,
    };
    message.error(`连接测试失败: ${error.message}`);
  } finally {
    testing.value = false;
  }
};

// 重置配置
const resetConfig = () => {
  Object.assign(configForm, {
    serviceName: 'TrustRAG',
    baseUrl: 'localhost',
    port: 8217,
    apiPath: '',
    timeout: 30000,
    authType: 'jwt',
    jwtSecret: 'erwqefdscweer)qi',
    tokenExpiry: 3600,
    apiKey: '',
    apiKeyHeader: 'X-API-Key',
    username: '',
    password: '',
    verifySSL: false,
    retryCount: 3,
  });
  testResult.value = null;
  message.info('配置已重置');
};

// 加载默认配置
const loadDefaultConfig = () => {
  resetConfig();
  message.info('已加载默认配置');
};

// 加载保存的配置
const loadSavedConfig = () => {
  try {
    const saved = localStorage.getItem('trustrag-config');
    if (saved) {
      const parsed = JSON.parse(saved);
      Object.assign(configForm, parsed);
      message.info('已加载保存的配置');
    }
  } catch (error) {
    console.error('加载配置失败:', error);
  }
};

// 生命周期
onMounted(() => {
  loadSavedConfig();
});
</script>

<style scoped>
.trustrag-config-container {
  padding: 20px;
}

.config-form {
  margin-bottom: 20px;
}

.test-result {
  margin-bottom: 20px;
}

.config-preview {
  margin-bottom: 20px;
}

.config-json {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.api-endpoints {
  padding: 16px;
}

.endpoint-item {
  margin-bottom: 12px;
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.endpoint-item code {
  background-color: #e6f7ff;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.ml-2 {
  margin-left: 8px;
}
</style>
