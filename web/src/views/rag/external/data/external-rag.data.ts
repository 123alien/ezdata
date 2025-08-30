export interface TrustRAGHealth {
  status: 'healthy' | 'initializing' | 'error';
  version: string;
  components: {
    rag_system: boolean;
    chunks_loaded: boolean;
    index_ready: boolean;
  };
  message?: string;
}

export interface TrustRAGStatus {
  service: string;
  base_url: string;
  timestamp: string;
  health: TrustRAGHealth;
  endpoints: {
    health: string;
    chat: string;
    text: string;
    openai: string;
    initialize: string;
  };
}

export interface TrustRAGResponse {
  response: string;
}

export interface TrustRAGError {
  error: string;
  detail: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface SearchParams {
  query: string;
  topK?: number;
  threshold?: number;
}

export interface SearchResult {
  query: string;
  results: Array<{
    content: string;
    score?: number;
    metadata?: Record<string, any>;
  }>;
}

export interface ConnectionTestResult {
  health: {
    status: 'success' | 'failed';
    result?: TrustRAGHealth;
    error?: string;
  };
  chat: {
    status: 'success' | 'failed';
    result?: TrustRAGResponse;
    error?: string;
  };
  text: {
    status: 'success' | 'failed';
    result?: string;
    error?: string;
  };
}

// 预设问题
export const presetQuestions = [
  '汽车保养需要注意什么？',
  '如何更换机油？',
  '轮胎保养有哪些要点？',
  '汽车日常维护有哪些要点？',
  '如何检查轮胎气压？',
  '汽车内饰如何保养？',
  '发动机保养有哪些注意事项？',
  '制动系统如何维护？',
  '汽车电池如何保养？',
  '雨刮器如何更换？'
];

// 服务状态颜色映射
export const statusColorMap = {
  healthy: '#52c41a',
  initializing: '#faad14',
  error: '#ff4d4f'
};

// 服务状态文本映射
export const statusTextMap = {
  healthy: '健康',
  initializing: '初始化中',
  error: '错误'
};
