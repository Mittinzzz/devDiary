<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { NButton, NInput, NSelect, NDatePicker, NIcon, NSpin, NEmpty, NPagination, NPopconfirm, useMessage } from 'naive-ui'
import { SearchOutline, SparklesOutline, CheckboxOutline, TrashOutline, CloseOutline } from '@vicons/ionicons5'
import { useDiaryStore } from '@/stores/diary'
import { useProjectStore } from '@/stores/project'
import { batchDeleteDiaries, deleteDiary } from '@/api'
import DiaryCard from '@/components/DiaryCard.vue'
import GenerateDialog from '@/components/GenerateDialog.vue'

const diaryStore = useDiaryStore()
const projectStore = useProjectStore()
const message = useMessage()

const search = ref('')
const styleFilter = ref<string | null>(null)
const projectFilter = ref<number | null>(null)
const dateRange = ref<[number, number] | null>(null)
const showGenerateDialog = ref(false)

// Multi-select mode
const selectMode = ref(false)
const selectedIds = ref<number[]>([])
const batchDeleting = ref(false)

const selectedCount = computed(() => selectedIds.value.length)

function toggleSelectMode() {
  selectMode.value = !selectMode.value
  if (!selectMode.value) {
    selectedIds.value = []
  }
}

function handleToggleSelect(id: number) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) {
    selectedIds.value = selectedIds.value.filter(i => i !== id)
  } else {
    selectedIds.value = [...selectedIds.value, id]
  }
}

async function handleDeleteSingle(id: number) {
  try {
    await diaryStore.removeDiary(id)
    message.success('删除成功')
  } catch (e: any) {
    message.error('删除失败')
  }
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  batchDeleting.value = true
  try {
    const ids = [...selectedIds.value]
    const result = await batchDeleteDiaries(ids)
    message.success(`成功删除 ${result.deleted_count} 篇日记`)
    selectedIds.value = []
    selectMode.value = false
    await loadFiltered()
  } catch (e: any) {
    message.error('批量删除失败：' + (e.response?.data?.detail || e.message))
  } finally {
    batchDeleting.value = false
  }
}

const styleOptions = [
  { label: '全部文体', value: '' },
  { label: '📝 日记', value: 'diary' },
  { label: '📖 博客', value: 'blog' },
  { label: '📊 报告', value: 'report' },
]

onMounted(async () => {
  await Promise.all([
    diaryStore.loadDiaries(),
    projectStore.loadProjects(),
  ])
})

async function loadFiltered(page = 1) {
  const params: any = { page }
  if (search.value) params.search = search.value
  if (styleFilter.value) params.style = styleFilter.value
  if (projectFilter.value) params.project_id = projectFilter.value
  if (dateRange.value) {
    params.date_from = new Date(dateRange.value[0]).toISOString().split('T')[0]
    params.date_to = new Date(dateRange.value[1]).toISOString().split('T')[0]
  }
  await diaryStore.loadDiaries(params)
}

function handlePageChange(page: number) {
  loadFiltered(page)
}

// Debounced search
let searchTimer: ReturnType<typeof setTimeout>
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadFiltered(), 300)
})

watch([styleFilter, projectFilter, dateRange], () => {
  loadFiltered()
})
</script>

