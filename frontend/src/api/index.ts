import axios from 'axios'
import type {
  Diary,
  DiaryListResponse,
  DiaryUpdate,
  Project,
  StatsOverview,
  GenerateParams,
  ProjectStats,
  CommitTrendResponse,
  HeatmapResponse,
  InsightsResponse,
  SettingsResponse,
  SettingsUpdate,
  BatchDeleteResponse,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Request failed'
    console.error('API Error:', message)
    return Promise.reject(error)
  }
)

// ---- Diaries API ----

export async function fetchDiaries(params?: {
  page?: number
  page_size?: number
  style?: string
  project_id?: number
  date_from?: string
  date_to?: string
  search?: string
}): Promise<DiaryListResponse> {
  const { data } = await api.get('/diaries', { params })
  return data
}

export async function fetchDiary(id: number): Promise<Diary> {
  const { data } = await api.get(`/diaries/${id}`)
  return data
}

export async function generateDiary(params: GenerateParams): Promise<{
  diary: Diary
  files_saved: string[]
  tokens_used: number
  message: string
}> {
  const { data } = await api.post('/diaries/generate', params)
  return data
}

export async function deleteDiary(id: number): Promise<void> {
  await api.delete(`/diaries/${id}`)
}

export async function updateDiary(id: number, data: DiaryUpdate): Promise<Diary> {
  const { data: result } = await api.put(`/diaries/${id}`, data)
  return result
}

export async function batchDeleteDiaries(ids: number[]): Promise<BatchDeleteResponse> {
  const { data } = await api.post('/diaries/batch-delete', { ids })
  return data
}

export async function exportDiary(id: number, format: 'markdown' | 'html' = 'markdown'): Promise<string> {
  const { data } = await api.get(`/diaries/${id}/export`, {
    params: { format },
    responseType: 'text',
  })
  return data
}

export async function fetchOverview(): Promise<StatsOverview> {
  const { data } = await api.get('/diaries/overview')
  return data
}

// ---- Projects API ----

export async function fetchProjects(): Promise<Project[]> {
  const { data } = await api.get('/projects')
  return data
}

export async function createProject(params: {
  name: string
  repo_path: string
  description?: string
}): Promise<Project> {
  const { data } = await api.post('/projects', params)
  return data
}

export async function fetchProject(id: number): Promise<Project> {
  const { data } = await api.get(`/projects/${id}`)
  return data
}

export async function deleteProject(id: number): Promise<void> {
  await api.delete(`/projects/${id}`)
}

export async function fetchProjectStats(id: number): Promise<ProjectStats> {
  const { data } = await api.get(`/projects/${id}/stats`)
  return data
}

// ---- Stats API ----

export async function fetchCommitTrend(days: number = 30): Promise<CommitTrendResponse> {
  const { data } = await api.get('/stats/commit-trend', { params: { days } })
  return data
}

export async function fetchHeatmap(days: number = 90): Promise<HeatmapResponse> {
  const { data } = await api.get('/stats/heatmap', { params: { days } })
  return data
}

export async function fetchInsights(): Promise<InsightsResponse> {
  const { data } = await api.get('/stats/insights')
  return data
}

// ---- Settings API ----

export async function fetchSettings(): Promise<SettingsResponse> {
  const { data } = await api.get('/settings')
  return data
}

export async function updateSettings(data: SettingsUpdate): Promise<SettingsResponse> {
  const { data: result } = await api.put('/settings', data)
  return result
}

// ---- Health ----

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const { data } = await api.get('/health')
  return data
}

export default api
