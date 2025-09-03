<template>
  <div class="knowledge-base-container">
    <div class="page-header">
      <h2>我的知识库</h2>
      <a-button type="primary" @click="showCreateModal">创建知识库</a-button>
    </div>
    
    <!-- 知识库列表 -->
    <a-table
      :columns="columns"
      :data-source="datasetList"
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <a @click="viewDataset(record)">{{ record.name }}</a>
        </template>
        
        <template v-else-if="column.key === 'status'">
          <a-tag :color="record.status === 1 ? 'green' : 'red'">
            {{ record.status === 1 ? '启用' : '禁用' }}
          </a-tag>
        </template>
        
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a @click="viewDataset(record)">查看</a>
            <a @click="editDataset(record)">编辑</a>
            <a @click="manageDocuments(record)">文档管理</a>
            <a @click="showBindingModal(record)">绑定索引</a>
            <a @click="deleteDataset(record)" class="text-danger">删除</a>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 创建/编辑知识库弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑知识库' : '创建知识库'"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="modalLoading"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="知识库名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入知识库名称" />
        </a-form-item>
        
        <a-form-item label="描述" name="description">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入知识库描述"
            :rows="3"
          />
        </a-form-item>
        
        <a-form-item label="状态" name="status">
          <a-radio-group v-model:value="formData.status">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 绑定管理弹窗 -->
    <BindingModal
      v-model:open="bindingModalVisible"
      :kb-data="currentBindingKb"
      @success="handleBindingSuccess"
    />

    <!-- 文档管理弹窗 -->
    <a-modal
      v-model:open="documentModalVisible"
      title="文档管理"
      width="80%"
      :footer="null"
    >
      <div class="document-management">
        <div class="document-header">
          <h3>{{ currentDataset?.name }} - 文档列表</h3>
          <a-upload
            :custom-request="handleDocumentUpload"
            :show-upload-list="false"
            accept=".pdf,.doc,.docx,.txt,.md"
          >
            <a-button type="primary">
              <template #icon>
                <UploadOutlined />
              </template>
              上传文档
            </a-button>
          </a-upload>
        </div>
        
        <a-table
          :columns="documentColumns"
          :data-source="documentList"
          :loading="documentLoading"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="getDocumentStatusColor(record.status)">
                {{ getDocumentStatusText(record.status) }}
              </a-tag>
            </template>
            
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a @click="viewDocument(record)">查看</a>
                <a @click="deleteDocument(record)" class="text-danger">删除</a>
                <a @click="vectorizeDocument(record)" v-if="record.status === 1">
                  向量化
                </a>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { UploadOutlined } from '@ant-design/icons-vue';
import {
  getDatasets,
  createDataset,
  updateDataset,
  deleteDataset as deleteDatasetApi,
  getDocuments,
  uploadDocument,
  deleteDocument as deleteDocumentApi,
  trustRAGVectorize,
} from '/@/api/rag/knowledge-base.api';
import BindingModal from '../components/BindingModal.vue';

// 响应式数据
const loading = ref(false);
const modalVisible = ref(false);
const modalLoading = ref(false);
const isEdit = ref(false);
const datasetList = ref<any[]>([]);
const formRef = ref();

// 文档管理相关
const documentModalVisible = ref(false);
const documentLoading = ref(false);
const documentList = ref<any[]>([]);
const currentDataset = ref<any>(null);

// 绑定管理相关
const bindingModalVisible = ref(false);
const currentBindingKb = ref<any>(null);

// 表单数据
const formData = reactive({
  id: '',
  name: '',
  description: '',
  status: 1,
});

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' },
  ],
};

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
});

// 知识库表格列定义
const columns = [
  { title: '知识库名称', dataIndex: 'name', key: 'name', width: 200 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'create_time', key: 'create_time', width: 180 },
  { title: '操作', key: 'action', width: 300, fixed: 'right' },
];

// 文档表格列定义
const documentColumns = [
  { title: '文档名称', dataIndex: 'name', key: 'name' },
  { title: '文档类型', dataIndex: 'document_type', key: 'document_type' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '上传时间', dataIndex: 'create_time', key: 'create_time', width: 180 },
  { title: '操作', key: 'action', width: 200 },
];

// 生命周期
onMounted(() => {
  // 延迟一点时间再调用API，确保页面完全加载
  setTimeout(async () => {
    await fetchDatasetList();
    // 若从“共享给我的”跳转携带 openDatasetId，则直接打开文档管理
    const url = new URL(window.location.href);
    const openId = url.searchParams.get('openDatasetId');
    if (openId) {
      const target = datasetList.value.find((d: any) => String(d.id) === String(openId));
      if (target) {
        manageDocuments(target);
      }
    }
  }, 100);
});

// 获取知识库列表
const fetchDatasetList = async () => {
  try {
    loading.value = true;
    const params = {
      pageNo: pagination.current,
      pageSize: pagination.pageSize,
    };
    
    console.log('开始获取知识库列表，参数:', params);
    const response = await getDatasets(params);
    console.log('API响应:', response);
    
    if (response && response.code === 200) {
      console.log('API调用成功，数据:', response.data);
      datasetList.value = response.data?.records || [];
      pagination.total = response.data?.total || 0;
      console.log('设置数据完成，记录数:', datasetList.value.length);
    } else {
      console.log('API调用失败，状态码:', response?.code, '消息:', response?.msg);
      message.error(response?.msg || '获取知识库列表失败');
    }
  } catch (error) {
    console.error('API调用异常:', error);
    message.error('获取知识库列表失败');
  } finally {
    loading.value = false;
  }
};

