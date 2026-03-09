<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { NButton, NButtonGroup, NSpin } from 'naive-ui'
import { useDiaryStore } from '@/stores/diary'
import { useProjectStore } from '@/stores/project'
import { fetchCommitTrend, fetchHeatmap, fetchInsights } from '@/api'
import StatsChart from '@/components/StatsChart.vue'
import type * as echarts from 'echarts'
import type { CommitTrendItem, HeatmapItem, InsightsResponse } from '@/types'

const diaryStore = useDiaryStore()
const projectStore = useProjectStore()
const timeRange = ref<'7d' | '30d' | '90d'>('30d')

// Stats reactive data
const trendData = ref<CommitTrendItem[]>([])
const heatmapData = ref<HeatmapItem[]>([])
const insights = ref<InsightsResponse | null>(null)

// Independent loading states
const trendLoading = ref(false)
const heatmapLoading = ref(false)
const insightsLoading = ref(false)

// Error states
const trendError = ref(false)
const heatmapError = ref(false)
const insightsError = ref(false)

async function loadTrend() {
  trendLoading.value = true
  trendError.value = false
  try {
    const days = timeRange.value === '7d' ? 7 : timeRange.value === '30d' ? 30 : 90
    const res = await fetchCommitTrend(days)
    trendData.value = res.items
  } catch (e) {
    console.error('Failed to load commit trend:', e)
    trendError.value = true
    trendData.value = []
  } finally {
    trendLoading.value = false
  }
}

async function loadHeatmap() {
  heatmapLoading.value = true
  heatmapError.value = false
  try {
    const days = timeRange.value === '7d' ? 7 : timeRange.value === '30d' ? 30 : 90
    const res = await fetchHeatmap(days)
    heatmapData.value = res.items
  } catch (e) {
    console.error('Failed to load heatmap:', e)
    heatmapError.value = true
    heatmapData.value = []
  } finally {
    heatmapLoading.value = false
  }
}

async function loadInsights() {
  insightsLoading.value = true
  insightsError.value = false
  try {
    const res = await fetchInsights()
    insights.value = res
  } catch (e) {
    console.error('Failed to load insights:', e)
    insightsError.value = true
    insights.value = null
  } finally {
    insightsLoading.value = false
  }
}

async function loadStats() {
  await Promise.all([loadTrend(), loadHeatmap(), loadInsights()])
}

onMounted(async () => {
  await Promise.all([
    diaryStore.loadOverview(),
    projectStore.loadProjects(),
    loadStats(),
  ])
})

// Reload trend and heatmap when time range changes
watch(timeRange, () => {
  loadTrend()
  loadHeatmap()
})

// Language distribution pie chart
const languageOption = computed<echarts.EChartsOption>(() => {
  const languages: Record<string, number> = {}
  for (const p of projectStore.projects) {
    for (const [lang, count] of Object.entries(p.languages || {})) {
      languages[lang] = (languages[lang] || 0) + (count as number)
    }
  }

  const data = Object.entries(languages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({ name, value }))

  const total = data.reduce((sum, d) => sum + d.value, 0)

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#94A3B8' },
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#0F172A',
        borderWidth: 2,
      },
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold',
          color: '#F8FAFC',
        },
      },
      data,
      color: ['#6366F1', '#8B5CF6', '#A78BFA', '#3B82F6', '#22C55E', '#F59E0B', '#EF4444', '#EC4899'],
    }],
    graphic: [{
      type: 'text',
      left: '27%',
      top: '45%',
      style: {
        text: String(total),
        textAlign: 'center',
        fill: '#F8FAFC',
        fontSize: 24,
        fontWeight: 'bold',
      },
    }, {
      type: 'text',
      left: '27%',
      top: '55%',
      style: {
        text: '总文件数',
        textAlign: 'center',
        fill: '#64748B',
        fontSize: 12,
      },
    }],
  }
})

// Commit trend area chart — uses real API data
const trendOption = computed<echarts.EChartsOption>(() => {
  const dates = trendData.value.map(d => {
    const dt = new Date(d.date)
    return dt.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  })
  const values = trendData.value.map(d => d.commit_count)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: '#64748B', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      axisLabel: { color: '#64748B' },
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      lineStyle: {
        width: 3,
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#6366F1' },
            { offset: 1, color: '#A78BFA' },
          ],
        } as any,
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.01)' },
          ],
        } as any,
      },
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#6366F1' },
    }],
    grid: {
      left: 50,
      right: 20,
      top: 20,
      bottom: 40,
    },
  }
})

// Heatmap chart — uses real API data
const heatmapOption = computed<echarts.EChartsOption>(() => {
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const days = ['一', '二', '三', '四', '五', '六', '日']

  const data: [number, number, number][] = heatmapData.value.map(d => [d.hour, d.day_of_week, d.count])

  const maxCount = data.length > 0
    ? Math.max(...data.map(d => d[2]), 1)
    : 15

  return {
    tooltip: {
      formatter: (params: any) => {
        return `${days[params.value[1]]} ${hours[params.value[0]]}: ${params.value[2]} 次提交`
      },
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: { show: true },
      axisLabel: { color: '#64748B', fontSize: 10, interval: 2 },
    },
    yAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: '#64748B' },
    },
    visualMap: {
      min: 0,
      max: maxCount,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: '#64748B' },
      inRange: {
        color: ['rgba(99, 102, 241, 0.05)', 'rgba(99, 102, 241, 0.3)', '#6366F1', '#8B5CF6', '#A78BFA'],
      },
    },
    series: [{
      type: 'heatmap',
      data,
      label: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(99, 102, 241, 0.5)',
        },
      },
    }],
    grid: {
      left: 40,
      right: 20,
      top: 10,
      bottom: 60,
    },
  }
})

