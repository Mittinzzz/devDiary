<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NIcon, NSpin, NTag, NBreadcrumb, NBreadcrumbItem,
  NInput, NSelect, NTabPane, NTabs, useMessage,
} from 'naive-ui'
import {
  ArrowBackOutline, DownloadOutline, DocumentTextOutline,
  CodeSlashOutline, CreateOutline, SaveOutline, CloseOutline,
} from '@vicons/ionicons5'
import { useDiaryStore } from '@/stores/diary'
import { exportDiary, updateDiary } from '@/api'
import type { DiaryUpdate } from '@/types'
import MarkdownViewer from '@/components/MarkdownViewer.vue'

const route = useRoute()
const router = useRouter()
const diaryStore = useDiaryStore()
const message = useMessage()

const diaryId = computed(() => Number(route.params.id))

// Edit mode state
const isEditing = ref(false)
const editTitle = ref('')
const editContent = ref('')
const editStyle = ref<'diary' | 'blog' | 'report'>('diary')
const saving = ref(false)
const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  await diaryStore.loadDiary(diaryId.value)
})

import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

const diary = computed(() => diaryStore.currentDiary)

const formattedDate = computed(() => {
  if (!diary.value) return ''
  const from = new Date(diary.value.date_from)
  const to = new Date(diary.value.date_to)
  const fromStr = from.toLocaleDateString('zh-CN')
  const toStr = to.toLocaleDateString('zh-CN')
  return fromStr === toStr ? fromStr : `${fromStr} ~ ${toStr}`
})

const styleLabel = computed(() => {
  const map: Record<string, string> = {
    diary: '日记体',
    blog: '博客体',
    report: '报告体',
  }
  return diary.value ? map[diary.value.style] || diary.value.style : ''
})

const styleOptions = [
  { label: '📝 日记体', value: 'diary' },
  { label: '📖 博客体', value: 'blog' },
  { label: '📊 报告体', value: 'report' },
]

