<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  option: echarts.EChartsOption
  height?: string
}>()

const chartRef = ref<HTMLDivElement>()
const chartInstance = shallowRef<echarts.ECharts>()

function initChart() {
  if (!chartRef.value) return
  chartInstance.value = echarts.init(chartRef.value, 'dark', {
    renderer: 'canvas',
  })
  chartInstance.value.setOption({
    ...props.option,
    backgroundColor: 'transparent',
  })
}

function handleResize() {
  chartInstance.value?.resize()
}

watch(
  () => props.option,
  (newOption) => {
    if (chartInstance.value) {
      chartInstance.value.setOption({
        ...newOption,
        backgroundColor: 'transparent',
      }, true)
    }
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance.value?.dispose()
})
</script>

<template>
  <div
    ref="chartRef"
    :style="{ height: height || '300px', width: '100%' }"
  />
</template>
