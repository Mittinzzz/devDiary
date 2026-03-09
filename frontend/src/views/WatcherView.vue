<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted } from 'vue'
import {
  NCard, NButton, NIcon, NSwitch, NSelect, NInput, NTag, NSpin,
  NTimePicker, useMessage, NEmpty,
} from 'naive-ui'
import { PlayOutline, StopOutline, RefreshOutline, TimeOutline } from '@vicons/ionicons5'
import { fetchWatcherStatus, startWatcher, stopWatcher, updateWatcherConfig } from '@/api'
import type { WatcherConfig } from '@/types'

const message = useMessage()
const loading = ref(false)
const saving = ref(false)

// State
const running = ref(false)
const lastCheck = ref<string | null>(null)
const lastGenerated = ref<string | null>(null)
const nextRun = ref<string | null>(null)
const diariesGenerated = ref(0)
const errors = ref<string[]>([])

// Config
const config = ref({
  enabled: true,
  schedule: 'daily' as string,
  time: '09:00',
  weekday: 'monday',
  auto_scan: true,
  notify_desktop: true,
  notify_email: '' as string | null,
  notify_webhook: '' as string | null,
})

let pollTimer: ReturnType<typeof setInterval> | null = null

const scheduleOptions = [
  { label: '📅 每天自动生成', value: 'daily' },
  { label: '📆 每周自动生成', value: 'weekly' },
  { label: '🚀 推送后自动生成', value: 'on_push' },
]

const weekdayOptions = [
  { label: '周一', value: 'monday' },
  { label: '周二', value: 'tuesday' },
  { label: '周三', value: 'wednesday' },
  { label: '周四', value: 'thursday' },
  { label: '周五', value: 'friday' },
  { label: '周六', value: 'saturday' },
  { label: '周日', value: 'sunday' },
]

async function loadStatus() {
  try {
    const data = await fetchWatcherStatus()
    running.value = data.state.running
    lastCheck.value = data.state.last_check
    lastGenerated.value = data.state.last_generated
    nextRun.value = data.state.next_run
    diariesGenerated.value = data.state.diaries_generated
    errors.value = data.state.errors || []

    config.value = {
      ...config.value,
      enabled: data.config.enabled,
      schedule: data.config.schedule,
      time: data.config.time,
      weekday: data.config.weekday,
      auto_scan: data.config.auto_scan,
      notify_desktop: data.config.notify_desktop,
      notify_email: data.config.notify_email || '',
      notify_webhook: data.config.notify_webhook || '',
    }
  } catch (e) {
    // API might not be available yet
  }
}

