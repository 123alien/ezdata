<template>
  <div class="knowledge-base-container">
    <div class="page-header">
      <h2>我的知识库</h2>
      <a-button type="primary" @click="showCreateModal">创建知识库</a-button>
    </div>
    
    <a-table
      :columns="columns"
      :data-source="knowledgeBaseList"
      :loading="loading"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="editKnowledgeBase(record)">编辑</a>
            <a @click="deleteKnowledgeBase(record.id)">删除</a>
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
const knowledgeBaseList = ref([]);

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', width: 150 },
];

onMounted(() => {
  fetchKnowledgeBaseList();
});

const fetchKnowledgeBaseList = async () => {
  loading.value = true;
  // TODO: 调用API获取数据
  loading.value = false;
};

const showCreateModal = () => {
  message.info('创建功能待实现');
};

const editKnowledgeBase = (record: any) => {
  message.info('编辑功能待实现');
};

const deleteKnowledgeBase = (id: string) => {
  message.info('删除功能待实现');
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
