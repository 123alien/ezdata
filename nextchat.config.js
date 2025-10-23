// NextChat 配置文件
module.exports = {
  // API 配置
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://1118qg49520ma.vicp.fun',
  apiKey: process.env.NEXT_PUBLIC_API_KEY || 'your-trustrag-api-key',
  
  // 模型配置
  model: process.env.NEXT_PUBLIC_MODEL_NAME || 'trustrag',
  
  // 界面配置
  title: process.env.NEXT_PUBLIC_TITLE || '数字金融实验室',
  description: process.env.NEXT_PUBLIC_DESCRIPTION || '基于 TrustRAG 的智能问答系统',
  
  // TrustRAG 集成配置
  trustrag: {
    baseUrl: process.env.TRUSTRAG_BASE_URL || 'http://1118qg49520ma.vicp.fun',
    port: process.env.TRUSTRAG_PORT || '8217',
    namespace: process.env.TRUSTRAG_NAMESPACE || 'ezdata-1',
    secretKey: process.env.EZDATA_SECRET_KEY || 'erwqefdscweer)qi',
    allowOrigins: process.env.TRUSTRAG_ALLOW_ORIGINS?.split(',') || [
      'http://localhost:3600',
      'http://127.0.0.1:3600',
      'http://1118qg49520ma.vicp.fun'
    ]
  },
  
  // 代理配置
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
    },
    '/trustrag': {
      target: 'http://localhost:8217',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/trustrag/, ''),
    },
    '/nextchat': {
      target: 'http://localhost:3000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/nextchat/, ''),
    }
  },
  
  // 数据库配置
  database: {
    host: process.env.MONGO_HOST || 'localhost',
    port: process.env.MONGO_PORT || 27017,
    username: process.env.MONGO_USERNAME || 'admin',
    password: process.env.MONGO_PASSWORD || 'admin123',
    database: process.env.MONGO_DB || 'ezdata',
    authSource: process.env.MONGO_AUTH_SOURCE || 'admin'
  },
  
  // 模型路径配置
  models: {
    embedding: process.env.TRUSTRAG_EMBEDDING_MODEL || 'autodl-tmp/BAAI/bge-large-zh-v1.5',
    llm: process.env.TRUSTRAG_LLM_MODEL || '/home/dfi/Desktop/TrustRAG-main/autodl-tmp/Qwen/Qwen2.5-7B-Instruct',
    reranker: process.env.TRUSTRAG_RERANK_MODEL || 'autodl-tmp/BAAI2/bge-reranker-large'
  },
  
  // 索引配置
  index: {
    path: process.env.TRUSTRAG_INDEX_PATH || 'indexs/ezdata-1/dense_cache'
  }
};