async function handleStart() {
  loading.value = true
  try {
    await startWatcher()
    running.value = true
    message.success('监听服务已启动')
  } catch (e: any) {
    message.error('启动失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function handleStop() {
  loading.value = true
  try {
    await stopWatcher()
    running.value = false
    message.success('监听服务已停止')
  } catch (e: any) {
    message.error('停止失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    await updateWatcherConfig({
      ...config.value,
      notify_email: config.value.notify_email || null,
      notify_webhook: config.value.notify_webhook || null,
    })
    message.success('配置保存成功')
  } catch (e: any) {
    message.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function formatTime(isoStr: string | null): string {
  if (!isoStr) return '从未'
  try {
    return new Date(isoStr).toLocaleString('zh-CN')
  } catch {
    return isoStr
  }
}

onMounted(() => {
  loadStatus()
  // Poll every 30s
  pollTimer = setInterval(loadStatus, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="watcher-view">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <span class="gradient-text">🔍 Git 实时监听</span>
        </h1>
        <p class="page-subtitle">自动监听 Git 仓库变更，定时生成开发日记</p>
      </div>
      <div class="header-actions">
        <NButton text @click="loadStatus" :loading="loading">
          <template #icon><NIcon><RefreshOutline /></NIcon></template>
          刷新状态
        </NButton>
      </div>
    </div>

    <!-- Status Card -->
    <NCard class="status-card glass-card" :bordered="false">
      <template #header>
        <div class="card-header">
          <span class="card-icon">📡</span>
          <span>服务状态</span>
          <NTag :type="running ? 'success' : 'default'" size="small" class="status-tag">
            {{ running ? '运行中' : '已停止' }}
          </NTag>
        </div>
      </template>

      <div class="status-grid">
        <div class="status-item">
          <span class="status-label">上次检查</span>
          <span class="status-value">{{ formatTime(lastCheck) }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">上次生成</span>
          <span class="status-value">{{ formatTime(lastGenerated) }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">下次执行</span>
          <span class="status-value">{{ formatTime(nextRun) }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">已生成日记</span>
          <span class="status-value highlight">{{ diariesGenerated }} 篇</span>
        </div>
      </div>

      <div class="control-buttons">
        <NButton
          v-if="!running"
          type="primary"
          size="large"
          :loading="loading"
          @click="handleStart"
          class="action-btn start-btn"
        >
          <template #icon><NIcon><PlayOutline /></NIcon></template>
          启动监听
        </NButton>
        <NButton
          v-else
          type="error"
          size="large"
          :loading="loading"
          @click="handleStop"
          class="action-btn"
        >
          <template #icon><NIcon><StopOutline /></NIcon></template>
          停止监听
        </NButton>
      </div>

      <!-- Recent errors -->
      <div v-if="errors.length" class="errors-section">
        <h4 class="errors-title">⚠️ 最近错误</h4>
        <div v-for="(err, i) in errors" :key="i" class="error-item">{{ err }}</div>
      </div>
    </NCard>

    <!-- Configuration -->
    <NCard class="config-card glass-card" :bordered="false">
      <template #header>
        <div class="card-header">
          <span class="card-icon">⚙️</span>
          <span>监听配置</span>
        </div>
      </template>

      <div class="config-form">
        <div class="config-row">
          <span class="config-label">启用自动监听</span>
          <NSwitch v-model:value="config.enabled" />
        </div>

        <div class="config-row">
          <span class="config-label">生成频率</span>
          <NSelect
            v-model:value="config.schedule"
            :options="scheduleOptions"
            style="width: 240px"
          />
        </div>

        <div class="config-row" v-if="config.schedule === 'daily' || config.schedule === 'weekly'">
          <span class="config-label">执行时间</span>
          <NInput v-model:value="config.time" placeholder="09:00" style="width: 120px" />
        </div>

        <div class="config-row" v-if="config.schedule === 'weekly'">
          <span class="config-label">执行日期</span>
          <NSelect
            v-model:value="config.weekday"
            :options="weekdayOptions"
            style="width: 120px"
          />
        </div>

        <div class="config-row">
          <span class="config-label">桌面通知</span>
          <NSwitch v-model:value="config.notify_desktop" />
        </div>

        <div class="config-row">
          <span class="config-label">邮箱通知</span>
          <NInput
            v-model:value="config.notify_email"
            placeholder="留空则不发送"
            style="width: 280px"
          />
        </div>

        <div class="config-row">
          <span class="config-label">Webhook 通知</span>
          <NInput
            v-model:value="config.notify_webhook"
            placeholder="飞书/钉钉/Slack Webhook URL"
            style="width: 280px"
          />
        </div>
      </div>

      <div class="save-area">
        <NButton type="primary" :loading="saving" @click="handleSave" class="save-btn">
          保存配置
        </NButton>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.watcher-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title { font-size: 28px; font-weight: 700; }
.page-subtitle { color: #94A3B8; font-size: 0.95rem; margin-top: 4px; }

.status-card, .config-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  color: #F8FAFC;
}

.card-icon { font-size: 1.3rem; }
.status-tag { margin-left: auto; }

.status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.status-item {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border-left: 3px solid #6366F1;
}

.status-label { display: block; font-size: 0.8rem; color: #64748B; margin-bottom: 4px; }
.status-value { font-size: 0.95rem; color: #CBD5E1; }
.status-value.highlight { color: #A78BFA; font-weight: 700; }

.control-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.action-btn { padding: 0 32px; height: 44px; font-weight: 600; }
.start-btn {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
}

.errors-section {
  margin-top: 16px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.05);
  border-radius: 8px;
}

.errors-title { font-size: 0.85rem; color: #EF4444; margin-bottom: 8px; }
.error-item { font-size: 0.8rem; color: #94A3B8; padding: 4px 0; }

/* Config form */
.config-form { display: flex; flex-direction: column; gap: 20px; }

.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.config-label { font-size: 0.95rem; color: #CBD5E1; min-width: 120px; }

.save-area {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

.save-btn {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  font-weight: 600;
  padding: 0 40px;
  height: 44px;
}

@media (max-width: 640px) {
  .status-grid { grid-template-columns: 1fr; }
  .config-row { flex-direction: column; align-items: flex-start; gap: 8px; }
}
</style>
