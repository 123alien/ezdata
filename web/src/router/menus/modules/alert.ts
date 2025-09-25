import type { MenuModule } from '/@/router/types';

const alertMenu: MenuModule = {
  orderNo: 6,
  menu: {
    name: '告警管理',
    path: '/alert',
    icon: 'ion:warning-outline',
    children: [
      {
        name: '设备告警管理',
        path: '/alert/device-alert',
        icon: 'ion:hardware-chip-outline',
      },
      {
        name: '通知配置',
        path: '/alert/notification-config',
        icon: 'ion:notifications-outline',
      },
      {
        name: '告警历史',
        path: '/alert/alert-list',
        icon: 'ion:list-outline',
      },
      {
        name: '告警策略',
        path: '/alert/alert-strategy',
        icon: 'ion:settings-outline',
      },
    ],
  },
};

export default alertMenu;
