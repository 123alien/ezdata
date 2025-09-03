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
      path: 'knowledge-base',
      name: 'KnowledgeBase',
      component: () => import('/@/views/rag/knowledge-base/index.vue'),
      meta: {
        title: '知识库管理',
        icon: 'ion:library',
        hideMenu: false,
      },
      children: [
        {
          path: 'my',
          name: 'MyKnowledgeBase',
          component: () => import('/@/views/rag/knowledge-base/my/index.vue'),
          meta: {
            title: '我的知识库',
            icon: 'ion:folder',
            hideMenu: false,
          },
        },
        {
          path: 'share',
          name: 'ShareKnowledgeBase',
          component: () => import('/@/views/rag/knowledge-base/share/index.vue'),
          meta: {
            title: '知识库分享',
            icon: 'ion:share',
            hideMenu: false,
          },
        },
        {
          path: 'shared',
          name: 'SharedKnowledgeBase',
          component: () => import('/@/views/rag/knowledge-base/shared/index.vue'),
          meta: {
            title: '共享给我的',
          },
        },
      ],
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
