"""
LSTM 时间序列预测算法服务
用于电表等设备数据的预测
"""

import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# 延迟导入TensorFlow，避免在没有安装时立即报错
try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow未安装，LSTM预测功能不可用。请安装：pip install tensorflow")


class TimeSeriesPredictor:
    """时间序列预测器"""
    
    def __init__(self, time_steps=30):
        """
        初始化预测器
        
        参数:
            time_steps: 时间窗口大小（用过去N个时间点预测下一个）
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow未安装，无法使用LSTM预测功能")
        
        self.time_steps = time_steps
        self.scaler = MinMaxScaler()
        self.model = None
        self._is_trained = False
    
    def prepare_data(self, data: List[float], train_ratio=0.8) -> Tuple:
        """
        准备训练数据
        
        参数:
            data: 一维数组或列表，时间序列数据
            train_ratio: 训练集比例
            
        返回:
            X_train, X_test, y_train, y_test
        """
        if len(data) < self.time_steps + 10:
            raise ValueError(f"数据量不足（至少需要{self.time_steps + 10}个点），当前只有{len(data)}个点")
        
        # 转换为numpy数组
        data = np.array(data).reshape(-1, 1)
        
        # 归一化到[0,1]
        scaled_data = self.scaler.fit_transform(data)
        
        # 创建时间序列数据集
        X, y = [], []
        for i in range(len(scaled_data) - self.time_steps):
            X.append(scaled_data[i:i + self.time_steps])
            y.append(scaled_data[i + self.time_steps])
        
        X = np.array(X)
        y = np.array(y)
        
        # 划分训练集和测试集
        split_idx = int(len(X) * train_ratio)
        X_train = X[:split_idx]
        X_test = X[split_idx:]
        y_train = y[:split_idx]
        y_test = y[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def build_model(self, lstm_units_1=50, lstm_units_2=50, dense_units=25):
        """
        构建LSTM神经网络
        
        参数:
            lstm_units_1: 第一层LSTM单元数
            lstm_units_2: 第二层LSTM单元数
            dense_units: 全连接层单元数
        """
        self.model = Sequential([
            LSTM(lstm_units_1, return_sequences=True, input_shape=(self.time_steps, 1)),
            LSTM(lstm_units_2, return_sequences=False),
            Dense(dense_units, activation='relu'),
            Dense(1)
        ])
        
        self.model.compile(optimizer='adam', loss='mean_squared_error')
    
    def train(self, X_train, y_train, epochs=50, batch_size=32, 
              validation_split=0.2, patience=5, verbose=0):
        """
        训练模型
        
        参数:
            X_train: 训练数据
            y_train: 训练标签
            epochs: 训练轮数
            batch_size: 批次大小
            validation_split: 验证集比例
            patience: 早停耐心值
            verbose: 输出详细度 (0=静默, 1=进度条, 2=每轮一行)
            
        返回:
            训练历史
        """
        if self.model is None:
            self.build_model()
        
        # 早停机制
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=patience,
            restore_best_weights=True,
            verbose=verbose
        )
        
        # 训练
        history = self.model.fit(
            X_train, y_train,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=verbose
        )
        
        self._is_trained = True
        return history
    
    def predict(self, X):
        """
        预测
        
        参数:
            X: 输入数据
            
        返回:
            预测结果（已反归一化）
        """
        if not self._is_trained or self.model is None:
            raise ValueError("模型未训练，请先调用 train() 方法")
        
        # 预测
        predictions_scaled = self.model.predict(X, verbose=0)
        
        # 反归一化
        predictions = self.scaler.inverse_transform(predictions_scaled)
        
        return predictions.flatten()
    
    def predict_next_n(self, recent_data: List[float], n: int = 36) -> List[float]:
        """
        预测未来N个值（多步预测）
        
        参数:
            recent_data: 最近N个数据点（N = time_steps）
            n: 要预测的未来点数
            
        返回:
            未来N个时间点的预测值列表
        """
        if len(recent_data) < self.time_steps:
            raise ValueError(f"需要至少 {self.time_steps} 个数据点，但提供了 {len(recent_data)} 个")
        
        if not self._is_trained or self.model is None:
            raise ValueError("模型未训练，请先调用 train() 方法")
        
        predictions = []
        # 使用最后time_steps个点作为起始窗口
        window = list(recent_data[-self.time_steps:])
        
        for _ in range(n):
            # 归一化窗口数据
            window_array = np.array(window[-self.time_steps:]).reshape(-1, 1)
            scaled_window = self.scaler.transform(window_array)
            
            # 预测下一个值
            X = scaled_window.reshape(1, self.time_steps, 1)
            prediction_scaled = self.model.predict(X, verbose=0)
            
            # 反归一化
            prediction = self.scaler.inverse_transform(prediction_scaled)[0][0]
            predictions.append(float(prediction))
            
            # 将预测值加入窗口用于下一步预测
            window.append(prediction)
        
        return predictions
    
    def predict_next(self, recent_data: List[float]) -> float:
        """
        预测下一个值（实时预测）
        
        参数:
            recent_data: 最近N个数据点（N = time_steps）
            
        返回:
            下一个时间点的预测值
        """
        predictions = self.predict_next_n(recent_data, n=1)
        return predictions[0] if predictions else None
    
    def save(self, filepath: str):
        """保存模型"""
        if self.model is None or not self._is_trained:
            raise ValueError("模型未训练")
        self.model.save(filepath)
        logger.info(f"模型已保存到: {filepath}")
    
    def load(self, filepath: str):
        """加载模型"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"模型文件不存在: {filepath}")
        self.model = load_model(filepath)
        self._is_trained = True
        logger.info(f"模型已从 {filepath} 加载")


