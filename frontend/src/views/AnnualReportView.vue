<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { NButton, NButtonGroup, NSpin, NIcon, NEmpty } from 'naive-ui'
import { CalendarOutline, TrophyOutline, FlameOutline, CodeSlashOutline } from '@vicons/ionicons5'
import StatsChart from '@/components/StatsChart.vue'
import { fetchAnnualReport } from '@/api'
import type { AnnualReport } from '@/types'
import type * as echarts from 'echarts'


const loading = ref(false)
const report = ref<AnnualReport | null>(null)
const selectedYear = ref(new Date().getFullYear())
const error = ref('')

const yearOptions = computed(() => {
  const current = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => current - i)
})

async function loadReport() {
  loading.value = true
  error.value = ''
  try {
    report.value = await fetchAnnualReport(selectedYear.value)
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadReport)

function changeYear(year: number) {
  selectedYear.value = year
  loadReport()
}

// Monthly trend chart
const trendOption = computed<echarts.EChartsOption>(() => {
  if (!report.value) return {}
  const months = report.value.monthly_trend.map(m => m.month)
  const commits = report.value.monthly_trend.map(m => m.commits)

  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: '#94A3B8' },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#64748B' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    },
    series: [{
      type: 'bar',
      data: commits,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#A78BFA' },
            { offset: 1, color: '#6366F1' },
          ],
        } as any,
      },
      barWidth: 28,
    }],
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
  }
})

// Active days chart
const activeDaysOption = computed<echarts.EChartsOption>(() => {
  if (!report.value) return {}
  const months = report.value.active_days_trend.map(m => m.month)
  const days = report.value.active_days_trend.map(m => m.active_days)

  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: '#94A3B8' },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
    },
    yAxis: {
      type: 'value',
      max: 31,
      axisLabel: { color: '#64748B' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    },
    series: [{
      type: 'line',
      data: days,
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(34, 197, 94, 0.3)' },
            { offset: 1, color: 'rgba(34, 197, 94, 0.01)' },
          ],
        } as any,
      },
      lineStyle: { width: 3, color: '#22C55E' },
      itemStyle: { color: '#22C55E' },
      symbol: 'circle',
      symbolSize: 6,
    }],
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
  }
})

// Project ranking bar
const projectOption = computed<echarts.EChartsOption>(() => {
  if (!report.value) return {}
  const projects = [...report.value.project_ranking].reverse()

  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
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
      data: projects.map(p => p.commits),
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: {
          type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#6366F1' },
            { offset: 1, color: '#A78BFA' },
          ],
        } as any,
      },
      barWidth: 20,
    }],
    grid: { left: 120, right: 40, top: 10, bottom: 20 },
  }
})

// Language pie
const languageOption = computed<echarts.EChartsOption>(() => {
  if (!report.value) return {}
  const data = report.value.language_ranking.map(l => ({
    name: l.language,
    value: l.count,
  }))

  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical', right: 10, top: 'center',
      textStyle: { color: '#94A3B8' },
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      itemStyle: {
        borderRadius: 6,
        borderColor: '#0F172A',
        borderWidth: 2,
      },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#F8FAFC' },
      },
      data,
      color: ['#6366F1', '#8B5CF6', '#A78BFA', '#3B82F6', '#22C55E', '#F59E0B', '#EF4444', '#EC4899'],
    }],
  }
})

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}
</script>

