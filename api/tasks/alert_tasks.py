'''
告警相关任务
'''
from celery_app import celery_app
from web_apps.alert.services.device_alert_service import DeviceAlertService


@celery_app.task(bind=True, name='self_check_device_alerts')
def self_check_device_alerts(self, **kwargs):
    '''
    检查设备告警任务
    '''
    try:
        print("开始执行设备告警检查任务...")
        service = DeviceAlertService()
        service.check_all_device_alerts()
        print("设备告警检查任务完成")
        return "设备告警检查完成"
    except Exception as e:
        print(f"设备告警检查任务失败: {e}")
        raise e