function enterEditMode() {
  if (!diary.value) return
  editTitle.value = diary.value.title
  editContent.value = diary.value.content
  editStyle.value = diary.value.style
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

async function handleSave() {
  if (!diary.value) return
  saving.value = true
  try {
    const data: DiaryUpdate = {
      title: editTitle.value,
      content: editContent.value,
      style: editStyle.value,
    }
    const updated = await updateDiary(diary.value.id, data)
    diaryStore.currentDiary = updated
    isEditing.value = false
    message.success('保存成功')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleExport(format: 'markdown' | 'html') {
  if (!diary.value) return
  try {
    const content = await exportDiary(diary.value.id, format)
    const blob = new Blob([content], {
      type: format === 'html' ? 'text/html' : 'text/markdown',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${diary.value.title}.${format === 'html' ? 'html' : 'md'}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Export failed:', e)
  }
}
</script>

<template>
  <div class="diary-detail-view">
    <NSpin :show="diaryStore.loading">
      <!-- Breadcrumb -->
      <NBreadcrumb class="breadcrumb">
        <NBreadcrumbItem @click="router.push({ name: 'diaries' })">
          日记列表
        </NBreadcrumbItem>
        <NBreadcrumbItem>
          {{ diary?.title || '加载中...' }}
        </NBreadcrumbItem>
      </NBreadcrumb>

      <template v-if="diary">
        <!-- Header Card -->
        <div class="header-card glass-card">
          <div class="header-top">
            <NButton text @click="router.push({ name: 'diaries' })" class="back-btn">
              <NIcon :size="20"><ArrowBackOutline /></NIcon>
              <span>返回</span>
            </NButton>
            <div class="header-actions">
              <template v-if="!isEditing">
                <NButton secondary size="small" @click="enterEditMode">
                  <template #icon>
                    <NIcon><CreateOutline /></NIcon>
                  </template>
                  编辑
                </NButton>
                <NButton secondary size="small" @click="handleExport('markdown')">
                  <template #icon>
                    <NIcon><DocumentTextOutline /></NIcon>
                  </template>
                  导出 Markdown
                </NButton>
                <NButton secondary size="small" @click="handleExport('html')">
                  <template #icon>
                    <NIcon><CodeSlashOutline /></NIcon>
                  </template>
                  导出 HTML
                </NButton>
              </template>
              <template v-else>
                <NButton
                  type="primary"
                  size="small"
                  :loading="saving"
                  @click="handleSave"
                  class="save-btn"
                >
                  <template #icon>
                    <NIcon><SaveOutline /></NIcon>
                  </template>
                  保存
                </NButton>
                <NButton secondary size="small" :disabled="saving" @click="cancelEdit">
                  <template #icon>
                    <NIcon><CloseOutline /></NIcon>
                  </template>
                  取消
                </NButton>
              </template>
            </div>
          </div>

          <!-- Title: view mode or edit mode -->
          <template v-if="!isEditing">
            <h1 class="diary-title">{{ diary.title }}</h1>
          </template>
          <template v-else>
            <NInput
              v-model:value="editTitle"
              placeholder="日记标题"
              class="edit-title-input"
              size="large"
            />
          </template>

          <div class="diary-meta">
            <span class="meta-item">📅 {{ formattedDate }}</span>
            <span class="meta-item">📁 {{ diary.project_name }}</span>
            <template v-if="!isEditing">
              <span class="meta-item">📝 {{ styleLabel }}</span>
            </template>
            <template v-else>
              <NSelect
                v-model:value="editStyle"
                :options="styleOptions"
                size="small"
                class="edit-style-select"
              />
            </template>
          </div>

          <div class="diary-tags" v-if="diary.tech_stack?.length && !isEditing">
            <NTag
              v-for="tag in diary.tech_stack"
              :key="tag"
              size="small"
              :bordered="false"
              class="tech-tag"
            >
              {{ tag }}
            </NTag>
          </div>
        </div>

        <!-- Content: View Mode -->
        <div v-if="!isEditing" class="content-card glass-card">
          <MarkdownViewer :content="diary.content" />
        </div>

        <!-- Content: Edit Mode — Desktop dual-pane -->
        <div v-else-if="!isMobile" class="edit-container">
          <div class="edit-pane glass-card">
            <h3 class="pane-title">📝 编辑</h3>
            <NInput
              v-model:value="editContent"
              type="textarea"
              placeholder="输入 Markdown 内容..."
              :autosize="{ minRows: 20 }"
              class="edit-textarea"
            />
          </div>
          <div class="preview-pane glass-card">
            <h3 class="pane-title">👁️ 预览</h3>
            <div class="preview-content">
              <MarkdownViewer :content="editContent" />
            </div>
          </div>
        </div>

        <!-- Content: Edit Mode — Mobile tab mode -->
        <div v-else class="edit-container-mobile glass-card">
          <NTabs type="line" animated>
            <NTabPane name="edit" tab="📝 编辑">
              <NInput
                v-model:value="editContent"
                type="textarea"
                placeholder="输入 Markdown 内容..."
                :autosize="{ minRows: 15 }"
                class="edit-textarea"
              />
            </NTabPane>
            <NTabPane name="preview" tab="👁️ 预览">
              <div class="preview-content">
                <MarkdownViewer :content="editContent" />
              </div>
            </NTabPane>
          </NTabs>
        </div>

        <!-- Bottom Stats -->
        <div class="stats-row" v-if="!isEditing">
          <div class="mini-stat glass-card">
            <span class="mini-stat-value">{{ diary.commit_count }}</span>
            <span class="mini-stat-label">提交数</span>
          </div>
          <div class="mini-stat glass-card">
            <span class="mini-stat-value text-green-400">+{{ diary.insertions }}</span>
            <span class="mini-stat-label">新增行</span>
          </div>
          <div class="mini-stat glass-card">
            <span class="mini-stat-value text-red-400">-{{ diary.deletions }}</span>
            <span class="mini-stat-label">删除行</span>
          </div>
          <div class="mini-stat glass-card" v-if="diary.tokens_used">
            <span class="mini-stat-value">{{ diary.tokens_used }}</span>
            <span class="mini-stat-label">Tokens</span>
          </div>
        </div>
      </template>
    </NSpin>
  </div>
</template>

<style scoped>
.diary-detail-view {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.breadcrumb {
  margin-bottom: 8px;
}

.header-card {
  padding: 24px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #94A3B8;
  transition: color 0.2s;
}
.back-btn:hover {
  color: #A78BFA;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.save-btn {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  font-weight: 600;
}

.diary-title {
  font-size: 1.6rem;
  font-weight: 700;
  background: linear-gradient(135deg, #6366F1, #A78BFA);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
}

.edit-title-input {
  margin-bottom: 12px;
}

.edit-style-select {
  width: 140px;
}

.diary-meta {
  display: flex;
  gap: 20px;
  color: #94A3B8;
  font-size: 0.9rem;
  flex-wrap: wrap;
  margin-bottom: 12px;
  align-items: center;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.diary-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tech-tag {
  background: rgba(99, 102, 241, 0.12) !important;
  color: #A78BFA !important;
  border: 1px solid rgba(99, 102, 241, 0.2) !important;
}

.content-card {
  padding: 32px;
}

/* Edit mode: dual pane layout */
.edit-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.edit-pane,
.preview-pane {
  padding: 20px;
  display: flex;
  flex-direction: column;
  max-height: 70vh;
  overflow: hidden;
}

.pane-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #94A3B8;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.edit-textarea {
  flex: 1;
}

.edit-textarea :deep(textarea) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
  font-size: 0.9rem;
  line-height: 1.7;
  color: #CBD5E1;
}

.preview-pane {
  overflow-y: auto;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
}

/* Mobile edit */
.edit-container-mobile {
  padding: 16px;
}

.edit-container-mobile .preview-content {
  min-height: 300px;
}

/* Stats row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.mini-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px;
  text-align: center;
}

.mini-stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #F8FAFC;
}

.mini-stat-label {
  font-size: 0.8rem;
  color: #64748B;
}

@media (max-width: 768px) {
  .diary-detail-view {
    gap: 16px;
  }
  .header-card {
    padding: 16px;
  }
  .header-top {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }
  .header-actions .n-button {
    flex: 1;
    min-width: 0;
  }
  .diary-title {
    font-size: 1.3rem;
  }
  .diary-meta {
    flex-direction: column;
    gap: 8px;
  }
  .content-card {
    padding: 16px;
  }
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
