'''
设备阈值告警服务
'''
import json
from datetime import datetime, timezone, timedelta
from web_apps.alert.db_models import AlertStrategy, Alert
from web_apps import db
from utils.common_utils import gen_uuid, md5, parse_json
from web_apps.alert.services.alert_forward_service import handle_alert_forward
from web_apps.alert.services.notification_service import NotificationService
from web_apps.datamodel.services.datamodel_api_services import DataModelApiService


class DeviceAlertService:
    '''
    设备阈值告警服务
    '''
    
    def __init__(self):
        self.datamodel_service = DataModelApiService()
        self.notification_service = NotificationService()
    
    def check_power_meter_alerts(self):
        '''
        检查电表设备告警
        '''
        try:
            # 获取电表统计数据
            power_stats = self.datamodel_service.get_power_meter_statistics()
            
            # 获取电表告警策略
            power_alert_strategies = db.session.query(AlertStrategy).filter(
                AlertStrategy.del_flag == 0,
                AlertStrategy.status == 1,
                AlertStrategy.template_code == 'power_meter_alert'
            ).all()
            
            for strategy in power_alert_strategies:
                trigger_conf = parse_json(strategy.trigger_conf)
                forward_conf = parse_json(strategy.forward_conf)
                
                # 检查每个电表设备
                for device in power_stats.get('devices', []):
                    device_name = device.get('name', '')
                    current_power = device.get('current_power', 0)
                    today_power = device.get('today_power', 0)
                    
                    # 检查功率阈值
                    power_threshold = trigger_conf.get('power_threshold', 0)
                    if current_power > power_threshold:
                        self._create_power_alert(
                            strategy, device_name, current_power, 
                            power_threshold, 'current_power', forward_conf
                        )
                    
                    # 检查日用电量阈值
                    daily_threshold = trigger_conf.get('daily_threshold', 0)
                    if today_power > daily_threshold:
                        self._create_power_alert(
                            strategy, device_name, today_power, 
                            daily_threshold, 'daily_power', forward_conf
                        )
                        
        except Exception as e:
            print(f"检查电表告警失败: {e}")
    
    def check_environment_alerts(self):
        '''
        检查环境监测设备告警
        '''
        try:
            # 获取环境监测设备数据
            env_stats = self.datamodel_service.get_device_statistics()
            
            # 获取环境监测告警策略
            env_alert_strategies = db.session.query(AlertStrategy).filter(
                AlertStrategy.del_flag == 0,
                AlertStrategy.status == 1,
                AlertStrategy.template_code == 'environment_alert'
            ).all()
            
            for strategy in env_alert_strategies:
                trigger_conf = parse_json(strategy.trigger_conf)
                forward_conf = parse_json(strategy.forward_conf)
                
                # 检查每个环境监测设备
                for device in env_stats.get('devices', []):
                    device_name = device.get('name', '')
                    metrics = device.get('metrics', {})
                    
                    # 检查温度阈值
                    temp_threshold = trigger_conf.get('temperature_threshold', {})
                    if 'temperature' in metrics:
                        temp_value = metrics['temperature']
                        if self._check_threshold(temp_value, temp_threshold):
                            self._create_environment_alert(
                                strategy, device_name, 'temperature', 
                                temp_value, temp_threshold, forward_conf
                            )
                    
                    # 检查湿度阈值
                    humidity_threshold = trigger_conf.get('humidity_threshold', {})
                    if 'humidity' in metrics:
                        humidity_value = metrics['humidity']
                        if self._check_threshold(humidity_value, humidity_threshold):
                            self._create_environment_alert(
                                strategy, device_name, 'humidity', 
                                humidity_value, humidity_threshold, forward_conf
                            )
                    
                    # 检查PM2.5阈值
                    pm25_threshold = trigger_conf.get('pm25_threshold', {})
                    if 'PM2.5' in metrics:
                        pm25_value = metrics['PM2.5']
                        if self._check_threshold(pm25_value, pm25_threshold):
                            self._create_environment_alert(
                                strategy, device_name, 'PM2.5', 
                                pm25_value, pm25_threshold, forward_conf
                            )
                    
                    # 检查PM10阈值
                    pm10_threshold = trigger_conf.get('pm10_threshold', {})
                    if 'PM10' in metrics:
                        pm10_value = metrics['PM10']
                        if self._check_threshold(pm10_value, pm10_threshold):
                            self._create_environment_alert(
                                strategy, device_name, 'PM10', 
                                pm10_value, pm10_threshold, forward_conf
                            )
                    
                    # 检查CO2阈值
                    co2_threshold = trigger_conf.get('co2_threshold', {})
                    if 'CO2' in metrics:
                        co2_value = metrics['CO2']
                        if self._check_threshold(co2_value, co2_threshold):
                            self._create_environment_alert(
                                strategy, device_name, 'CO2', 
                                co2_value, co2_threshold, forward_conf
                            )
                        
        except Exception as e:
            print(f"检查环境监测告警失败: {e}")
    
    def _check_threshold(self, value, threshold_config):
        '''
        检查阈值条件
        '''
        if not threshold_config:
            return False
        
        min_val = threshold_config.get('min', None)
        max_val = threshold_config.get('max', None)
        
        if min_val is not None and value < min_val:
            return True
        if max_val is not None and value > max_val:
            return True
        
        return False
    
    def _create_power_alert(self, strategy, device_name, current_value, threshold, metric_type, forward_conf):
        '''
        创建电表告警
        '''
        try:
            # 检查是否已存在相同告警
            existing_alert = db.session.query(Alert).filter(
                Alert.strategy_id == strategy.id,
                Alert.source == device_name,
                Alert.metric == metric_type,
                Alert.status == 0  # 未处理状态
            ).first()
            
            if existing_alert:
                return  # 已存在相同告警，不重复创建
            
            alert_content = f"电表设备 {device_name} {metric_type} 超过阈值：当前值 {current_value}，阈值 {threshold}"
            
            alert_obj = Alert(
                id=gen_uuid(),
                strategy_id=strategy.id,
                title=f"电表{metric_type}告警",
                content=alert_content,
                level=strategy.trigger_conf.get('level', 1),
                status=0,
                rule_id=md5(strategy.id + device_name + metric_type),
                rule_name=strategy.name,
                biz='power_meter',
                source=device_name,
                tags=json.dumps({
                    'device_type': 'power_meter',
                    'metric_type': metric_type,
                    'current_value': current_value,
                    'threshold': threshold
                }),
                metric=metric_type,
                create_by='system'
            )
            
            db.session.add(alert_obj)
            db.session.commit()
            db.session.flush()
            
            # 处理告警转发
            if forward_conf:
                handle_alert_forward(alert_obj, forward_conf)
            
            # 发送通知
            self._send_alert_notification(alert_obj, strategy)
                
        except Exception as e:
            print(f"创建电表告警失败: {e}")
    
    def _create_environment_alert(self, strategy, device_name, metric_name, current_value, threshold_config, forward_conf):
        '''
        创建环境监测告警
        '''
        try:
            # 检查是否已存在相同告警
            existing_alert = db.session.query(Alert).filter(
                Alert.strategy_id == strategy.id,
                Alert.source == device_name,
                Alert.metric == metric_name,
                Alert.status == 0  # 未处理状态
            ).first()
            
            if existing_alert:
                return  # 已存在相同告警，不重复创建
            
            # 构建告警内容
            threshold_desc = ""
            if threshold_config.get('min') is not None:
                threshold_desc += f"最小值: {threshold_config['min']}"
            if threshold_config.get('max') is not None:
                if threshold_desc:
                    threshold_desc += ", "
                threshold_desc += f"最大值: {threshold_config['max']}"
            
            alert_content = f"环境监测设备 {device_name} {metric_name} 超出阈值：当前值 {current_value}，阈值范围 {threshold_desc}"
            
            alert_obj = Alert(
                id=gen_uuid(),
                strategy_id=strategy.id,
                title=f"环境监测{metric_name}告警",
                content=alert_content,
                level=strategy.trigger_conf.get('level', 1),
                status=0,
                rule_id=md5(strategy.id + device_name + metric_name),
                rule_name=strategy.name,
                biz='environment_monitoring',
                source=device_name,
                tags=json.dumps({
                    'device_type': 'environment_monitoring',
                    'metric_name': metric_name,
                    'current_value': current_value,
                    'threshold_config': threshold_config
                }),
                metric=metric_name,
                create_by='system'
            )
            
            db.session.add(alert_obj)
            db.session.commit()
            db.session.flush()
            
            # 处理告警转发
            if forward_conf:
                handle_alert_forward(alert_obj, forward_conf)
            
            # 发送通知
            self._send_alert_notification(alert_obj, strategy)
                
        except Exception as e:
            print(f"创建环境监测告警失败: {e}")
    
    def _send_alert_notification(self, alert_obj, strategy):
        '''
        发送告警通知
        '''
        try:
            # 解析策略配置
            forward_conf = parse_json(strategy.forward_conf) if strategy.forward_conf else {}
            
            # 获取通知方式
            notification_methods = forward_conf.get('notification_methods', ['platform'])
            receivers = forward_conf.get('receivers', ['admin'])
            
            # 发送通知
            self.notification_service.send_alert_notification(
                alert_obj, notification_methods, receivers
            )
            
        except Exception as e:
            print(f"发送告警通知失败: {e}")

    def check_all_device_alerts(self):
        '''
        检查所有设备告警
        '''
        print("开始检查设备告警...")
        self.check_power_meter_alerts()
        self.check_environment_alerts()
        print("设备告警检查完成")


if __name__ == '__main__':
    # 测试告警服务
    service = DeviceAlertService()
    service.check_all_device_alerts()
