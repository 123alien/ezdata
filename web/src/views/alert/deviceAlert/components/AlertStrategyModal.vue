<template>
  <BasicModal
    v-bind="$attrs"
    @register="registerModal"
    :title="getTitle"
    @ok="handleSubmit"
    :okButtonProps="{ loading: confirmLoading }"
  >
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed, unref } from 'vue'
import { BasicModal, useModalInner } from '/@/components/Modal'
import { BasicForm, useForm } from '/@/components/Form'
import { baseStrategyFormSchema, powerMeterStrategyFormSchema, environmentStrategyFormSchema } from '../deviceAlert.data'
import { addAlertStrategy, editAlertStrategy } from '../deviceAlert.api'

const emit = defineEmits(['success', 'register'])

const isUpdate = ref(true)
const confirmLoading = ref(false)
const data = ref(null)

// 根据策略类型选择表单配置
const getFormSchema = (strategyName?: string) => {
  if (strategyName?.includes('电表') || strategyName?.includes('功率')) {
    return powerMeterStrategyFormSchema
  } else if (strategyName?.includes('环境') || strategyName?.includes('监测')) {
    return environmentStrategyFormSchema
  }
  return baseStrategyFormSchema
}

// 动态表单配置
const currentFormSchema = ref(baseStrategyFormSchema)

const [registerForm, { setFieldsValue, updateSchema, resetFields, validate }] = useForm({
  labelWidth: 100,
  schemas: currentFormSchema,
  showActionButtonGroup: false,
  actionColOptions: {
    span: 23,
  },
})

const [registerModal, { setModalProps, closeModal }] = useModalInner(async (modalData) => {
  resetFields()
  setModalProps({ confirmLoading: false })
  isUpdate.value = !!modalData?.isUpdate
  data.value = modalData

  // 根据策略名称动态更新表单配置
  const strategyName = modalData?.record?.name || modalData?.strategyName || ''
  console.log('策略名称:', strategyName) // 调试日志
  const formSchema = getFormSchema(strategyName)
  console.log('选择的表单配置:', formSchema.length, '个字段') // 调试日志
  
  // 直接更新表单配置
  currentFormSchema.value = formSchema
  console.log('已更新表单配置，当前字段数:', currentFormSchema.value.length) // 调试日志

  if (unref(isUpdate)) {
    const record = modalData.record
    const formData = {
      ...record,
      // 从 trigger_conf 中提取数据
      power_threshold: record.trigger_conf?.power_threshold,
      daily_threshold: record.trigger_conf?.daily_threshold,
      temperature_min: record.trigger_conf?.temperature_range?.min,
      temperature_max: record.trigger_conf?.temperature_range?.max,
      humidity_min: record.trigger_conf?.humidity_range?.min,
      humidity_max: record.trigger_conf?.humidity_range?.max,
      pm25_threshold: record.trigger_conf?.pm25_threshold,
      pm10_threshold: record.trigger_conf?.pm10_threshold,
      co2_threshold: record.trigger_conf?.co2_threshold,
      // 从 forward_conf 中提取数据
      notification_methods: record.forward_conf?.notification_methods?.join(','),
      receivers: record.forward_conf?.receivers?.join(','),
      alert_frequency: record.forward_conf?.alert_frequency,
      silence_hours: record.forward_conf?.silence_hours,
    }
    setFieldsValue(formData)
  }
})

const getTitle = computed(() => (!unref(isUpdate) ? '新增告警策略' : '编辑告警策略'))

async function handleSubmit() {
  try {
    const values = await validate()
    setModalProps({ confirmLoading: true })
    
    // 组织数据到正确的结构中
    const submitData = {
      ...values,
      trigger_conf: {
        // 电表阈值
        power_threshold: values.power_threshold,
        daily_threshold: values.daily_threshold,
        // 环境监测阈值
        temperature_range: values.temperature_min && values.temperature_max 
          ? { min: values.temperature_min, max: values.temperature_max }
          : undefined,
        humidity_range: values.humidity_min && values.humidity_max 
          ? { min: values.humidity_min, max: values.humidity_max }
          : undefined,
        pm25_threshold: values.pm25_threshold,
        pm10_threshold: values.pm10_threshold,
        co2_threshold: values.co2_threshold,
      },
      forward_conf: {
        notification_methods: values.notification_methods ? values.notification_methods.split(',') : ['platform'],
        receivers: values.receivers ? values.receivers.split(',') : ['admin'],
        alert_frequency: values.alert_frequency,
        silence_hours: values.silence_hours,
      }
    }
    
    if (unref(isUpdate)) {
      await editAlertStrategy(submitData)
    } else {
      await addAlertStrategy(submitData)
    }
    
    closeModal()
    emit('success')
  } finally {
    setModalProps({ confirmLoading: false })
  }
}
</script>
