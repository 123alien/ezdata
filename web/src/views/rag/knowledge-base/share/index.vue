<template>
  <div class="knowledge-base-container">
    <div class="page-header">
      <h2>知识库分享</h2>
      <a-space>
        <a-select v-model:value="selectedKbId" style="width: 220px" placeholder="选择知识库">
          <a-select-option v-for="kb in kbOptions" :key="kb.id" :value="kb.id">{{ kb.name }}</a-select-option>
        </a-select>
        <a-select v-model:value="selectedUserId" show-search style="width: 220px" placeholder="选择用户" :filter-option="filterUser">
          <a-select-option v-for="u in userOptions" :key="u.id" :value="u.id">{{ u.username || (u.nickname || u.id) }}</a-select-option>
        </a-select>
        <a-select v-model:value="selectedPermission" style="width: 160px" placeholder="权限">
          <a-select-option value="read">只读</a-select-option>
          <a-select-option value="write">读写</a-select-option>
          <a-select-option value="admin">管理员</a-select-option>
        </a-select>
        <a-button type="primary" @click="quickShare">分享</a-button>
        <a-button @click="showManualShare">手动输入</a-button>
      </a-space>
    </div>
    
    <a-table
      :columns="columns"
      :data-source="shareList"
      :loading="loading"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'permission_level'">
          <a-tag :color="getPermissionColor(record.permission_level)">
            {{ getPermissionText(record.permission_level) }}
          </a-tag>
        </template>
        
        <template v-else-if="column.key === 'status'">
          <a-tag :color="record.status === 1 ? 'green' : 'red'">
            {{ record.status === 1 ? '有效' : '失效' }}
          </a-tag>
        </template>
        
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a @click="editShare(record)">编辑权限</a>
            <a @click="revokeShare(record.id)">撤销分享</a>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { getShareList, shareKnowledgeBase, updateSharePermission, deleteShare, getDatasets } from '/@/api/rag/knowledge-base.api';
import { getUserList } from '/@/api/sys/user';

const loading = ref(false);
const shareList = ref([]);
const kbOptions = ref<any[]>([]);
const userOptions = ref<any[]>([]);
const selectedKbId = ref<string | undefined>();
const selectedUserId = ref<string | undefined>();
const selectedPermission = ref<string>('read');

const columns = [
  { title: '知识库名称', dataIndex: 'kb_name', key: 'kb_name' },
  // 后端当前返回 shared_with_id，这里先展示ID；后续可联表显示用户名
  { title: '分享给(用户ID)', dataIndex: 'shared_with_id', key: 'shared_with_id' },
  { title: '权限级别', dataIndex: 'permission_level', key: 'permission_level' },
  { title: '分享时间', dataIndex: 'create_time', key: 'create_time' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', width: 150 },
];

onMounted(() => {
  fetchShareList();
  preloadKbAndUsers();
});

const fetchShareList = async () => {
  loading.value = true;
  try {
    const res: any = await getShareList({ page: 1, size: 20 });
    // isTransformResponse=false 时，这里是 {code,data,msg}
    shareList.value = Array.isArray(res?.data?.records) ? res.data.records : [];
  } catch (e: any) {
    message.error(e?.message || '获取分享列表失败');
  } finally {
    loading.value = false;
  }
};

const showManualShare = () => {
  // 手动输入分享信息
  const kbId = window.prompt('输入知识库ID（kb_id）：\n例如：d013c38f2cef4b26959b243b1993150b');
  if (!kbId) return;
  const sharedWithId = window.prompt('输入被分享用户ID（shared_with_id）：\n例如：1');
  if (!sharedWithId) return;
  const permission = window.prompt('输入权限级别（read/write/admin），默认 read：') || 'read';
  doShare(kbId, sharedWithId, permission);
};

const editShare = (record: any) => {
  const permission = window.prompt('调整权限级别（read/write/admin）：', record.permission_level || 'read') || record.permission_level;
  if (!permission) return;
  doUpdatePermission(record.id, permission);
};

const revokeShare = (id: string) => {
  doRevoke(id);
};

const getPermissionColor = (level: string) => {
  const colors = {
    'read': 'blue',
    'write': 'orange',
    'admin': 'red'
  } as Record<string, string>;
  return colors[level] || 'default';
};

const getPermissionText = (level: string) => {
  const texts = {
    'read': '只读',
    'write': '读写',
    'admin': '管理员'
  } as Record<string, string>;
  return texts[level] || level;
};

function filterUser(input: string, option: any) {
  const label = (option?.children ?? '').toLowerCase?.() || '';
  return label.includes((input || '').toLowerCase());
}

async function preloadKbAndUsers() {
  try {
    const kbRes: any = await getDatasets({ page: 1, size: 100 });
    kbOptions.value = Array.isArray(kbRes?.data?.records) ? kbRes.data.records : [];
  } catch {}
  try {
    const userRes: any = await getUserList({ page: 1, size: 100 });
    userOptions.value = Array.isArray(userRes?.data?.records) ? userRes.data.records : [];
  } catch {}
}

async function quickShare() {
  if (!selectedKbId.value) return message.warning('请选择知识库');
  if (!selectedUserId.value) return message.warning('请选择用户');
  await doShare(String(selectedKbId.value), String(selectedUserId.value), selectedPermission.value || 'read');
}

async function doShare(kb_id: string, shared_with_id: string, permission_level: string) {
  try {
    loading.value = true;
    const res: any = await shareKnowledgeBase({ kb_id, shared_with_id, permission_level });
    if (res?.code === 200) {
      message.success('分享成功');
      fetchShareList();
    } else {
      message.error(res?.msg || '分享失败');
    }
  } catch (e: any) {
    message.error(e?.message || '分享失败');
  } finally {
    loading.value = false;
  }
}

async function doUpdatePermission(share_id: string, permission_level: string) {
  try {
    loading.value = true;
    const res: any = await updateSharePermission({ share_id, permission_level });
    if (res?.code === 200) {
      message.success('更新成功');
      fetchShareList();
    } else {
      message.error(res?.msg || '更新失败');
    }
  } catch (e: any) {
    message.error(e?.message || '更新失败');
  } finally {
    loading.value = false;
  }
}

async function doRevoke(share_id: string) {
  try {
    loading.value = true;
    const res: any = await deleteShare({ share_id });
    if (res?.code === 200) {
      message.success('已撤销');
      fetchShareList();
    } else {
      message.error(res?.msg || '撤销失败');
    }
  } catch (e: any) {
    message.error(e?.message || '撤销失败');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.knowledge-base-container {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
</style>
