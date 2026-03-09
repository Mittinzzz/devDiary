<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  NButton, NIcon, NModal, NForm, NFormItem, NInput, NEmpty, NSpin,
  NPopconfirm, useMessage,
} from 'naive-ui'
import { AddOutline, TrashOutline, FolderOpenOutline } from '@vicons/ionicons5'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()
const message = useMessage()

const showAddModal = ref(false)
const formData = ref({
  name: '',
  repo_path: '',
  description: '',
})
const addLoading = ref(false)
const expandedId = ref<number | null>(null)

onMounted(() => {
  projectStore.loadProjects()
})

async function handleAddProject() {
  if (!formData.value.name || !formData.value.repo_path) {
    message.warning('请填写项目名称和仓库路径')
    return
  }
  addLoading.value = true
  try {
    await projectStore.addProject(formData.value)
    message.success('项目添加成功！')
    showAddModal.value = false
    formData.value = { name: '', repo_path: '', description: '' }
  } catch (e: any) {
    message.error(e.response?.data?.detail || '添加失败')
  } finally {
    addLoading.value = false
  }
}

async function handleDeleteProject(id: number) {
  try {
    await projectStore.removeProject(id)
    message.success('项目已删除')
  } catch (e: any) {
    message.error('删除失败')
  }
}

function toggleExpand(id: number) {
  if (expandedId.value === id) {
    expandedId.value = null
  } else {
    expandedId.value = id
    projectStore.loadProjectStats(id)
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '未扫描'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="projects-view">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="gradient-text">项目管理</span>
      </h1>
      <NButton type="primary" @click="showAddModal = true">
        <template #icon>
          <NIcon><AddOutline /></NIcon>
        </template>
        添加项目
      </NButton>
    </div>

    <!-- Project List -->
    <NSpin :show="projectStore.loading">
      <div v-if="projectStore.hasProjects" class="project-list">
        <div
          v-for="project in projectStore.projects"
          :key="project.id"
          class="project-card glass-card"
        >
          <div class="project-main" @click="toggleExpand(project.id)">
            <div class="project-avatar">
              {{ project.name.charAt(0).toUpperCase() }}
            </div>
            <div class="project-info">
              <h3 class="project-name">{{ project.name }}</h3>
              <p class="project-path">{{ project.repo_path }}</p>
              <div class="project-meta">
                <span>📊 {{ project.total_commits }} 提交</span>
                <span>🕐 {{ formatDate(project.last_scanned) }}</span>
              </div>
            </div>
            <div class="project-languages">
              <div
                v-for="(count, lang) in (project.languages || {})"
                :key="String(lang)"
                class="lang-item"
              >
                <span class="lang-dot" :style="{ background: getLangColor(String(lang)) }"></span>
                <span class="lang-name">{{ lang }}</span>
              </div>
            </div>
            <div class="project-actions">
              <NPopconfirm @positive-click="handleDeleteProject(project.id)">
                <template #trigger>
                  <NButton text type="error" @click.stop>
                    <NIcon><TrashOutline /></NIcon>
                  </NButton>
                </template>
                确定删除该项目吗？
              </NPopconfirm>
            </div>
          </div>

          <!-- Expanded details -->
          <transition name="expand">
            <div v-if="expandedId === project.id && projectStore.currentStats" class="project-details">
              <div class="details-grid">
                <div class="detail-card">
                  <span class="detail-label">总提交数</span>
                  <span class="detail-value">{{ project.total_commits }}</span>
                </div>
                <div class="detail-card">
                  <span class="detail-label">最近扫描</span>
                  <span class="detail-value">{{ formatDate(project.last_scanned) }}</span>
                </div>
                <div class="detail-card">
                  <span class="detail-label">语言数量</span>
                  <span class="detail-value">{{ Object.keys(project.languages || {}).length }}</span>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>

      <NEmpty v-else description="还没有添加项目" size="large" class="empty-state">
        <template #icon>
          <NIcon :size="48" color="#475569"><FolderOpenOutline /></NIcon>
        </template>
        <template #extra>
          <p class="text-gray-500 mb-4">添加你的 Git 仓库，开始生成开发日记</p>
          <NButton type="primary" @click="showAddModal = true">
            添加第一个项目
          </NButton>
        </template>
      </NEmpty>
    </NSpin>

    <!-- Add Project Modal -->
    <NModal
      v-model:show="showAddModal"
      preset="dialog"
      title="添加项目"
      positive-text="确认"
      negative-text="取消"
      @positive-click="handleAddProject"
      :loading="addLoading"
    >
      <NForm :model="formData" label-placement="top" class="add-form">
        <NFormItem label="项目名称" required>
          <NInput v-model:value="formData.name" placeholder="例如：DevDiary" />
        </NFormItem>
        <NFormItem label="Git 仓库路径" required>
          <NInput v-model:value="formData.repo_path" placeholder="例如：E:/projects/my-project" />
        </NFormItem>
        <NFormItem label="项目描述">
          <NInput
            v-model:value="formData.description"
            type="textarea"
            placeholder="可选：项目简介"
            :rows="3"
          />
        </NFormItem>
      </NForm>
    </NModal>
  </div>
</template>

<script lang="ts">
const LANG_COLORS: Record<string, string> = {
  Python: '#3572A5',
  JavaScript: '#F1E05A',
  TypeScript: '#3178C6',
  Java: '#B07219',
  Go: '#00ADD8',
  Rust: '#DEA584',
  'C++': '#F34B7D',
  C: '#555555',
  'C#': '#178600',
  Ruby: '#701516',
  PHP: '#4F5D95',
  Swift: '#F05138',
  Vue: '#41B883',
  Shell: '#89E051',
  Dart: '#00B4AB',
}

function getLangColor(lang: string): string {
  return LANG_COLORS[lang] || '#6366F1'
}
</script>

<style scoped>
.projects-view {
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

.project-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-card {
  padding: 0;
  overflow: hidden;
}

.project-main {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  cursor: pointer;
  transition: background 0.2s;
}
.project-main:hover {
  background: rgba(255, 255, 255, 0.02);
}

.project-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #F8FAFC;
  margin-bottom: 2px;
}

.project-path {
  font-size: 0.8rem;
  color: #64748B;
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 6px;
}

.project-meta {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  color: #94A3B8;
}

.project-languages {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.lang-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: #CBD5E1;
}

.lang-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.project-details {
  padding: 0 20px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.detail-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.detail-label {
  display: block;
  font-size: 0.8rem;
  color: #64748B;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #F8FAFC;
}

.empty-state {
  padding: 80px 0;
}

.add-form {
  margin-top: 16px;
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .project-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .project-avatar {
    width: 40px;
    height: 40px;
    font-size: 1rem;
  }
  .project-languages {
    width: 100%;
  }
  .project-actions {
    align-self: flex-end;
  }
  .details-grid {
    grid-template-columns: 1fr;
  }
}
</style>
