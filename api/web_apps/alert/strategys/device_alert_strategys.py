'''
设备告警策略处理
'''
import json
from web_apps.alert.services.device_alert_service import DeviceAlertService


def handle_device_alert_check():
    '''
    处理设备告警检查
    '''
    try:
        print("开始执行设备告警检查...")
        service = DeviceAlertService()
        service.check_all_device_alerts()
        print("设备告警检查完成")
    except Exception as e:
        print(f"设备告警检查失败: {e}")


def create_default_alert_strategies():
    '''
    创建默认的告警策略
    '''
    from web_apps.alert.db_models import AlertStrategy
    from web_apps import db
    from utils.common_utils import gen_uuid
    
    try:
        # 电表告警策略
        power_strategy = AlertStrategy(
            id=gen_uuid(),
            name='电表功率告警',
            template_code='power_meter_alert',
            trigger_conf=json.dumps({
                'power_threshold': 1000,  # 功率阈值 1000W
                'daily_threshold': 50,    # 日用电量阈值 50kWh
                'level': 2
            }),
            forward_conf=json.dumps({
                'notification_methods': ['platform', 'sms', 'email'],
                'receivers': ['admin', 'operator'],
                'alert_frequency': 'immediate',
                'silence_hours': 2
            }),
            status=1,
            description='电表设备功率和用电量告警策略，支持平台通知、短信和邮件预警'
        )
        
        # 环境监测告警策略
        env_strategy = AlertStrategy(
            id=gen_uuid(),
            name='环境监测告警',
            template_code='environment_alert',
            trigger_conf=json.dumps({
                'temperature_threshold': {
                    'min': 15,
                    'max': 30
                },
                'humidity_threshold': {
                    'min': 30,
                    'max': 80
                },
                'pm25_threshold': {
                    'max': 75  # PM2.5超过75μg/m³告警
                },
                'pm10_threshold': {
                    'max': 150  # PM10超过150μg/m³告警
                },
                'co2_threshold': {
                    'max': 1000  # CO2超过1000ppm告警
                },
                'level': 1
            }),
            forward_conf=json.dumps({
                'notification_methods': ['platform', 'sms', 'wechat'],
                'receivers': ['admin', 'device_manager', 'security_manager'],
                'alert_frequency': '15min',
                'silence_hours': 1
            }),
            status=1,
            description='环境监测设备各项指标告警策略，支持平台通知、短信和微信预警'
        )
        
        # 检查是否已存在
        existing_power = db.session.query(AlertStrategy).filter(
            AlertStrategy.template_code == 'power_meter_alert'
        ).first()
        
        existing_env = db.session.query(AlertStrategy).filter(
            AlertStrategy.template_code == 'environment_alert'
        ).first()
        
        if not existing_power:
            db.session.add(power_strategy)
            print("创建电表告警策略")
        
        if not existing_env:
            db.session.add(env_strategy)
            print("创建环境监测告警策略")
        
        db.session.commit()
        print("默认告警策略创建完成")
        
    except Exception as e:
        print(f"创建默认告警策略失败: {e}")


if __name__ == '__main__':
    # 创建默认策略
    create_default_alert_strategies()
    
    # 执行告警检查
    handle_device_alert_check()
