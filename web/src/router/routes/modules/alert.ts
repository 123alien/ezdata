import type { AppRouteModule } from '/@/router/types';
import { LAYOUT } from '/@/router/constant';

const alert: AppRouteModule = {
  path: '/alert',
  name: 'Alert',
  component: LAYOUT,
  redirect: '/alert/device-alert',
  meta: {
    orderNo: 6,
    icon: 'ion:warning-outline',
    title: '告警管理',
    hideChildrenInMenu: false,
  },
         children: [
           {
             path: 'device-alert',
             name: 'DeviceAlert',
             component: () => import('/@/views/alert/deviceAlert/index.vue'),
             meta: {
               title: '设备告警管理',
               icon: 'ion:hardware-chip-outline',
               hideMenu: false,
             },
           },
           {
             path: 'notification-config',
             name: 'NotificationConfig',
             component: () => import('/@/views/alert/notificationConfig/index.vue'),
             meta: {
               title: '通知配置',
               icon: 'ion:notifications-outline',
               hideMenu: false,
             },
           },
           {
             path: 'device-alert-test',
             name: 'DeviceAlertTest',
             component: () => import('/@/views/alert/deviceAlert/test.vue'),
             meta: {
               title: '设备告警测试',
               icon: 'ion:bug-outline',
               hideMenu: false,
             },
           },
           {
             path: 'alert-list',
             name: 'AlertList',
             component: () => import('/@/views/alert/index.vue'),
             meta: {
               title: '告警历史',
               icon: 'ion:list-outline',
               hideMenu: false,
             },
           },
           {
             path: 'alert-strategy',
             name: 'AlertStrategy',
             component: () => import('/@/views/alert/alert_strategy/index.vue'),
             meta: {
               title: '告警策略',
               icon: 'ion:settings-outline',
               hideMenu: false,
             },
           },
         ],
};

export default alert;
