import type { AppRouteModule } from '/@/router/types';

import { LAYOUT } from '/@/router/constant';

const rag: AppRouteModule = {
  path: '/rag',
  name: 'RAG',
  component: LAYOUT,
  redirect: '/rag/document',
  meta: {
    orderNo: 10,
    icon: 'ion:library-outline',
    title: 'RAG 知识库',
  },
  children: [
    {
      path: 'document',
      name: 'RAGDocument',
      component: () => import('/@/views/rag/document/index.vue'),
      meta: {
        title: '文档管理',
        icon: 'ion:document-outline',
      },
    },
    {
      path: 'dataset',
      name: 'RAGDataset',
      component: () => import('/@/views/rag/dataset/index.vue'),
      meta: {
        title: '数据集管理',
        icon: 'ion:folder-outline',
      },
    },
    {
      path: 'chunk',
      name: 'RAGChunk',
      component: () => import('/@/views/rag/chunk/index.vue'),
      meta: {
        title: '分块管理',
        icon: 'ion:grid-outline',
      },
    },
    {
      path: 'external',
      name: 'RAGExternal',
      component: () => import('/@/views/rag/external/index.vue'),
      meta: {
        title: 'TrustRAG 外部服务',
        icon: 'ion:cloud-outline',
        hideMenu: false,
      },
    },
  ],
};

export default rag;
