<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NIcon, NPopconfirm, NButton, NCheckbox } from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import type { Diary } from '@/types'

const props = defineProps<{
  diary: Diary
  selectable?: boolean
  selected?: boolean
}>()

const emit = defineEmits<{
  (e: 'delete', id: number): void
  (e: 'toggle-select', id: number): void
}>()

const router = useRouter()

const formattedDate = computed(() => {
  const d = new Date(props.diary.date_from || props.diary.created_at)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
})

const styleLabel = computed(() => {
  const map: Record<string, string> = {
    diary: '📝 日记',
    blog: '📖 博客',
    report: '📊 报告',
  }
  return map[props.diary.style] || props.diary.style
})

const truncatedSummary = computed(() => {
  const text = props.diary.summary || props.diary.content
  const cleaned = text.replace(/[#*`\-]/g, '').trim()
  return cleaned.length > 150 ? cleaned.slice(0, 150) + '...' : cleaned
})

function navigateToDetail() {
  if (props.selectable) {
    emit('toggle-select', props.diary.id)
    return
  }
  router.push({ name: 'diary-detail', params: { id: props.diary.id } })
}

function handleDelete() {
  emit('delete', props.diary.id)
}

function handleCheckboxChange() {
  emit('toggle-select', props.diary.id)
}
</script>

<template>
  <div
    class="diary-card glass-card p-5 cursor-pointer"
    :class="{ 'card-selected': selected }"
    @click="navigateToDetail"
  >
    <!-- Selection checkbox -->
    <div class="card-top-row">
      <div class="date-tag">
        {{ formattedDate }}
      </div>
      <div class="card-top-actions" @click.stop>
        <NCheckbox
          v-if="selectable"
          :checked="selected"
          @update:checked="handleCheckboxChange"
        />
        <NPopconfirm
          v-if="!selectable"
          @positive-click="handleDelete"
        >
          <template #trigger>
            <NButton text size="tiny" class="delete-btn">
              <NIcon :size="16"><TrashOutline /></NIcon>
            </NButton>
          </template>
          确定要删除这篇日记吗？
        </NPopconfirm>
      </div>
    </div>

    <!-- Title -->
    <h3 class="title">{{ diary.title }}</h3>

    <!-- Summary -->
    <p class="summary">{{ truncatedSummary }}</p>

    <!-- Footer: tags + stats -->
    <div class="card-footer">
      <div class="tags">
        <span class="tag" v-for="tag in (diary.tech_stack || []).slice(0, 3)" :key="tag">
          {{ tag }}
        </span>
        <span class="style-tag">{{ styleLabel }}</span>
      </div>
      <div class="stats">
        <span class="stat-item">
          <span class="stat-label">commits</span>
          <span class="stat-value">{{ diary.commit_count }}</span>
        </span>
        <span class="stat-item text-green-400">+{{ diary.insertions }}</span>
        <span class="stat-item text-red-400">-{{ diary.deletions }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diary-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.3s ease;
  position: relative;
}

.diary-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
}

.diary-card.card-selected {
  border-color: rgba(99, 102, 241, 0.6);
  background: rgba(99, 102, 241, 0.08);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
}

.card-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.delete-btn {
  color: #64748B;
  transition: color 0.2s;
  opacity: 0;
}

.diary-card:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #EF4444 !important;
}

.date-tag {
  display: inline-block;
  padding: 4px 12px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.15));
  border-radius: 20px;
  font-size: 0.8rem;
  color: #A78BFA;
  font-weight: 500;
  width: fit-content;
}

.title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #F8FAFC;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.summary {
  font-size: 0.9rem;
  color: #94A3B8;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.style-tag {
  padding: 2px 8px;
  background: rgba(34, 197, 94, 0.1);
  color: #22C55E;
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 12px;
  font-size: 0.75rem;
}

.stats {
  display: flex;
  gap: 8px;
  font-size: 0.8rem;
  color: #64748B;
}

.stat-item {
  display: flex;
  gap: 4px;
  align-items: center;
}

.stat-label {
  color: #475569;
}

.stat-value {
  color: #CBD5E1;
  font-weight: 600;
}
</style>
