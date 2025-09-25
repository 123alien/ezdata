"""
告警通知服务
支持平台通知、短信预警、邮件通知、微信通知等多种方式
"""
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from web_apps import db
from web_apps.alert.db_models import Alert
from models import Notice
from utils.common_utils import gen_uuid
import logging
logger = logging.getLogger(__name__)


class NotificationService:
    """告警通知服务"""
    
    def __init__(self):
        self.sms_config = {
            'api_url': 'https://api.sms.com/send',  # 短信服务商API
            'api_key': 'your_sms_api_key',
            'signature': '数字金融实验室'
        }
        
        self.email_config = {
            'smtp_server': 'smtp.qq.com',
            'smtp_port': 587,
            'username': 'your_email@qq.com',
            'password': 'your_email_password'
        }
        
        self.wechat_config = {
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
            'key': 'your_wechat_webhook_key'
        }

    def send_alert_notification(self, alert: Alert, notification_methods: list, receivers: list):
        """
        发送告警通知
        :param alert: 告警对象
        :param notification_methods: 通知方式列表
        :param receivers: 接收人员列表
        """
        try:
            # 检查是否在静默期内
            if self._is_in_silence_period(alert):
                logger.info(f"告警 {alert.id} 在静默期内，跳过通知")
                return

            # 构建通知内容
            notification_content = self._build_notification_content(alert)
            
            # 发送各种通知
            for method in notification_methods:
                if method == 'platform':
                    self._send_platform_notification(alert, notification_content, receivers)
                elif method == 'sms':
                    self._send_sms_notification(alert, notification_content, receivers)
                elif method == 'email':
                    self._send_email_notification(alert, notification_content, receivers)
                elif method == 'wechat':
                    self._send_wechat_notification(alert, notification_content, receivers)
                    
            logger.info(f"告警通知发送完成: {alert.id}")
            
        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")

    def _is_in_silence_period(self, alert: Alert) -> bool:
        """检查是否在静默期内"""
        try:
            # 从策略配置中获取静默时间
            strategy = alert.strategy
            if not strategy or not strategy.forward_conf:
                return False
                
            forward_conf = json.loads(strategy.forward_conf)
            silence_hours = forward_conf.get('silence_hours', 0)
            
            if silence_hours <= 0:
                return False
                
            # 检查最近是否有相同设备的告警
            silence_start = datetime.now() - timedelta(hours=silence_hours)
            recent_alerts = db.session.query(Alert).filter(
                Alert.source == alert.source,
                Alert.metric == alert.metric,
                Alert.create_time >= silence_start,
                Alert.id != alert.id
            ).count()
            
            return recent_alerts > 0
            
        except Exception as e:
            logger.error(f"检查静默期失败: {e}")
            return False

    def _build_notification_content(self, alert: Alert) -> dict:
        """构建通知内容"""
        return {
            'title': alert.title,
            'content': alert.content,
            'level': self._get_level_text(alert.level),
            'source': alert.source,
            'metric': alert.metric,
            'time': alert.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'url': f"http://localhost:5179/alert/alert-list?id={alert.id}"
        }

    def _get_level_text(self, level: int) -> str:
        """获取告警等级文本"""
        level_map = {0: '低', 1: '中', 2: '高', 3: '紧急'}
        return level_map.get(level, '未知')

    def _send_platform_notification(self, alert: Alert, content: dict, receivers: list):
        """发送平台通知"""
        try:
            for receiver in receivers:
                # 使用时间戳作为ID，确保唯一性
                notice_id = int(datetime.now().timestamp() * 1000) % 2147483647  # MySQL INT 最大值
                notice = Notice(
                    id=notice_id,
                    title=f"【{content['level']}级告警】{content['title']}",
                    msg_content=content['content'],
                    msg_category='2',  # 系统消息
                    msg_type='USER',  # 指定用户
                    user_ids=f'["{receiver}"]',
                    send_status='1',  # 已发布
                    send_time=int(datetime.now().timestamp()),
                    create_by='system'
                )
                db.session.add(notice)
            
            db.session.commit()
            logger.info(f"平台通知发送成功: {alert.id}")
            
        except Exception as e:
            logger.error(f"发送平台通知失败: {e}")

    def _send_sms_notification(self, alert: Alert, content: dict, receivers: list):
        """发送短信通知"""
        try:
            # 构建短信内容
            sms_content = f"【{content['level']}级告警】{content['title']}\n{content['content']}\n时间：{content['time']}"
            
            # 获取接收人员手机号（这里需要根据实际用户表结构调整）
            phone_numbers = self._get_receiver_phones(receivers)
            
            for phone in phone_numbers:
                self._send_sms(phone, sms_content)
                
            logger.info(f"短信通知发送成功: {alert.id}")
            
        except Exception as e:
            logger.error(f"发送短信通知失败: {e}")

    def _send_sms(self, phone: str, content: str):
        """发送单条短信"""
        try:
            data = {
                'phone': phone,
                'content': content,
                'signature': self.sms_config['signature']
            }
            
            headers = {
                'Authorization': f"Bearer {self.sms_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.sms_config['api_url'],
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"短信发送成功: {phone}")
            else:
                logger.error(f"短信发送失败: {phone}, {response.text}")
                
        except Exception as e:
            logger.error(f"发送短信异常: {e}")

    def _send_email_notification(self, alert: Alert, content: dict, receivers: list):
        """发送邮件通知"""
        try:
            # 构建邮件内容
            email_subject = f"【{content['level']}级告警】{content['title']}"
            email_body = f"""
            <html>
            <body>
                <h2>设备告警通知</h2>
                <p><strong>告警等级：</strong>{content['level']}</p>
                <p><strong>告警对象：</strong>{content['source']}</p>
                <p><strong>告警指标：</strong>{content['metric']}</p>
                <p><strong>告警内容：</strong>{content['content']}</p>
                <p><strong>告警时间：</strong>{content['time']}</p>
                <p><strong>查看详情：</strong><a href="{content['url']}">点击查看</a></p>
            </body>
            </html>
            """
            
            # 获取接收人员邮箱
            email_addresses = self._get_receiver_emails(receivers)
            
            for email in email_addresses:
                self._send_email(email, email_subject, email_body)
                
            logger.info(f"邮件通知发送成功: {alert.id}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")

    def _send_email(self, to_email: str, subject: str, body: str):
        """发送单封邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['username'], to_email, text)
            server.quit()
            
            logger.info(f"邮件发送成功: {to_email}")
            
        except Exception as e:
            logger.error(f"发送邮件异常: {e}")

    def _send_wechat_notification(self, alert: Alert, content: dict, receivers: list):
        """发送微信通知"""
        try:
            # 构建微信消息
            wechat_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"""## 设备告警通知
                    
