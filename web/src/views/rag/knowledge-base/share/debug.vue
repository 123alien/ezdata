<template>
  <div class="debug-container">
    <h2>知识库分享调试页面</h2>
    
    <div class="debug-section">
      <h3>1. 用户登录状态</h3>
      <p>Token: {{ token || '未登录' }}</p>
      <p>用户信息: {{ userInfo ? JSON.stringify(userInfo, null, 2) : '未获取' }}</p>
    </div>
    
    <div class="debug-section">
      <h3>2. 知识库列表</h3>
      <a-button @click="loadKnowledgeBases" :loading="loading">加载知识库列表</a-button>
      <div v-if="knowledgeBases.length > 0">
        <h4>知识库列表:</h4>
        <ul>
          <li v-for="kb in knowledgeBases" :key="kb.id">
            ID: {{ kb.id }} | 名称: {{ kb.name }} | 创建者: {{ kb.create_by }}
          </li>
        </ul>
      </div>
    </div>
    
    <div class="debug-section">
      <h3>3. 测试分享功能</h3>
      <a-form layout="inline">
        <a-form-item label="知识库ID">
          <a-input v-model:value="testKbId" placeholder="输入知识库ID" />
        </a-form-item>
        <a-form-item label="分享给用户ID">
          <a-input v-model:value="testUserId" placeholder="输入用户ID" />
        </a-form-item>
        <a-form-item label="权限级别">
          <a-select v-model:value="testPermission" style="width: 120px">
            <a-select-option value="read">只读</a-select-option>
            <a-select-option value="write">读写</a-select-option>
            <a-select-option value="admin">管理员</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="testShare" :loading="shareLoading">测试分享</a-button>
        </a-form-item>
      </a-form>
      
      <div v-if="shareResult" class="result-section">
        <h4>分享结果:</h4>
        <pre>{{ JSON.stringify(shareResult, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="debug-section">
      <h3>4. 分享列表</h3>
      <a-button @click="loadShareList" :loading="shareListLoading">加载分享列表</a-button>
      <div v-if="shareList.length > 0">
        <h4>分享列表:</h4>
        <ul>
          <li v-for="share in shareList" :key="share.id">
            ID: {{ share.id }} | 知识库: {{ share.kb_name }} | 分享给: {{ share.shared_with_id }} | 权限: {{ share.permission_level }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { getToken } from '/@/utils/auth';
import { getUserInfo } from '/@/api/sys/user';
import { getDatasets, shareKnowledgeBase, getShareList } from '/@/api/rag/knowledge-base.api';

const token = ref<string>('');
const userInfo = ref<any>(null);
const knowledgeBases = ref<any[]>([]);
const shareList = ref<any[]>([]);
const loading = ref(false);
const shareLoading = ref(false);
const shareListLoading = ref(false);
const shareResult = ref<any>(null);

const testKbId = ref('d013c38f2cef4b26959b243b1993150b');
const testUserId = ref('1');
const testPermission = ref('read');

onMounted(async () => {
  // 获取token和用户信息
  token.value = getToken() || '';
  try {
    userInfo.value = await getUserInfo();
  } catch (e) {
    console.error('获取用户信息失败:', e);
  }
});

const loadKnowledgeBases = async () => {
  loading.value = true;
  try {
    const res: any = await getDatasets({ page: 1, size: 100 });
    knowledgeBases.value = Array.isArray(res?.data?.records) ? res.data.records : [];
    message.success(`加载了 ${knowledgeBases.value.length} 个知识库`);
  } catch (e: any) {
    message.error('加载知识库列表失败: ' + (e?.message || e));
    console.error('加载知识库列表失败:', e);
  } finally {
    loading.value = false;
  }
};

const testShare = async () => {
  if (!testKbId.value || !testUserId.value) {
    message.warning('请填写知识库ID和用户ID');
    return;
  }
  
  shareLoading.value = true;
  shareResult.value = null;
  
  try {
    const res: any = await shareKnowledgeBase({
      kb_id: testKbId.value,
      shared_with_id: testUserId.value,
      permission_level: testPermission.value
    });
    
    shareResult.value = res;
    
    if (res?.code === 200) {
      message.success('分享成功');
    } else {
      message.error('分享失败: ' + (res?.msg || '未知错误'));
    }
  } catch (e: any) {
    shareResult.value = { error: e.message || e };
    message.error('分享异常: ' + (e?.message || e));
    console.error('分享异常:', e);
  } finally {
    shareLoading.value = false;
  }
};

const loadShareList = async () => {
  shareListLoading.value = true;
  try {
    const res: any = await getShareList({ page: 1, size: 20 });
    shareList.value = Array.isArray(res?.data?.records) ? res.data.records : [];
    message.success(`加载了 ${shareList.value.length} 个分享记录`);
  } catch (e: any) {
    message.error('加载分享列表失败: ' + (e?.message || e));
    console.error('加载分享列表失败:', e);
  } finally {
    shareListLoading.value = false;
  }
};
</script>

<style scoped>
.debug-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.debug-section {
  margin-bottom: 32px;
  padding: 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
}

.result-section {
  margin-top: 16px;
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
