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
            <a @click="showBindingModal(record)" v-if="record.permission_level !== 'read'">绑定索引</a>
            <a @click="downloadDocuments(record)" v-if="record.permission_level !== 'read'">
              下载文档
            </a>
          </a-space>
        </template>
      </template>
    </a-table>
    <!-- 只读文档查看弹窗 -->
    <a-modal
      v-model:open="documentModalVisible"
      :title="(currentKb?.kb_name || '知识库') + ' - 文档列表'"
      width="80%"
      :footer="null"
    >
      <a-table
        :columns="documentColumns"
        :data-source="documentList"
        :loading="documentLoading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a @click="viewDocument(record)">查看</a>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- 绑定管理弹窗 -->
    <BindingModal
      v-model:open="bindingModalVisible"
      :kb-data="currentBindingKb"
      @success="handleBindingSuccess"
    />

    <!-- 文档详情弹窗（简单JSON预览） -->
    <a-modal
      v-model:open="docDetailVisible"
      title="文档详情"
      width="700px"
      :confirm-loading="docDetailLoading"
      @ok="() => (docDetailVisible = false)"
      @cancel="() => (docDetailVisible = false)"
    >
      <pre style="max-height: 60vh; overflow: auto; white-space: pre-wrap;">{{ JSON.stringify(docDetail, null, 2) }}</pre>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { getSharedWithMe, getDocuments, getDocumentDetail } from '/@/api/rag/knowledge-base.api';
import BindingModal from '../components/BindingModal.vue';

const loading = ref(false);
const sharedList = ref([]);
// 文档查看（只读）
const documentModalVisible = ref(false);
const documentLoading = ref(false);
const documentList = ref<any[]>([]);
const currentKb = ref<any>(null);

// 绑定管理相关
const bindingModalVisible = ref(false);
const currentBindingKb = ref<any>(null);

const columns = [
  { title: '知识库名称', dataIndex: 'kb_name', key: 'kb_name' },
  { title: '分享者', dataIndex: 'shared_by_name', key: 'shared_by_name' },
  { title: '权限级别', dataIndex: 'permission_level', key: 'permission_level' },
  { title: '分享时间', dataIndex: 'create_time', key: 'create_time' },
  { title: '操作', key: 'action', width: 150 },
];

const documentColumns = [
  { title: '文档名称', dataIndex: 'name', key: 'name' },
  { title: '文档类型', dataIndex: 'document_type', key: 'document_type' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '上传时间', dataIndex: 'create_time', key: 'create_time' },
  { title: '操作', key: 'action', width: 120 },
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

const viewKnowledgeBase = async (record: any) => {
  currentKb.value = record;
  documentModalVisible.value = true;
  await fetchDocumentList(record.kb_id);
};

async function fetchDocumentList(datasetId: string) {
  try {
    documentLoading.value = true;
    const res: any = await getDocuments({ dataset_id: datasetId });
    if (res && res.code === 200) {
      documentList.value = Array.isArray(res?.data?.records) ? res.data.records : [];
    } else {
      message.error(res?.msg || '获取文档列表失败');
    }
  } catch (e: any) {
    message.error(e?.message || '获取文档列表失败');
  } finally {
    documentLoading.value = false;
  }
}

const downloadDocuments = (record: any) => {
  message.info('下载文档功能待实现');
};

// 文档详情查看
const docDetailVisible = ref(false);
const docDetailLoading = ref(false);
const docDetail = ref<Record<string, any> | null>(null);

async function viewDocument(record: any) {
  try {
    docDetailVisible.value = true;
    docDetailLoading.value = true;
    const res: any = await getDocumentDetail({ id: record.id });
    if (res && res.code === 200) {
      docDetail.value = res.data || {};
    } else {
      message.error(res?.msg || '获取文档详情失败');
    }
  } catch (e: any) {
    message.error(e?.message || '获取文档详情失败');
  } finally {
    docDetailLoading.value = false;
  }
}

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

// 显示绑定弹窗
const showBindingModal = (record: any) => {
  currentBindingKb.value = {
    id: record.kb_id,
    name: record.kb_name,
  };
  bindingModalVisible.value = true;
};

// 绑定成功回调
const handleBindingSuccess = () => {
  message.success('绑定操作成功');
  // 可以在这里刷新共享列表或做其他操作
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
