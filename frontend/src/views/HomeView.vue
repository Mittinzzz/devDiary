<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NIcon, NSpin, NEmpty } from 'naive-ui'
import { SparklesOutline, DocumentTextOutline, CalendarOutline, TrendingUpOutline, CodeSlashOutline, GitCommitOutline } from '@vicons/ionicons5'
import { useDiaryStore } from '@/stores/diary'
import { useProjectStore } from '@/stores/project'
import DiaryCard from '@/components/DiaryCard.vue'
import GenerateDialog from '@/components/GenerateDialog.vue'

const router = useRouter()
const diaryStore = useDiaryStore()
const projectStore = useProjectStore()
const showGenerateDialog = ref(false)

onMounted(async () => {
  await Promise.all([
    diaryStore.loadOverview(),
    projectStore.loadProjects(),
  ])
})

const stats = computed(() => [
  {
    label: '总日记',
    value: diaryStore.overview?.total_diaries || 0,
    icon: DocumentTextOutline,
    color: '#6366F1',
    bg: 'rgba(99, 102, 241, 0.1)',
  },
  {
    label: '总提交',
    value: diaryStore.overview?.total_commits || 0,
    icon: GitCommitOutline,
    color: '#22C55E',
    bg: 'rgba(34, 197, 94, 0.1)',
  },
  {
    label: '活跃项目',
    value: diaryStore.overview?.total_projects || 0,
    icon: CodeSlashOutline,
    color: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.1)',
  },
  {
    label: '本周日记',
    value: diaryStore.overview?.this_week_diaries || 0,
    icon: CalendarOutline,
    color: '#3B82F6',
    bg: 'rgba(59, 130, 246, 0.1)',
  },
])

async function handleGenerate() {
  if (!projectStore.hasProjects) {
    router.push({ name: 'projects' })
    return
  }
  showGenerateDialog.value = true
}

function navigateToDiaries() {
  router.push({ name: 'diaries' })
}

function handleGenerateWeek() {
  if (!projectStore.hasProjects) {
    router.push({ name: 'projects' })
    return
  }
  showGenerateDialog.value = true
}

const todayStr = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })
})
</script>

<template>
  <div class="home-view">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <span class="gradient-text">仪表盘</span>
        </h1>
        <p class="page-subtitle">{{ todayStr }}</p>
      </div>
      <NButton
        type="primary"
        size="large"
        class="generate-btn"
        @click="handleGenerate"
      >
        <template #icon>
          <NIcon><SparklesOutline /></NIcon>
        </template>
        生成今日日记
      </NButton>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="stat-card glass-card"
      >
        <div class="stat-icon" :style="{ background: stat.bg }">
          <NIcon :size="24" :color="stat.color">
            <component :is="stat.icon" />
          </NIcon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="section">
      <h2 class="section-title">快捷操作</h2>
      <div class="actions-grid">
        <button class="action-card glass-card" @click="handleGenerate">
          <span class="action-icon">📝</span>
          <span class="action-label">生成日记</span>
          <span class="action-desc">今日开发记录</span>
        </button>
        <button class="action-card glass-card" @click="handleGenerateWeek">
          <span class="action-icon">📊</span>
          <span class="action-label">生成周报</span>
          <span class="action-desc">本周工作总结</span>
        </button>
        <button class="action-card glass-card" @click="router.push({ name: 'projects' })">
          <span class="action-icon">📁</span>
          <span class="action-label">管理项目</span>
          <span class="action-desc">添加 Git 仓库</span>
        </button>
        <button class="action-card glass-card" @click="router.push({ name: 'stats' })">
          <span class="action-icon">📈</span>
          <span class="action-label">查看统计</span>
          <span class="action-desc">数据可视化</span>
        </button>
      </div>
    </div>

    <!-- Recent Diaries -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">最近日记</h2>
        <NButton text type="primary" @click="navigateToDiaries" v-if="diaryStore.overview?.recent_diaries?.length">
          查看全部 →
        </NButton>
      </div>

      <NSpin :show="diaryStore.loading">
        <div v-if="diaryStore.overview?.recent_diaries?.length" class="diary-grid">
          <DiaryCard
            v-for="diary in diaryStore.overview.recent_diaries"
            :key="diary.id"
            :diary="diary"
          />
        </div>
        <NEmpty v-else description="还没有日记，快来生成第一篇吧！" class="empty-state">
          <template #extra>
            <NButton type="primary" @click="handleGenerate">
              生成第一篇日记
            </NButton>
          </template>
        </NEmpty>
      </NSpin>
    </div>

    <!-- Generate Dialog -->
    <GenerateDialog v-model:show="showGenerateDialog" />
  </div>
</template>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.page-subtitle {
  color: #94A3B8;
  font-size: 0.95rem;
}

.generate-btn {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  font-weight: 600;
  padding: 0 24px;
  height: 44px;
  transition: all 0.3s;
}
.generate-btn:hover {
  box-shadow: 0 0 24px rgba(99, 102, 241, 0.4);
  transform: translateY(-1px);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #F8FAFC;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.85rem;
  color: #94A3B8;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #F8FAFC;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 16px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  transition: all 0.3s ease;
  text-align: center;
}
.action-card:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.1);
}

.action-icon {
  font-size: 2rem;
}

.action-label {
  font-size: 1rem;
  font-weight: 600;
  color: #F8FAFC;
}

.action-desc {
  font-size: 0.8rem;
  color: #64748B;
}

.diary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.empty-state {
  padding: 48px 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .generate-btn {
    width: 100%;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .diary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
