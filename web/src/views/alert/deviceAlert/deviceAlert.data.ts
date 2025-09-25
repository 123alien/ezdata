import { BasicColumn, FormSchema } from '/@/components/Table'
import { render } from "/@/utils/common/renderUtils"

// 告警历史表格列配置
export const columns: BasicColumn[] = [
  {
    title: '告警标题',
    align: 'center',
    dataIndex: 'title',
    width: 200,
  },
  {
    title: '告警内容',
    align: 'center',
    dataIndex: 'content',
    width: 300,
  },
  {
    title: '告警等级',
    align: 'center',
    dataIndex: 'level',
    customRender: ({ text }) => {
      const levelMap = { 0: '低', 1: '中', 2: '高', 3: '紧急' }
      return levelMap[text] || text
    },
  },
  {
    title: '告警状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      const statusMap = { 0: '未处理', 1: '已处理', 2: '已恢复' }
      return statusMap[text] || text
    },
  },
  {
    title: '告警对象',
    align: 'center',
    dataIndex: 'source',
    width: 150,
  },
  {
    title: '告警指标',
    align: 'center',
    dataIndex: 'metric',
    width: 120,
  },
  {
    title: '创建时间',
    align: 'center',
    dataIndex: 'create_time',
    width: 180,
  },
  {
    title: '恢复时间',
    align: 'center',
    dataIndex: 'recover_time',
    width: 180,
  },
]

// 搜索表单配置
export const searchFormSchema: FormSchema[] = [
  {
    field: 'title',
    label: '告警标题',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    field: 'level',
    label: '告警等级',
    component: 'Select',
    componentProps: {
      placeholder: '请选择告警等级',
      options: [
        { label: '低', value: 0 },
        { label: '中', value: 1 },
        { label: '高', value: 2 },
        { label: '紧急', value: 3 },
      ],
    },
    colProps: { span: 8 },
  },
  {
    field: 'status',
    label: '告警状态',
    component: 'Select',
    componentProps: {
      placeholder: '请选择告警状态',
      options: [
        { label: '未处理', value: 0 },
        { label: '已处理', value: 1 },
        { label: '已恢复', value: 2 },
      ],
    },
    colProps: { span: 8 },
  },
  {
    field: 'source',
    label: '告警对象',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    field: 'metric',
    label: '告警指标',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    field: 'create_time',
    label: '创建时间',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
]

// 基础策略表单配置
export const baseStrategyFormSchema: FormSchema[] = [
  {
    label: 'ID',
    field: 'id',
    component: 'Input',
    show: false, // 隐藏字段
  },
  {
    label: '策略名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '策略描述',
    field: 'description',
    component: 'InputTextArea',
  },
  {
    label: '策略状态',
    field: 'status',
    component: 'Select',
    componentProps: {
      placeholder: '请选择策略状态',
      options: [
        { label: '启用', value: 1 },
        { label: '禁用', value: 0 },
      ],
    },
  },
  {
    label: '告警等级',
    field: 'level',
    required: true,
    component: 'Select',
    componentProps: {
      placeholder: '请选择告警等级',
      options: [
        { label: '低', value: 0 },
        { label: '中', value: 1 },
        { label: '高', value: 2 },
        { label: '紧急', value: 3 },
      ],
    },
  },
]

// 电表策略表单配置
export const powerMeterStrategyFormSchema: FormSchema[] = [
  ...baseStrategyFormSchema,
  // 电表阈值配置
  {
    label: '电表功率阈值(W)',
    field: 'power_threshold',
    component: 'InputNumber',
    componentProps: {
      placeholder: '请输入功率阈值',
      min: 0,
    },
  },
  {
    label: '日用电量阈值(kWh)',
    field: 'daily_threshold',
    component: 'InputNumber',
    componentProps: {
      placeholder: '请输入日用电量阈值',
      min: 0,
    },
  },
]

// 环境监测策略表单配置
export const environmentStrategyFormSchema: FormSchema[] = [
  ...baseStrategyFormSchema,
  // 环境监测阈值配置
  {
    label: '温度安全范围(°C)',
    field: 'temperature_range',
    component: 'InputGroup',
    componentProps: {
      compact: true,
    },
    children: [
      {
        field: 'temperature_min',
        component: 'InputNumber',
        componentProps: {
          placeholder: '最低温度',
          style: { width: '50%' },
        },
      },
      {
        field: 'temperature_max',
        component: 'InputNumber',
        componentProps: {
          placeholder: '最高温度',
          style: { width: '50%' },
        },
      },
    ],
  },
  {
    label: '湿度安全范围(%)',
    field: 'humidity_range',
    component: 'InputGroup',
    componentProps: {
      compact: true,
    },
    children: [
      {
        field: 'humidity_min',
        component: 'InputNumber',
        componentProps: {
          placeholder: '最低湿度',
          style: { width: '50%' },
        },
      },
      {
        field: 'humidity_max',
        component: 'InputNumber',
        componentProps: {
          placeholder: '最高湿度',
          style: { width: '50%' },
        },
      },
    ],
  },
  {
    label: 'PM2.5安全阈值(μg/m³)',
    field: 'pm25_threshold',
    component: 'InputNumber',
    componentProps: {
      placeholder: '请输入PM2.5阈值',
      min: 0,
    },
  },
  {
    label: 'PM10安全阈值(μg/m³)',
    field: 'pm10_threshold',
    component: 'InputNumber',
    componentProps: {
      placeholder: '请输入PM10阈值',
      min: 0,
    },
  },
  {
    label: 'CO2安全阈值(ppm)',
    field: 'co2_threshold',
    component: 'InputNumber',
    componentProps: {
      placeholder: '请输入CO2阈值',
      min: 0,
    },
  },
  // 通知配置
  {
    label: '通知方式',
    field: 'notification_methods',
    component: 'CheckboxGroup',
    componentProps: {
      options: [
        { label: '平台通知', value: 'platform' },
        { label: '短信预警', value: 'sms' },
        { label: '邮件通知', value: 'email' },
        { label: '微信通知', value: 'wechat' },
      ],
    },
  },
  {
    label: '接收人员',
    field: 'receivers',
    component: 'Select',
    componentProps: {
      mode: 'multiple',
      placeholder: '请选择接收人员',
      options: [
        { label: '系统管理员', value: 'admin' },
        { label: '运维人员', value: 'operator' },
        { label: '设备管理员', value: 'device_manager' },
        { label: '安全负责人', value: 'security_manager' },
      ],
    },
  },
  {
    label: '报警频次',
    field: 'alert_frequency',
    component: 'Select',
    componentProps: {
      placeholder: '请选择报警频次',
      options: [
        { label: '立即通知', value: 'immediate' },
        { label: '每5分钟', value: '5min' },
        { label: '每15分钟', value: '15min' },
        { label: '每30分钟', value: '30min' },
        { label: '每小时', value: '1hour' },
        { label: '每天一次', value: '1day' },
      ],
    },
  },
  {
    label: '静默时间',
    field: 'silence_hours',
    component: 'InputNumber',
    componentProps: {
      placeholder: '请输入静默时间(小时)',
      min: 0,
      max: 24,
    },
  },
]

// 通用策略表单配置（保持向后兼容）
export const strategyFormSchema: FormSchema[] = baseStrategyFormSchema
