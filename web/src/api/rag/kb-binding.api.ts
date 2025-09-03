import { defHttp } from '@/utils/http/axios';

enum Api {
  GetBinding = '/api/rag/kb/binding/binding',
  CreateOrUpdateBinding = '/api/rag/kb/binding/binding',
  DeleteBinding = '/api/rag/kb/binding/binding',
}

/**
 * 获取知识库绑定信息
 * @param params
 */
export const getKnowledgeBaseBinding = (params: { kid: string | number }) =>
  defHttp.get({ url: Api.GetBinding, params });

/**
 * 创建或更新知识库绑定
 * @param params
 */
export const createOrUpdateBinding = (params: {
  kb_id: string | number;
  namespace: string;
  remark?: string;
}) => defHttp.post({ url: Api.CreateOrUpdateBinding, params });

/**
 * 删除知识库绑定
 * @param kb_id
 */
export const deleteKnowledgeBaseBinding = (kb_id: string | number) =>
  defHttp.delete({ url: `${Api.DeleteBinding}/${kb_id}` });
