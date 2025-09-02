<template>
  <div class="knowledge-base-container">
    <div class="page-header">
      <h2>共享给我的</h2>
      <p class="subtitle">其他用户分享给您的知识库</p>
    </div>
    
    <a-table
      :columns="columns"
      :data-source="sharedList"
      :loading="loading"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'permission_level'">
          <a-tag :color="getPermissionColor(record.permission_level)">
            {{ getPermissionText(record.permission_level) }}
          </a-tag>
        </template>
        
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a @click="viewKnowledgeBase(record)">查看</a>
            <a @click="downloadDocuments(record)" v-if="record.permission_level !== 'read'">
              下载文档
            </a>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { getSharedWithMe } from '/@/api/rag/knowledge-base.api';

const loading = ref(false);
const sharedList = ref([]);
const router = useRouter();

const columns = [
  { title: '知识库名称', dataIndex: 'kb_name', key: 'kb_name' },
  { title: '分享者', dataIndex: 'shared_by_name', key: 'shared_by_name' },
  { title: '权限级别', dataIndex: 'permission_level', key: 'permission_level' },
  { title: '分享时间', dataIndex: 'create_time', key: 'create_time' },
  { title: '操作', key: 'action', width: 150 },
];

onMounted(() => {
  fetchSharedList();
});

const fetchSharedList = async () => {
  loading.value = true;
  try {
    const res: any = await getSharedWithMe({ page: 1, size: 20 });
    sharedList.value = Array.isArray(res?.data?.records) ? res.data.records : [];
  } catch (e: any) {
    message.error(e?.message || '获取共享列表失败');
  } finally {
    loading.value = false;
  }
};

const viewKnowledgeBase = (record: any) => {
  router.push({ path: '/rag/knowledge-base/my', query: { openDatasetId: String(record.kb_id) } });
};

const downloadDocuments = (record: any) => {
  message.info('下载文档功能待实现');
};

const getPermissionColor = (level: string) => {
  const colors = {
    'read': 'blue',
    'write': 'orange',
    'admin': 'red'
  };
  return colors[level] || 'default';
};

const getPermissionText = (level: string) => {
  const texts = {
    'read': '只读',
    'write': '读写',
    'admin': '管理员'
  };
  return texts[level] || level;
};
</script>

<style scoped>
.knowledge-base-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
}
</style>
