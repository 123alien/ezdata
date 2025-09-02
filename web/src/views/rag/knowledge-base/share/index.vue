<template>
  <div class="knowledge-base-container">
    <div class="page-header">
      <h2>知识库分享</h2>
      <a-button type="primary" @click="showShareModal">分享知识库</a-button>
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

const loading = ref(false);
const shareList = ref([]);

const columns = [
  { title: '知识库名称', dataIndex: 'kb_name', key: 'kb_name' },
  { title: '分享给', dataIndex: 'shared_with_name', key: 'shared_with_name' },
  { title: '权限级别', dataIndex: 'permission_level', key: 'permission_level' },
  { title: '分享时间', dataIndex: 'create_time', key: 'create_time' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', width: 150 },
];

onMounted(() => {
  fetchShareList();
});

const fetchShareList = async () => {
  loading.value = true;
  // TODO: 调用API获取分享列表
  loading.value = false;
};

const showShareModal = () => {
  message.info('分享功能待实现');
};

const editShare = (record: any) => {
  message.info('编辑权限功能待实现');
};

const revokeShare = (id: string) => {
  message.info('撤销分享功能待实现');
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
</style>
