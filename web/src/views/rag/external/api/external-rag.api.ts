import { defHttp } from '/@/utils/http/axios';

export enum Api {
  // 基础接口
  health = '/rag/external/health',
  initialize = '/rag/external/initialize',
  status = '/rag/external/status',
  test = '/rag/external/test',
  
  // 查询接口
  chat = '/rag/external/chat',
  text = '/rag/external/text',
  openai = '/rag/external/v1/chat/completions',
  search = '/rag/external/search',
  searchText = '/rag/external/search_text',
}

/**
 * 健康检查
 */
export const healthCheck = () => {
  return defHttp.get({ url: Api.health });
};

/**
 * 初始化RAG系统
 */
export const initializeRAG = () => {
  return defHttp.post({ url: Api.initialize });
};

/**
 * 获取服务状态
 */
export const getStatus = () => {
  return defHttp.get({ url: Api.status });
};

/**
 * 测试连接
 */
export const testConnection = () => {
  return defHttp.post({ url: Api.test });
};

/**
 * 聊天查询
 * @param message 用户消息
 */
export const chat = (message: string) => {
  return defHttp.post({ 
    url: Api.chat, 
    params: { message } 
  });
};

/**
 * 文本查询
 * @param query 查询内容
 */
export const textQuery = (query: string) => {
  return defHttp.post({ 
    url: Api.text, 
    params: { query } 
  });
};

/**
 * OpenAI兼容接口
 * @param messages 消息列表
 * @param model 模型名称
 * @param temperature 温度参数
 * @param maxTokens 最大token数
 */
export const openaiChat = (params: {
  messages: Array<{ role: string; content: string }>;
  model?: string;
  temperature?: number;
  maxTokens?: number;
}) => {
  return defHttp.post({ 
    url: Api.openai, 
    params 
  });
};

/**
 * 知识检索
 * @param query 检索查询
 * @param topK 返回结果数量
 * @param threshold 相似度阈值
 */
export const search = (params: {
  query: string;
  topK?: number;
  threshold?: number;
}) => {
  return defHttp.post({ 
    url: Api.search, 
    params 
  });
};

/**
 * 纯文本知识检索
 * @param query 检索查询
 */
export const searchText = (query: string) => {
  return defHttp.post({ 
    url: Api.searchText, 
    params: { query } 
  });
};