**告警等级：** {content['level']}
**告警对象：** {content['source']}
**告警指标：** {content['metric']}
**告警内容：** {content['content']}
**告警时间：** {content['time']}
**查看详情：** [点击查看]({content['url']})"""
                }
            }
            
            response = requests.post(
                f"{self.wechat_config['webhook_url']}?key={self.wechat_config['key']}",
                json=wechat_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"微信通知发送成功: {alert.id}")
            else:
                logger.error(f"微信通知发送失败: {response.text}")
                
        except Exception as e:
            logger.error(f"发送微信通知异常: {e}")

    def _get_receiver_phones(self, receivers: list) -> list:
        """获取接收人员手机号"""
        # 这里需要根据实际用户表结构查询手机号
        # 暂时返回示例数据
        phone_map = {
            'admin': '13800138000',
            'operator': '13800138001',
            'device_manager': '13800138002',
            'security_manager': '13800138003'
        }
        return [phone_map.get(receiver, '13800138000') for receiver in receivers]

    def _get_receiver_emails(self, receivers: list) -> list:
        """获取接收人员邮箱"""
        # 这里需要根据实际用户表结构查询邮箱
        # 暂时返回示例数据
        email_map = {
            'admin': 'admin@example.com',
            'operator': 'operator@example.com',
            'device_manager': 'device@example.com',
            'security_manager': 'security@example.com'
        }
        return [email_map.get(receiver, 'admin@example.com') for receiver in receivers]

    def test_notification(self, method: str, receiver: str):
        """测试通知功能"""
        try:
            test_alert = Alert(
                id=gen_uuid(),
                title="测试告警",
                content="这是一个测试告警，用于验证通知功能",
                level=1,
                source="测试设备",
                metric="test",
                create_time=datetime.now()
            )
            
            content = self._build_notification_content(test_alert)
            
            if method == 'platform':
                self._send_platform_notification(test_alert, content, [receiver])
            elif method == 'sms':
                self._send_sms_notification(test_alert, content, [receiver])
            elif method == 'email':
                self._send_email_notification(test_alert, content, [receiver])
            elif method == 'wechat':
                self._send_wechat_notification(test_alert, content, [receiver])
                
            return True
            
        except Exception as e:
            logger.error(f"测试通知失败: {e}")
            return False
