import type { AppRouteModule } from '/@/router/types';
import { LAYOUT } from '/@/router/constant';

const dataCenter: AppRouteModule = {
  path: '/data-center',
  name: 'DataCenter',
  component: LAYOUT,
  redirect: '/data-center/environment-monitoring',
  meta: {
    orderNo: 5,
    icon: 'ion:server-outline',
    title: '数据中心',
    hideChildrenInMenu: false,
  },
  children: [
    {
      path: 'environment-monitoring',
      name: 'EnvironmentMonitoring',
      component: () => import('/@/views/dataCenter/EnvironmentMonitoring/index.vue'),
      meta: {
        title: '环境监测设备',
        icon: 'ion:thermometer-outline',
        hideMenu: false,
      },
    },
    {
      path: 'power-meter',
      name: 'PowerMeter',
      component: () => import('/@/views/dataCenter/PowerMeter/index.vue'),
      meta: {
        title: '电表设备',
        icon: 'ion:flash-outline',
        hideMenu: false,
      },
    },
  ],
};

export default dataCenter;
