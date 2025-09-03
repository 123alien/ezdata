<template>
  <a-modal
    :open="open"
    :title="title"
    :width="600"
    @ok="handleOk"
    @cancel="handleCancel"
    :confirm-loading="loading"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
    >
      <a-form-item label="知识库名称" name="kb_name">
        <a-input v-model:value="formData.kb_name" disabled />
      </a-form-item>
      
      <a-form-item label="TrustRAG Namespace" name="namespace" required>
        <a-input
          v-model:value="formData.namespace"
          placeholder="请输入TrustRAG的namespace"
          :maxlength="255"
          show-count
        />
      </a-form-item>
      
      <a-form-item label="备注说明" name="remark">
        <a-textarea
          v-model:value="formData.remark"
          placeholder="请输入备注说明（可选）"
          :rows="3"
          :maxlength="500"
          show-count
        />
      </a-form-item>
    </a-form>
    
    <template #footer>
      <a-space>
        <a-button @click="handleCancel">取消</a-button>
        <a-button
          v-if="formData.id"
          type="primary"
          danger
          @click="handleDelete"
          :loading="deleteLoading"
        >
          删除绑定
        </a-button>
        <a-button type="primary" @click="handleOk" :loading="loading">
          {{ formData.id ? '更新' : '创建' }}
        </a-button>
      </a-space>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue';
import { message } from 'ant-design-vue';
import {
  getKnowledgeBaseBinding,
  createOrUpdateBinding,
  deleteKnowledgeBaseBinding,
} from '@/api/rag/kb-binding.api';

interface BindingData {
  id?: string | number;
  kb_id: string | number;
  kb_name: string;
  namespace: string;
  remark?: string;
}

interface Props {
  open: boolean;
  kbData: {
    id: string | number;
    name: string;
  };
}

interface Emits {
  (e: 'update:open', value: boolean): void;
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const formRef = ref();
const loading = ref(false);
const deleteLoading = ref(false);

const formData = reactive<BindingData>({
  kb_id: '',
  kb_name: '',
  namespace: '',
  remark: '',
});

const rules = {
  namespace: [
    { required: true, message: '请输入TrustRAG namespace', trigger: 'blur' },
    { min: 1, max: 255, message: 'namespace长度在1-255个字符之间', trigger: 'blur' },
  ],
  remark: [
    { max: 500, message: '备注长度不能超过500个字符', trigger: 'blur' },
  ],
};

const title = computed(() => {
  return formData.id ? '编辑绑定' : '创建绑定';
});

// 监听弹窗打开，加载数据
watch(
  () => props.open,
  async (newVal) => {
    if (newVal && props.kbData) {
      formData.kb_id = props.kbData.id;
      formData.kb_name = props.kbData.name;
      
      // 加载现有绑定信息
      try {
        const res = await getKnowledgeBaseBinding({ kid: props.kbData.id });
        if (res.success && res.result) {
          formData.id = res.result.id;
          formData.namespace = res.result.namespace;
          formData.remark = res.result.remark || '';
        } else {
          // 没有绑定信息，清空表单
          formData.id = undefined;
          formData.namespace = '';
          formData.remark = '';
        }
      } catch (error) {
        console.error('加载绑定信息失败:', error);
        message.error('加载绑定信息失败');
      }
    }
  }
);

const handleOk = async () => {
  try {
    await formRef.value.validate();
    
    loading.value = true;
    
    const params = {
      kb_id: formData.kb_id,
      namespace: formData.namespace,
      remark: formData.remark,
    };
    
    const res = await createOrUpdateBinding(params);
    
    if (res.success) {
      message.success(res.message || '操作成功');
      emit('success');
      handleCancel();
    } else {
      message.error(res.message || '操作失败');
    }
  } catch (error) {
    console.error('操作失败:', error);
    message.error('操作失败');
  } finally {
    loading.value = false;
  }
};

const handleDelete = async () => {
  try {
    deleteLoading.value = true;
    
    const res = await deleteKnowledgeBaseBinding(formData.kb_id);
    
    if (res.success) {
      message.success(res.message || '删除成功');
      emit('success');
      handleCancel();
    } else {
      message.error(res.message || '删除失败');
    }
  } catch (error) {
    console.error('删除失败:', error);
    message.error('删除失败');
  } finally {
    deleteLoading.value = false;
  }
};

const handleCancel = () => {
  emit('update:open', false);
  formRef.value?.resetFields();
};
</script>