// 表格变化处理
const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchDatasetList();
};

// 显示创建弹窗
const showCreateModal = () => {
  isEdit.value = false;
  resetForm();
  modalVisible.value = true;
};

// 编辑知识库
const editDataset = (record: any) => {
  isEdit.value = true;
  Object.assign(formData, record);
  modalVisible.value = true;
};

// 查看知识库
const viewDataset = (record: any) => {
  message.info('查看知识库功能待实现');
};

// 管理文档
const manageDocuments = async (record: any) => {
  currentDataset.value = record;
  documentModalVisible.value = true;
  await fetchDocumentList(record.id);
};

// 获取文档列表
const fetchDocumentList = async (datasetId: string) => {
  try {
    documentLoading.value = true;
    const params = {
      dataset_id: datasetId,
    };
    
    const response = await getDocuments(params);
    if (response && response.code === 200) {
      documentList.value = response.data?.records || [];
    } else {
      message.error(response?.msg || '获取文档列表失败');
    }
  } catch (error) {
    message.error('获取文档列表失败');
    console.error(error);
  } finally {
    documentLoading.value = false;
  }
};

// 文档上传处理
const handleDocumentUpload = async (options: any) => {
  if (!currentDataset.value) return;
  
  try {
    const formData = new FormData();
    formData.append('file', options.file);
    formData.append('dataset_id', currentDataset.value.id);
    formData.append('document_type', 'upload_file');
    formData.append('name', options.file.name);
    
    const response = await uploadDocument(formData);
    if (response && response.code === 200) {
      message.success('文档上传成功');
      await fetchDocumentList(currentDataset.value.id);
    } else {
      message.error(response?.msg || '文档上传失败');
    }
  } catch (error) {
    message.error('文档上传失败');
    console.error(error);
  }
};

// 查看文档
const viewDocument = (record: any) => {
  message.info('查看文档功能待实现');
};

// 删除文档
const deleteDocument = async (record: any) => {
  if (!currentDataset.value) return;
  
  try {
    const response = await deleteDocumentApi({ id: record.id });
    if (response && response.code === 200) {
      message.success('删除成功');
      await fetchDocumentList(currentDataset.value.id);
    } else {
      message.error(response?.msg || '删除失败');
    }
  } catch (error) {
    message.error('删除失败');
    console.error(error);
  }
};

// 向量化文档（使用TrustRAG）
const vectorizeDocument = async (record: any) => {
  if (!currentDataset.value) return;
  
  try {
    const response = await trustRAGVectorize({
      document_id: record.id,
      dataset_id: currentDataset.value.id,
    });
    if (response && response.code === 200) {
      message.success('向量化任务已启动');
      await fetchDocumentList(currentDataset.value.id);
    } else {
      message.error(response?.msg || '向量化失败');
    }
  } catch (error) {
    message.error('向量化失败');
    console.error(error);
  }
};

// 删除知识库
const deleteDataset = async (record: any) => {
  try {
    const response = await deleteDatasetApi({ id: record.id });
    if (response && response.code === 200) {
      message.success('删除成功');
      fetchDatasetList();
    } else {
      message.error(response?.msg || '删除失败');
    }
  } catch (error) {
    message.error('删除失败');
    console.error(error);
  }
};

// 弹窗确认
const handleModalOk = async () => {
  try {
    await formRef.value.validate();
    modalLoading.value = true;

    const response = isEdit.value
      ? await updateDataset(formData)
      : await createDataset(formData);

    if (response && response.code === 200) {
      message.success(isEdit.value ? '更新成功' : '创建成功');
      modalVisible.value = false;
      fetchDatasetList();
    } else {
      message.error(response?.msg || '操作失败');
    }
  } catch (error) {
    message.error('操作失败');
    console.error(error);
  } finally {
    modalLoading.value = false;
  }
};

// 弹窗取消
const handleModalCancel = () => {
  modalVisible.value = false;
  resetForm();
};

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    id: '',
    name: '',
    description: '',
    status: 1,
  });
  formRef.value?.resetFields();
};

// 文档状态相关
const getDocumentStatusColor = (status: number) => {
  const colors = {
    1: 'orange',   // 待处理
    2: 'blue',     // 处理中
    3: 'green',    // 已处理
    4: 'red',      // 处理失败
  };
  return colors[status] || 'default';
};

const getDocumentStatusText = (status: number) => {
  const texts = {
    1: '待处理',
    2: '处理中',
    3: '已处理',
    4: '处理失败',
  };
  return texts[status] || '未知';
};

// 显示绑定弹窗
const showBindingModal = (record: any) => {
  currentBindingKb.value = {
    id: record.id,
    name: record.name,
  };
  bindingModalVisible.value = true;
};

// 绑定成功回调
const handleBindingSuccess = () => {
  message.success('绑定操作成功');
  // 可以在这里刷新知识库列表或做其他操作
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

.document-management {
  .document-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
    }
  }
}

.text-danger {
  color: #ff4d4f;
}
</style>