// Project activity bar chart
const activityOption = computed<echarts.EChartsOption>(() => {
  const projects = projectStore.projects
    .slice(0, 8)
    .sort((a, b) => (b.total_commits || 0) - (a.total_commits || 0))

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#64748B' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    },
    yAxis: {
      type: 'category',
      data: projects.map(p => p.name),
      axisLabel: { color: '#CBD5E1', fontSize: 12 },
    },
    series: [{
      type: 'bar',
      data: projects.map(p => p.total_commits || 0),
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#6366F1' },
            { offset: 1, color: '#A78BFA' },
          ],
        } as any,
      },
      barWidth: 24,
    }],
    grid: {
      left: 120,
      right: 40,
      top: 10,
      bottom: 20,
    },
  }
})
</script>

<template>
  <div class="stats-view">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="gradient-text">统计概览</span>
      </h1>
      <NButtonGroup>
        <NButton
          v-for="range in (['7d', '30d', '90d'] as const)"
          :key="range"
          :type="timeRange === range ? 'primary' : 'default'"
          size="small"
          @click="timeRange = range"
        >
          {{ range === '7d' ? '7天' : range === '30d' ? '30天' : '90天' }}
        </NButton>
      </NButtonGroup>
    </div>

    <NSpin :show="diaryStore.loading && projectStore.loading">
      <!-- Charts Grid -->
      <div class="charts-grid">
        <!-- Language Distribution -->
        <div class="chart-card glass-card">
          <h3 class="chart-title">🎨 代码语言分布</h3>
          <StatsChart :option="languageOption" height="300px" />
        </div>

        <!-- Commit Trend -->
        <div class="chart-card glass-card">
          <h3 class="chart-title">📈 提交趋势</h3>
          <NSpin :show="trendLoading" size="small">
            <template v-if="trendError">
              <div class="empty-state">暂无数据</div>
            </template>
            <template v-else-if="trendData.length === 0 && !trendLoading">
              <div class="empty-state">暂无数据</div>
            </template>
            <template v-else>
              <StatsChart :option="trendOption" height="300px" />
            </template>
          </NSpin>
        </div>

        <!-- Heatmap -->
        <div class="chart-card glass-card">
          <h3 class="chart-title">🔥 提交时间热力图</h3>
          <NSpin :show="heatmapLoading" size="small">
            <template v-if="heatmapError">
              <div class="empty-state">暂无数据</div>
            </template>
            <template v-else-if="heatmapData.length === 0 && !heatmapLoading">
              <div class="empty-state">暂无数据</div>
            </template>
            <template v-else>
              <StatsChart :option="heatmapOption" height="300px" />
            </template>
          </NSpin>
        </div>

        <!-- Project Activity -->
        <div class="chart-card glass-card">
          <h3 class="chart-title">🏆 项目活跃度</h3>
          <StatsChart :option="activityOption" height="300px" />
        </div>
      </div>

      <!-- Insights -->
      <div class="insights glass-card">
        <h3 class="chart-title">💡 数据洞察</h3>
        <NSpin :show="insightsLoading" size="small">
          <template v-if="insightsError">
            <div class="empty-state">暂无洞察数据</div>
          </template>
          <template v-else>
            <div class="insight-items">
              <p class="insight">🕐 你最高效的编码时间段是 <strong>{{ insights?.most_active_hour || '暂无数据' }}</strong></p>
              <p class="insight">📅 你最活跃的工作日是 <strong>{{ insights?.most_active_day || '暂无数据' }}</strong></p>
              <p class="insight">📊 本月最活跃的项目是 <strong>{{ insights?.most_active_project || '暂无' }}</strong></p>
              <p class="insight">🔥 你已经连续 <strong>{{ insights?.current_streak || 0 }}</strong> 天保持编码记录</p>
              <p class="insight">📝 共生成了 <strong>{{ insights?.total_diaries || 0 }}</strong> 篇开发日记</p>
              <p class="insight">⚡ 本月共提交了 <strong>{{ insights?.this_month_commits || 0 }}</strong> 次代码</p>
            </div>
          </template>
        </NSpin>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.stats-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-card {
  padding: 20px;
}

.chart-title {
  font-size: 1rem;
  font-weight: 600;
  color: #F8FAFC;
  margin-bottom: 16px;
}

.insights {
  padding: 24px;
}

.insight-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.insight {
  color: #CBD5E1;
  font-size: 0.95rem;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border-left: 3px solid #6366F1;
}

.insight strong {
  color: #A78BFA;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #64748B;
  font-size: 0.95rem;
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
