<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NModal, NForm, NFormItem, NSelect, NDatePicker, NButton, NIcon,
  NResult, NSpin, useMessage,
} from 'naive-ui'
import { SparklesOutline } from '@vicons/ionicons5'
import { useProjectStore } from '@/stores/project'
import { useDiaryStore } from '@/stores/diary'
import { useRouter } from 'vue-router'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const router = useRouter()
const projectStore = useProjectStore()
const diaryStore = useDiaryStore()
const message = useMessage()

const formData = ref({
  project_id: null as number | null,
  dateRange: null as [number, number] | null,
  style: 'diary' as string,
  output_format: 'both' as string,
})

const generating = ref(false)
const generated = ref(false)
const generatedDiaryId = ref<number | null>(null)
const generatedMessage = ref('')

const styleOptions = [
  { label: '📝 日记体 — 轻松口语化', value: 'diary' },
  { label: '📖 博客体 — 技术分享风', value: 'blog' },
  { label: '📊 报告体 — 正式工作汇报', value: 'report' },
]

const formatOptions = [
  { label: 'Markdown + HTML', value: 'both' },
  { label: '仅 Markdown', value: 'markdown' },
  { label: '仅 HTML', value: 'html' },
]

const canGenerate = computed(() => {
  return formData.value.project_id !== null
})

// Reset state when dialog opens
watch(() => props.show, (val) => {
  if (val) {
    generated.value = false
    generatedDiaryId.value = null
    generatedMessage.value = ''
    // Set default date range to today
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const todayEnd = new Date()
    todayEnd.setHours(23, 59, 59, 999)
    formData.value.dateRange = [today.getTime(), todayEnd.getTime()]

    // Load projects if not loaded
    if (!projectStore.hasProjects) {
      projectStore.loadProjects()
    }
  }
})

async function handleGenerate() {
  if (!formData.value.project_id) {
    message.warning('请选择一个项目')
    return
  }

  generating.value = true
  try {
    const params: any = {
      project_id: formData.value.project_id,
      style: formData.value.style,
      output_format: formData.value.output_format,
    }

    if (formData.value.dateRange) {
      params.date_from = new Date(formData.value.dateRange[0]).toISOString().split('T')[0]
      params.date_to = new Date(formData.value.dateRange[1]).toISOString().split('T')[0]
    }

    const result = await diaryStore.generate(params)
    generated.value = true
    generatedDiaryId.value = result.diary.id
    generatedMessage.value = result.message
    message.success('日记生成成功！')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '生成失败，请检查配置和网络')
  } finally {
    generating.value = false
  }
}

function handleViewDiary() {
  emit('update:show', false)
  if (generatedDiaryId.value) {
    router.push({ name: 'diary-detail', params: { id: generatedDiaryId.value } })
  }
}

function handleClose() {
  if (!generating.value) {
    emit('update:show', false)
  }
}
</script>

<template>
  <NModal
    :show="show"
    @update:show="handleClose"
    :mask-closable="!generating"
    :close-on-esc="!generating"
    preset="card"
    title="✨ 生成开发日记"
    :style="{ width: '520px' }"
    :bordered="false"
    :segmented="{ content: true, footer: true }"
  >
    <!-- Success State -->
    <div v-if="generated" class="success-content">
      <NResult
        status="success"
        title="日记生成成功！"
        :description="generatedMessage"
      >
        <template #footer>
          <div class="success-actions">
            <NButton type="primary" @click="handleViewDiary">
              查看日记
            </NButton>
            <NButton secondary @click="generated = false">
              继续生成
            </NButton>
          </div>
        </template>
      </NResult>
    </div>

    <!-- Generating State -->
    <div v-else-if="generating" class="generating-content">
      <NSpin size="large" />
      <p class="generating-text">正在扫描 Git 仓库并生成日记...</p>
      <p class="generating-hint">AI 正在分析你的提交记录，这可能需要 30-60 秒</p>
    </div>

    <!-- Form State -->
    <NForm v-else :model="formData" label-placement="top" class="generate-form">
      <NFormItem label="选择项目" required>
        <NSelect
          v-model:value="formData.project_id"
          :options="projectStore.projectOptions"
          placeholder="选择要生成日记的 Git 项目"
          filterable
        />
      </NFormItem>

      <NFormItem label="日期范围">
        <NDatePicker
          v-model:value="formData.dateRange"
          type="daterange"
          clearable
          :style="{ width: '100%' }"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
      </NFormItem>

      <div class="form-row">
        <NFormItem label="写作风格" class="form-col">
          <NSelect
            v-model:value="formData.style"
            :options="styleOptions"
          />
        </NFormItem>
        <NFormItem label="输出格式" class="form-col">
          <NSelect
            v-model:value="formData.output_format"
            :options="formatOptions"
          />
        </NFormItem>
      </div>
    </NForm>

    <!-- Footer (only show when in form state) -->
    <template #footer>
      <div v-if="!generated && !generating" class="dialog-footer">
        <NButton @click="handleClose">取消</NButton>
        <NButton
          type="primary"
          :disabled="!canGenerate"
          @click="handleGenerate"
          class="generate-btn"
        >
          <template #icon>
            <NIcon><SparklesOutline /></NIcon>
          </template>
          开始生成
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.generate-form {
  padding: 8px 0;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-col {
  flex: 1;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.generate-btn {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  font-weight: 600;
}

.generating-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 40px 0;
}

.generating-text {
  font-size: 1rem;
  font-weight: 600;
  color: #F8FAFC;
}

.generating-hint {
  font-size: 0.85rem;
  color: #64748B;
}

.success-content {
  padding: 20px 0;
}

.success-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