<template>
  <div class="diary-list-view">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="gradient-text">日记列表</span>
      </h1>
      <div class="header-actions">
        <NButton
          :type="selectMode ? 'primary' : 'default'"
          secondary
          @click="toggleSelectMode"
        >
          <template #icon>
            <NIcon><CheckboxOutline /></NIcon>
          </template>
          {{ selectMode ? '退出选择' : '选择' }}
        </NButton>
        <NButton type="primary" @click="showGenerateDialog = true" class="generate-btn">
          <template #icon>
            <NIcon><SparklesOutline /></NIcon>
          </template>
          生成日记
        </NButton>
      </div>
    </div>

    <!-- Batch action bar -->
    <transition name="slide-down">
      <div v-if="selectMode && selectedCount > 0" class="batch-bar glass-card">
        <span class="batch-info">已选择 <strong>{{ selectedCount }}</strong> 篇日记</span>
        <div class="batch-actions">
          <NPopconfirm @positive-click="handleBatchDelete">
            <template #trigger>
              <NButton
                type="error"
                size="small"
                :loading="batchDeleting"
              >
                <template #icon>
                  <NIcon><TrashOutline /></NIcon>
                </template>
                删除选中 ({{ selectedCount }})
              </NButton>
            </template>
            确定要删除选中的 {{ selectedCount }} 篇日记吗？此操作不可撤销。
          </NPopconfirm>
          <NButton size="small" secondary @click="selectedIds = []">
            <template #icon>
              <NIcon><CloseOutline /></NIcon>
            </template>
            取消选择
          </NButton>
        </div>
      </div>
    </transition>

    <!-- Filters -->
    <div class="filters glass-card">
      <div class="filter-row">
        <NInput
          v-model:value="search"
          placeholder="搜索日记..."
          clearable
          class="search-input"
        >
          <template #prefix>
            <NIcon><SearchOutline /></NIcon>
          </template>
        </NInput>

        <NSelect
          v-model:value="styleFilter"
          :options="styleOptions"
          placeholder="文体筛选"
          clearable
          class="filter-select"
        />

        <NSelect
          v-model:value="projectFilter"
          :options="[{ label: '全部项目', value: null as any }, ...projectStore.projectOptions]"
          placeholder="项目筛选"
          clearable
          class="filter-select"
        />

        <NDatePicker
          v-model:value="dateRange"
          type="daterange"
          clearable
          class="date-picker"
        />
      </div>
    </div>

    <!-- Diary Grid -->
    <NSpin :show="diaryStore.loading">
      <div v-if="diaryStore.hasDiaries" class="diary-grid">
        <DiaryCard
          v-for="diary in diaryStore.diaries"
          :key="diary.id"
          :diary="diary"
          :selectable="selectMode"
          :selected="selectedIds.includes(diary.id)"
          @delete="handleDeleteSingle"
          @toggle-select="handleToggleSelect"
        />
      </div>

      <NEmpty
        v-else
        description="没有找到日记"
        size="large"
        class="empty-state"
      >
        <template #extra>
          <p class="text-gray-500 mb-4">开始生成你的第一篇开发日记吧</p>
        </template>
      </NEmpty>
    </NSpin>

    <!-- Pagination -->
    <div v-if="diaryStore.total > diaryStore.pageSize" class="pagination">
      <NPagination
        :page="diaryStore.page"
        :page-count="diaryStore.totalPages"
        :page-size="diaryStore.pageSize"
        @update:page="handlePageChange"
      />
    </div>

    <!-- Generate Dialog -->
    <GenerateDialog v-model:show="showGenerateDialog" />
  </div>
</template>

<style scoped>
.diary-list-view {
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

.header-actions {
  display: flex;
  gap: 10px;
}

.generate-btn {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  font-weight: 600;
}

/* Batch action bar */
.batch-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border: 1px solid rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.05);
}

.batch-info {
  color: #CBD5E1;
  font-size: 0.9rem;
}

.batch-info strong {
  color: #A78BFA;
}

.batch-actions {
  display: flex;
  gap: 8px;
}

/* Slide down transition */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
  margin-top: -24px;
  padding-top: 0;
  padding-bottom: 0;
}

.filters {
  padding: 16px 20px;
}

.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.filter-select {
  width: 160px;
}

.date-picker {
  width: 280px;
}

.diary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.empty-state {
  padding: 80px 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .header-actions {
    width: 100%;
  }
  .header-actions .n-button {
    flex: 1;
  }
  .filter-row {
    flex-direction: column;
  }
  .search-input, .filter-select, .date-picker {
    width: 100%;
  }
  .diary-grid {
    grid-template-columns: 1fr;
  }
  .batch-bar {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  .batch-actions {
    width: 100%;
  }
}
</style>
