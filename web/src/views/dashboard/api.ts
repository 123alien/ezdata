import { defHttp } from '/@/utils/http/axios';

enum Api {
  datamodelOverview = '/datamodel/dashboard/overview',
  datamodelTypeStats = '/datamodel/dashboard/type-stats',
  datamodelTrend = '/datamodel/dashboard/trend',
  datamodelDataflow = '/datamodel/dashboard/dataflow',
  datamodelFieldStats = '/datamodel/dashboard/field-stats',
  iotDevices = '/datamodel/dashboard/iot-devices',
  deviceStats = '/datamodel/dashboard/device-stats',
  powerMeterStats = '/datamodel/dashboard/power-meter-stats',
  deviceMetrics = '/datamodel/dashboard/device-metrics',
  dailyPowerTrend = '/datamodel/dashboard/daily-power-trend',
  devicePrediction = '/datamodel/dashboard/device-prediction',
}

/**
 * 获取数据模型总览数据
 */
export const getDataModelOverview = (params?) => defHttp.get({ url: Api.datamodelOverview, params });

/**
 * 获取数据模型类型统计
 */
export const getDataModelTypeStats = (params?) => defHttp.get({ url: Api.datamodelTypeStats, params });

/**
 * 获取数据模型创建趋势
 */
export const getDataModelCreationTrend = (params?) => defHttp.get({ url: Api.datamodelTrend, params });

/**
 * 获取数据流向（桑基图）
 */
export const getDataModelDataflow = (params?) => defHttp.get({ url: Api.datamodelDataflow, params });

/**
 * 获取数据模型字段统计
 */
export const getDataModelFieldStats = (params?) => defHttp.get({ url: Api.datamodelFieldStats, params });

/**
 * 获取物联网设备数据
 */
export const getIotDevices = (params?) => defHttp.get({ url: Api.iotDevices, params });

/**
 * 获取设备统计信息
 */
export const getDeviceStats = (params?) => defHttp.get({ url: Api.deviceStats, params });

/**
 * 获取电表设备统计信息
 */
export const getPowerMeterStats = (params?) => defHttp.get({ url: Api.powerMeterStats, params });

/**
 * 获取设备多指标时序
 */
export const getDeviceMetrics = (params?) => defHttp.get({ url: Api.deviceMetrics, params });

/**
 * 获取日用电量趋势数据
 */
export const getDailyPowerTrend = (params?) => defHttp.get({ url: Api.dailyPowerTrend, params });

/**
 * 设备指标LSTM预测
 */
export const predictDeviceMetrics = (params?) => defHttp.post({ url: Api.devicePrediction, params });
