<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  NForm, NFormItem, NInput, NSelect, NButton, NCard, NIcon, NSpin,
  useMessage,
} from 'naive-ui'
import { SaveOutline } from '@vicons/ionicons5'
import { fetchSettings, updateSettings } from '@/api'
import type { SettingsUpdate } from '@/types'

const message = useMessage()
const loading = ref(false)
const saving = ref(false)

const formData = ref<SettingsUpdate & { api_key_masked?: string }>({
  ai_provider: 'openai',
  api_key: '',
  model: '',
  base_url: '',
  output_dir: '',
  output_format: 'markdown',
  output_style: 'diary',
})

// Track if user has modified the API key
const apiKeyModified = ref(false)
const apiKeyMasked = ref('')

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: '智谱 AI', value: 'zhipu' },
  { label: '工蜂', value: 'gongfeng' },
]

const formatOptions = [
  { label: 'Markdown', value: 'markdown' },
  { label: 'HTML', value: 'html' },
  { label: 'Markdown + HTML', value: 'both' },
]

const styleOptions = [
  { label: '📝 日记体', value: 'diary' },
  { label: '📖 博客体', value: 'blog' },
  { label: '📊 报告体', value: 'report' },
]

onMounted(async () => {
  loading.value = true
  try {
    const settings = await fetchSettings()
    formData.value = {
      ai_provider: settings.ai_provider || 'openai',
      api_key: '',
      model: settings.model || '',
      base_url: settings.base_url || '',
      output_dir: settings.output_dir || '',
      output_format: settings.output_format || 'markdown',
      output_style: settings.output_style || 'diary',
    }
    apiKeyMasked.value = settings.api_key_masked || ''
  } catch (e: any) {
    message.error('加载配置失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
})

function handleApiKeyInput(value: string) {
  apiKeyModified.value = true
  formData.value.api_key = value
}

async function handleSave() {
  saving.value = true
  try {
    const data: SettingsUpdate = {
      ai_provider: formData.value.ai_provider,
      model: formData.value.model,
      base_url: formData.value.base_url,
      output_dir: formData.value.output_dir,
      output_format: formData.value.output_format,
      output_style: formData.value.output_style,
    }
    // Only send api_key if user has modified it
    if (apiKeyModified.value && formData.value.api_key) {
      data.api_key = formData.value.api_key
    }
    const updated = await updateSettings(data)
    apiKeyMasked.value = updated.api_key_masked || ''
    apiKeyModified.value = false
    formData.value.api_key = ''
    message.success('配置保存成功')
  } catch (e: any) {
    message.error('保存失败：' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="settings-view">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="gradient-text">系统设置</span>
      </h1>
    </div>

    <NSpin :show="loading">
      <div class="settings-content">
        <!-- AI Configuration -->
        <NCard class="settings-card glass-card" :bordered="false">
          <template #header>
            <div class="card-header">
              <span class="card-icon">🤖</span>
              <span>AI 配置</span>
            </div>
          </template>

          <NForm :model="formData" label-placement="top">
            <div class="form-grid">
              <NFormItem label="AI 服务商" path="ai_provider">
                <NSelect
                  v-model:value="formData.ai_provider"
                  :options="providerOptions"
                  placeholder="选择 AI 服务商"
                />
              </NFormItem>

              <NFormItem label="API Key" path="api_key">
                <NInput
                  :value="apiKeyModified ? formData.api_key : ''"
                  :placeholder="apiKeyMasked || '输入 API Key'"
                  type="password"
                  show-password-on="click"
                  @update:value="handleApiKeyInput"
                />
              </NFormItem>

              <NFormItem label="Model" path="model">
                <NInput
                  v-model:value="formData.model"
                  placeholder="例如：gpt-4o、deepseek-chat"
                />
              </NFormItem>

              <NFormItem label="Base URL" path="base_url">
                <NInput
                  v-model:value="formData.base_url"
                  placeholder="例如：https://api.openai.com/v1"
                />
              </NFormItem>
            </div>
          </NForm>
        </NCard>

        <!-- Output Configuration -->
        <NCard class="settings-card glass-card" :bordered="false">
          <template #header>
            <div class="card-header">
              <span class="card-icon">📄</span>
              <span>输出配置</span>
            </div>
          </template>

          <NForm :model="formData" label-placement="top">
            <div class="form-grid">
              <NFormItem label="输出目录" path="output_dir">
                <NInput
                  v-model:value="formData.output_dir"
                  placeholder="例如：E:/output/diaries"
                />
              </NFormItem>

              <NFormItem label="输出格式" path="output_format">
                <NSelect
                  v-model:value="formData.output_format"
                  :options="formatOptions"
                  placeholder="选择输出格式"
                />
              </NFormItem>

              <NFormItem label="默认风格" path="output_style">
                <NSelect
                  v-model:value="formData.output_style"
                  :options="styleOptions"
                  placeholder="选择默认风格"
                />
              </NFormItem>
            </div>
          </NForm>
        </NCard>

        <!-- Save Button -->
        <div class="save-area">
          <NButton
            type="primary"
            size="large"
            :loading="saving"
            @click="handleSave"
            class="save-btn"
          >
            <template #icon>
              <NIcon><SaveOutline /></NIcon>
            </template>
            保存配置
          </NButton>
        </div>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.settings-view {
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
}

.page-title {
  font-size: 28px;
  font-weight: 700;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
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

.card-icon {
  font-size: 1.3rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 20px;
}

.save-area {
  display: flex;
  justify-content: center;
  padding: 8px 0 24px;
}

.save-btn {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  font-weight: 600;
  padding: 0 40px;
  height: 44px;
  transition: all 0.3s;
}
.save-btn:hover {
  box-shadow: 0 0 24px rgba(99, 102, 241, 0.4);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
