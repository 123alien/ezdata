import { defHttp } from '/@/utils/http/axios';

export enum Api {
  // 知识库管理 - 使用ezdata自带的dataset API
  GetDatasets = '/api/rag/dataset/list',                    // 获取知识库列表
  CreateDataset = '/api/rag/dataset/add',                   // 创建知识库
  UpdateDataset = '/api/rag/dataset/edit',                  // 更新知识库
  DeleteDataset = '/api/rag/dataset/delete',                // 删除知识库
  GetDatasetDetail = '/api/rag/dataset/queryById',          // 获取知识库详情
  
  // 文档管理 - 使用ezdata自带的document API
  GetDocuments = '/api/rag/document/list',                  // 获取文档列表
  UploadDocument = '/api/rag/document/add',                 // 上传文档
  UpdateDocument = '/api/rag/document/edit',                // 更新文档
  DeleteDocument = '/api/rag/document/delete',              // 删除文档
  GetDocumentDetail = '/api/rag/document/queryById',        // 获取文档详情
  TrainDocument = '/api/rag/document/train',                // 训练文档（向量化）
  
  // TrustRAG向量化接口
  TrustRAGVectorize = '/api/rag/external/vectorize',        // TrustRAG向量化
  TrustRAGSearch = '/api/rag/external/search',              // TrustRAG检索
  
  // 知识库分享 - 使用我们自定义的分享功能
  GetShareList = '/api/rag/kb/share/list',
  ShareKnowledgeBase = '/api/rag/kb/share',
  UpdateSharePermission = '/api/rag/kb/share/update',
  DeleteShare = '/api/rag/kb/share/delete',
  
  // 共享给我的
  GetSharedWithMe = '/api/rag/kb/shared/list',
}

// ========== 知识库管理（ezdata dataset API）==========
export const getDatasets = (params?: any) => {
  return defHttp.get({ url: Api.GetDatasets, params }, { joinPrefix: false, isTransformResponse: false });
};

export const createDataset = (data: any) => {
  return defHttp.post({ url: Api.CreateDataset, data }, { joinPrefix: false, isTransformResponse: false });
};

export const updateDataset = (data: any) => {
  return defHttp.post({ url: Api.UpdateDataset, data }, { joinPrefix: false, isTransformResponse: false });
};

export const deleteDataset = (data: any) => {
  return defHttp.post({ url: Api.DeleteDataset, data }, { joinPrefix: false, isTransformResponse: false });
};

export const getDatasetDetail = (params: any) => {
  return defHttp.get({ url: Api.GetDatasetDetail, params }, { joinPrefix: false, isTransformResponse: false });
};

// ========== 文档管理（ezdata document API）==========
export const getDocuments = (params?: any) => {
  return defHttp.get({ url: Api.GetDocuments, params }, { joinPrefix: false, isTransformResponse: false });
};

export const uploadDocument = (data: any) => {
  return defHttp.post({ url: Api.UploadDocument, data }, { joinPrefix: false, isTransformResponse: false });
};

export const updateDocument = (data: any) => {
  return defHttp.post({ url: Api.UpdateDocument, data }, { joinPrefix: false, isTransformResponse: false });
};

export const deleteDocument = (data: any) => {
  return defHttp.post({ url: Api.DeleteDocument, data }, { joinPrefix: false, isTransformResponse: false });
};

export const getDocumentDetail = (params: any) => {
  return defHttp.get({ url: Api.GetDocumentDetail, params }, { joinPrefix: false, isTransformResponse: false });
};

// ========== TrustRAG向量化和检索 ==========
export const trustRAGVectorize = (data: any) => {
  return defHttp.post({ url: Api.TrustRAGVectorize, data }, { joinPrefix: false, isTransformResponse: false });
};

export const trustRAGSearch = (params: any) => {
  return defHttp.get({ url: Api.TrustRAGSearch, params }, { joinPrefix: false, isTransformResponse: false });
};

// ========== 知识库分享 ==========
export const getShareList = (params?: any) => {
  return defHttp.get({ url: Api.GetShareList, params }, { joinPrefix: false, isTransformResponse: false });
};

export const shareKnowledgeBase = (data: any) => {
  return defHttp.post({ url: Api.ShareKnowledgeBase, data }, { joinPrefix: false, isTransformResponse: false });
};

export const updateSharePermission = (data: any) => {
  return defHttp.post({ url: Api.UpdateSharePermission, data }, { joinPrefix: false, isTransformResponse: false });
};

export const deleteShare = (data: any) => {
  return defHttp.post({ url: Api.DeleteShare, data }, { joinPrefix: false, isTransformResponse: false });
};

// ========== 共享给我的 ==========
export const getSharedWithMe = (params?: any) => {
  return defHttp.get({ url: Api.GetSharedWithMe, params }, { joinPrefix: false, isTransformResponse: false });
};