class DevicePredictionService:
    """设备预测服务（封装LSTM预测器）"""
    
    def __init__(self):
        """初始化服务"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow未安装，预测服务将使用简单算法")
    
    def predict_device_metric(
        self, 
        data_points: List[Dict], 
        metric_name: str = 'power',
        prediction_steps: int = 36,
        time_steps: int = 30,
        train_ratio: float = 0.8,
        epochs: int = 30
    ) -> Dict:
        """
        对设备指标进行LSTM预测
        
        参数:
            data_points: 数据点列表，格式为 [{'t': timestamp, 'v': value}, ...]
            metric_name: 指标名称
            prediction_steps: 预测未来多少个点
            time_steps: LSTM时间窗口大小
            train_ratio: 训练集比例
            epochs: 训练轮数
            
        返回:
            {
                'success': True/False,
                'metric': metric_name,
                'predictions': [value1, value2, ...],
                'trend': float,
                'confidence': float,
                'method': 'lstm' or 'simple'
            }
        """
        try:
            # 提取数值序列
            values = []
            for point in data_points:
                if isinstance(point, dict) and 'v' in point:
                    v = point.get('v')
                    if v is not None:
                        values.append(float(v))
            
            if len(values) < time_steps + 10:
                # 数据不足，使用简单算法
                return self._simple_predict(values, metric_name, prediction_steps)
            
            # 使用LSTM预测
            if not TENSORFLOW_AVAILABLE:
                return self._simple_predict(values, metric_name, prediction_steps)
            
            predictor = TimeSeriesPredictor(time_steps=time_steps)
            
            # 准备数据
            X_train, X_test, y_train, y_test = predictor.prepare_data(values, train_ratio=train_ratio)
            
            # 构建并训练模型
            predictor.build_model()
            predictor.train(X_train, y_train, epochs=epochs, verbose=0)
            
            # 生成预测
            recent_data = values[-time_steps:]
            predictions = predictor.predict_next_n(recent_data, n=prediction_steps)
            
            # 计算趋势和置信度
            trend = (values[-1] - values[0]) / len(values) if len(values) > 1 else 0
            confidence = min(0.9, max(0.3, 1 - abs(trend) / (abs(values[-1]) + 1e-6)))
            
            return {
                'success': True,
                'metric': metric_name,
                'predictions': predictions,
                'trend': float(trend),
                'confidence': float(confidence),
                'method': 'lstm'
            }
            
        except Exception as e:
            logger.error(f"LSTM预测失败: {e}", exc_info=True)
            # 降级到简单算法
            try:
                values = [float(p.get('v', 0)) for p in data_points if p.get('v') is not None]
                return self._simple_predict(values, metric_name, prediction_steps)
            except Exception as e2:
                logger.error(f"简单预测也失败: {e2}", exc_info=True)
                return {
                    'success': False,
                    'metric': metric_name,
                    'predictions': [],
                    'error': str(e2),
                    'method': 'none'
                }
    
    def _simple_predict(self, values: List[float], metric_name: str, n: int = 36) -> Dict:
        """简单预测算法（降级方案）"""
        if len(values) < 5:
            return {
                'success': False,
                'metric': metric_name,
                'predictions': [],
                'error': '数据不足',
                'method': 'simple'
            }
        
        # 简单线性趋势
        recent = values[-20:] if len(values) >= 20 else values
        trend = (recent[-1] - recent[0]) / len(recent) if len(recent) > 1 else 0
        last_value = values[-1]
        
        # PM2.5、PM10使用更剧烈的波动，CO2适度波动
        is_pm_metric = metric_name in ['PM25', 'PM10', 'PM2.5'] or \
                       metric_name.upper() in ['PM25', 'PM10', 'PM2.5']
        is_co2_metric = metric_name in ['CO2'] or metric_name.upper() == 'CO2'
        
        predictions = []
        for i in range(1, n + 1):
            predicted = last_value + (trend * i * 0.1)
            # 根据指标类型调整波动幅度
            if is_pm_metric:
                # PM2.5、PM10：使用更剧烈的波动（增加波动幅度）
                variation = np.sin(i / n * np.pi * 3) * abs(last_value) * 0.25 + \
                           np.sin(i / n * np.pi * 5) * abs(last_value) * 0.15 + \
                           (np.random.random() - 0.5) * abs(last_value) * 0.2
            elif is_co2_metric:
                # CO2：适度波动（比原来稍高，但不过于剧烈）
                variation = np.sin(i / n * np.pi * 3) * abs(last_value) * 0.12 + \
                           (np.random.random() - 0.5) * abs(last_value) * 0.06
            else:
                # 其他指标：原有波动幅度
                variation = np.sin(i / n * np.pi * 3) * abs(last_value) * 0.1
            predicted += variation
            predicted = max(0, predicted)  # 不能为负
            predictions.append(float(predicted))
        
        confidence = min(0.9, max(0.3, 1 - abs(trend) / (abs(last_value) + 1e-6)))
        
        return {
            'success': True,
            'metric': metric_name,
            'predictions': predictions,
            'trend': float(trend),
            'confidence': float(confidence),
            'method': 'simple'
        }

