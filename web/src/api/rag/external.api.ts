import { defHttp } from '/@/utils/http/axios';
import { ContentTypeEnum } from '/@/enums/httpEnum';

enum Api {
  // SSO Token 相关
  GenerateSSOToken = '/api/rag/external/sso_token',
  AskQuestion = '/api/rag/external/ask',
  
  // TrustRAG 直接访问
  TrustRAGHealth = '/trustrag/health',
  TrustRAGInitialize = '/trustrag/initialize',
  TrustRAGChat = '/trustrag/chat',
  TrustRAGText = '/trustrag/text',
  TrustRAGSearch = '/trustrag/search',
  TrustRAGStatus = '/trustrag/status',
}

/**
 * 生成 SSO Token 用于访问 TrustRAG 服务
 * @param dataset_id 知识库ID（可选）
 * @param namespace TrustRAG 命名空间（可选）
 */
export function generateSSOToken(dataset_id?: string, namespace?: string) {
  return defHttp.post(
    {
      url: Api.GenerateSSOToken,
      data: { dataset_id, namespace },
    },
    { joinPrefix: false }
  );
}

/**
 * 向指定知识库或 namespace 提问
 * @param question 问题
 * @param dataset_id 知识库ID（可选）
 * @param namespace TrustRAG 命名空间（可选）
 */
export function askQuestion(question: string, dataset_id?: string, namespace?: string) {
  return defHttp.post(
    {
      url: Api.AskQuestion,
      data: { question, dataset_id, namespace },
    },
    { joinPrefix: false }
  );
}

/**
 * TrustRAG 健康检查
 */
export function checkTrustRAGHealth() {
  return defHttp.get(
    {
      url: Api.TrustRAGHealth,
    },
    { joinPrefix: false }
  );
}

/**
 * 初始化 TrustRAG 系统
 */
export function initializeTrustRAG() {
  return defHttp.post(
    {
      url: Api.TrustRAGInitialize,
    },
    { joinPrefix: false }
  );
}

/**
 * TrustRAG 聊天接口
 * @param message 消息内容
 */
export function trustRAGChat(message: string) {
  return defHttp.post(
    {
      url: Api.TrustRAGChat,
      data: { message },
    },
    { joinPrefix: false }
  );
}

/**
 * TrustRAG 文本查询
 * @param content 查询内容
 */
export function trustRAGTextQuery(content: string) {
  return defHttp.post(
    {
      url: Api.TrustRAGText,
      data: { content },
    },
    { joinPrefix: false }
  );
}

/**
 * TrustRAG 搜索
 * @param query 搜索查询
 */
export function trustRAGSearch(query: string) {
  return defHttp.post(
    {
      url: Api.TrustRAGSearch,
      data: { query },
    },
    { joinPrefix: false }
  );
}

/**
 * TrustRAG 状态查询
 */
export function getTrustRAGStatus() {
  return defHttp.get(
    {
      url: Api.TrustRAGStatus,
    },
    { joinPrefix: false }
  );
}
