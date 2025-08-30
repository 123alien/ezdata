import type { AppRouteModule } from '/@/router/types';
import { LAYOUT } from '/@/router/constant';

const rag: AppRouteModule = {
  path: '/rag',
  name: 'RAG',
  component: LAYOUT,
  redirect: '/rag/external',
  meta: {
    orderNo: 10,
    icon: 'ion:library-outline',
    title: 'RAG 知识库',
    hideChildrenInMenu: false,
  },
  children: [
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
    {
      path: 'test',
      name: 'RAGTest',
      component: () => import('/@/views/rag/external/test.vue'),
      meta: {
        title: '测试路由',
        icon: 'ion:bug-outline',
        hideMenu: false,
      },
    },
  ],
};

export default rag;
