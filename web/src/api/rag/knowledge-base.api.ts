import { defHttp } from '/@/utils/http/axios';

export enum Api {
  // 我的知识库
  GetMyKnowledgeBases = '/rag/knowledge-base/my/list',
  CreateKnowledgeBase = '/rag/knowledge-base/my/create',
  UpdateKnowledgeBase = '/rag/knowledge-base/my/update',
  DeleteKnowledgeBase = '/rag/knowledge-base/my/delete',
  
  // 知识库分享
  GetShareList = '/rag/knowledge-base/share/list',
  ShareKnowledgeBase = '/rag/knowledge-base/share/create',
  UpdateSharePermission = '/rag/knowledge-base/share/update',
  DeleteShare = '/rag/knowledge-base/share/delete',
  
  // 共享给我的
  GetSharedWithMe = '/rag/knowledge-base/shared/list',
  
  // 通用
  GetKnowledgeBaseDetail = '/rag/knowledge-base/detail',
}

// 我的知识库
export const getMyKnowledgeBases = (params?: any) => {
  return defHttp.get({ url: Api.GetMyKnowledgeBases, params });
};

export const createKnowledgeBase = (data: any) => {
  return defHttp.post({ url: Api.CreateKnowledgeBase, data });
};

export const updateKnowledgeBase = (id: string | number, data: any) => {
  return defHttp.put({ url: `${Api.UpdateKnowledgeBase}/${id}`, data });
};

export const deleteKnowledgeBase = (id: string | number) => {
  return defHttp.delete({ url: `${Api.DeleteKnowledgeBase}/${id}` });
};

// 知识库分享
export const getShareList = (params?: any) => {
  return defHttp.get({ url: Api.GetShareList, params });
};

export const shareKnowledgeBase = (data: any) => {
  return defHttp.post({ url: Api.ShareKnowledgeBase, data });
};

export const updateSharePermission = (id: string | number, data: any) => {
  return defHttp.put({ url: `${Api.UpdateSharePermission}/${id}`, data });
};

export const deleteShare = (id: string | number) => {
  return defHttp.delete({ url: `${Api.DeleteShare}/${id}` });
};

// 共享给我的
export const getSharedWithMe = (params?: any) => {
  return defHttp.get({ url: Api.GetSharedWithMe, params });
};

// 通用
export const getKnowledgeBaseDetail = (id: string | number) => {
  return defHttp.get({ url: `${Api.GetKnowledgeBaseDetail}/${id}` });
};
