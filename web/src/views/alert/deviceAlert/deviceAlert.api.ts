import { defHttp } from '/@/utils/http/axios'

enum Api {
  alertStrategyList = '/alert_strategy/list',
  alertStrategyAllList = '/alert_strategy/queryAllList',
  alertStrategyDetail = '/alert_strategy/queryById',
  alertStrategyAdd = '/alert_strategy/add',
  alertStrategyEdit = '/alert_strategy/edit',
  alertStrategyDelete = '/alert_strategy/delete',
  alertStrategyDeleteBatch = '/alert_strategy/deleteBatch',
  alertList = '/alert/list',
  alertAllList = '/alert/queryAllList',
  alertDetail = '/alert/queryById',
  alertDelete = '/alert/delete',
  alertDeleteBatch = '/alert/deleteBatch',
  checkDeviceAlerts = '/alert/checkDeviceAlerts',
  createDefaultStrategies = '/alert/createDefaultStrategies',
  testNotification = '/alert/testNotification',
}

// 告警策略相关API
export const getAlertStrategyList = (params?) => defHttp.get({ url: Api.alertStrategyList, params })
export const getAlertStrategyAllList = (params?) => defHttp.get({ url: Api.alertStrategyAllList, params })
export const getAlertStrategyDetail = (params) => defHttp.get({ url: Api.alertStrategyDetail, params })
export const addAlertStrategy = (params) => defHttp.post({ url: Api.alertStrategyAdd, params })
export const editAlertStrategy = (params) => defHttp.post({ url: Api.alertStrategyEdit, params })
export const deleteAlertStrategy = (params) => defHttp.post({ url: Api.alertStrategyDelete, params })
export const deleteAlertStrategyBatch = (params) => defHttp.post({ url: Api.alertStrategyDeleteBatch, params })

// 告警相关API
export const getAlertList = (params?) => defHttp.get({ url: Api.alertList, params })
export const getAlertAllList = (params?) => defHttp.get({ url: Api.alertAllList, params })
export const getAlertDetail = (params) => defHttp.get({ url: Api.alertDetail, params })
export const deleteAlert = (params) => defHttp.post({ url: Api.alertDelete, params })
export const deleteAlertBatch = (params) => defHttp.post({ url: Api.alertDeleteBatch, params })

// 设备告警相关API
export const checkDeviceAlerts = () => defHttp.post({ url: Api.checkDeviceAlerts })
export const createDefaultStrategies = () => defHttp.post({ url: Api.createDefaultStrategies })
export const testNotification = (params) => defHttp.post({ url: Api.testNotification, params })

// 导入导出
export const getImportUrl = () => '/alert_strategy/importExcel'
export const getExportUrl = () => '/alert_strategy/exportXls'