<template>
  <div class="report-view">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <span class="gradient-text">📊 年度开发者报告</span>
        </h1>
        <p class="page-subtitle">你的 {{ selectedYear }} 年编码轨迹回顾</p>
      </div>
      <NButtonGroup>
        <NButton
          v-for="y in yearOptions"
          :key="y"
          :type="selectedYear === y ? 'primary' : 'default'"
          size="small"
          @click="changeYear(y)"
        >
          {{ y }}
        </NButton>
      </NButtonGroup>
    </div>

    <NSpin :show="loading">
      <NEmpty v-if="error" :description="error" class="error-state" />

      <template v-else-if="report">
        <!-- Hero Stats -->
        <div class="hero-section glass-card">
          <div class="hero-title">🎉 {{ report.year }} 年度总结</div>
          <div class="hero-stats">
            <div class="hero-stat">
              <div class="hero-value">{{ formatNumber(report.summary.total_commits) }}</div>
              <div class="hero-label">次提交</div>
            </div>
            <div class="hero-stat">
              <div class="hero-value">+{{ formatNumber(report.summary.total_insertions) }}</div>
              <div class="hero-label">行新增</div>
            </div>
            <div class="hero-stat">
              <div class="hero-value">{{ report.summary.total_active_days }}</div>
              <div class="hero-label">活跃天数</div>
            </div>
            <div class="hero-stat">
              <div class="hero-value">{{ report.summary.total_projects }}</div>
              <div class="hero-label">活跃项目</div>
            </div>
            <div class="hero-stat">
              <div class="hero-value">{{ report.summary.total_diaries }}</div>
              <div class="hero-label">篇日记</div>
            </div>
          </div>
        </div>

        <!-- Highlights -->
        <div class="highlights-grid">
          <div class="highlight-card glass-card">
            <div class="highlight-icon">📅</div>
            <div class="highlight-info">
              <div class="highlight-value">{{ report.highlights.best_month }}</div>
              <div class="highlight-label">最高产月份 ({{ report.highlights.best_month_commits }} 次提交)</div>
            </div>
          </div>
          <div class="highlight-card glass-card">
            <div class="highlight-icon">🔥</div>
            <div class="highlight-info">
              <div class="highlight-value">{{ report.highlights.longest_streak }} 天</div>
              <div class="highlight-label">最长连续编码</div>
            </div>
          </div>
          <div class="highlight-card glass-card">
            <div class="highlight-icon">⚡</div>
            <div class="highlight-info">
              <div class="highlight-value">{{ report.highlights.busiest_date }}</div>
              <div class="highlight-label">最忙的一天 ({{ report.highlights.busiest_date_commits }} 次提交)</div>
            </div>
          </div>
          <div class="highlight-card glass-card">
            <div class="highlight-icon">🕐</div>
            <div class="highlight-info">
              <div class="highlight-value">{{ report.highlights.peak_hour }}</div>
              <div class="highlight-label">最高效时段</div>
            </div>
          </div>
        </div>

        <!-- Charts -->
        <div class="charts-grid">
          <div class="chart-card glass-card">
            <h3 class="chart-title">📈 月度提交趋势</h3>
            <StatsChart :option="trendOption" height="300px" />
          </div>
          <div class="chart-card glass-card">
            <h3 class="chart-title">🟢 月度活跃天数</h3>
            <StatsChart :option="activeDaysOption" height="300px" />
          </div>
          <div class="chart-card glass-card">
            <h3 class="chart-title">🏆 项目排行榜</h3>
            <StatsChart
              :option="projectOption"
              :height="Math.max(200, report.project_ranking.length * 40) + 'px'"
            />
          </div>
          <div class="chart-card glass-card">
            <h3 class="chart-title">🎨 语言分布</h3>
            <StatsChart :option="languageOption" height="300px" />
          </div>
        </div>

        <!-- Achievements -->
        <div class="achievements-section glass-card" v-if="report.achievements.length">
          <h3 class="chart-title">🏅 年度成就</h3>
          <div class="achievements-grid">
            <div
              v-for="(ach, i) in report.achievements"
              :key="i"
              class="achievement-card"
            >
              <div class="achievement-icon">{{ ach.icon }}</div>
              <div class="achievement-title">{{ ach.title }}</div>
              <div class="achievement-desc">{{ ach.desc }}</div>
            </div>
          </div>
        </div>
      </template>
    </NSpin>
  </div>
</template>

<style scoped>
.report-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title { font-size: 28px; font-weight: 700; }
.page-subtitle { color: #94A3B8; font-size: 0.95rem; margin-top: 4px; }

/* Hero Section */
.hero-section {
  padding: 32px;
  text-align: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05)) !important;
  border: 1px solid rgba(99, 102, 241, 0.2) !important;
}

.hero-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #F8FAFC;
  margin-bottom: 24px;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.hero-stat { text-align: center; }

.hero-value {
  font-size: 2.2rem;
  font-weight: 800;
  background: linear-gradient(135deg, #A78BFA, #6366F1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.hero-label {
  font-size: 0.85rem;
  color: #94A3B8;
  margin-top: 4px;
}

/* Highlights */
.highlights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.highlight-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.highlight-icon { font-size: 2rem; flex-shrink: 0; }

.highlight-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: #F8FAFC;
}

.highlight-label {
  font-size: 0.8rem;
  color: #94A3B8;
  margin-top: 2px;
}

/* Charts */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-card { padding: 20px; }

.chart-title {
  font-size: 1rem;
  font-weight: 600;
  color: #F8FAFC;
  margin-bottom: 16px;
}

/* Achievements */
.achievements-section { padding: 24px; }

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.achievement-card {
  text-align: center;
  padding: 24px 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  transition: all 0.3s;
}

.achievement-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.1);
}

.achievement-icon { font-size: 2.5rem; margin-bottom: 8px; }
.achievement-title { font-size: 1rem; font-weight: 700; color: #F8FAFC; }
.achievement-desc { font-size: 0.8rem; color: #94A3B8; margin-top: 4px; }

.error-state { padding: 64px 0; }

@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
  .hero-stats { gap: 20px; }
  .hero-value { font-size: 1.6rem; }
}

@media (max-width: 480px) {
  .highlights-grid { grid-template-columns: 1fr; }
}
</style>
