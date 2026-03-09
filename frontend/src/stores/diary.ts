import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Diary, DiaryListResponse, GenerateParams, StatsOverview } from '@/types'
import { fetchDiaries, fetchDiary, generateDiary, fetchOverview, deleteDiary } from '@/api'

export const useDiaryStore = defineStore('diary', () => {
  // State
  const diaries = ref<Diary[]>([])
  const currentDiary = ref<Diary | null>(null)
  const overview = ref<StatsOverview | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const generating = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const hasDiaries = computed(() => diaries.value.length > 0)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  // Actions
  async function loadDiaries(params?: {
    page?: number
    page_size?: number
    style?: string
    project_id?: number
    date_from?: string
    date_to?: string
    search?: string
  }) {
    loading.value = true
    error.value = null
    try {
      const result: DiaryListResponse = await fetchDiaries({
        page: params?.page || page.value,
        page_size: params?.page_size || pageSize.value,
        ...params,
      })
      diaries.value = result.items
      total.value = result.total
      page.value = result.page
      pageSize.value = result.page_size
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message
    } finally {
      loading.value = false
    }
  }

  async function loadDiary(id: number) {
    loading.value = true
    error.value = null
    try {
      currentDiary.value = await fetchDiary(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message
    } finally {
      loading.value = false
    }
  }

  async function generate(params: GenerateParams) {
    generating.value = true
    error.value = null
    try {
      const result = await generateDiary(params)
      // Prepend the new diary to the list
      diaries.value.unshift(result.diary)
      total.value += 1
      return result
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      generating.value = false
    }
  }

  async function removeDiary(id: number) {
    await deleteDiary(id)
    diaries.value = diaries.value.filter((d) => d.id !== id)
    total.value -= 1
  }

  async function loadOverview() {
    loading.value = true
    try {
      overview.value = await fetchOverview()
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message
    } finally {
      loading.value = false
    }
  }

  return {
    diaries,
    currentDiary,
    overview,
    total,
    page,
    pageSize,
    loading,
    generating,
    error,
    hasDiaries,
    totalPages,
    loadDiaries,
    loadDiary,
    generate,
    removeDiary,
    loadOverview,
  }
})
