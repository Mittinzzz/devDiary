/** Diary record */
export interface Diary {
  id: number
  title: string
  content: string
  summary: string
  style: 'diary' | 'blog' | 'report'
  date_from: string
  date_to: string
  project_id: number
  project_name: string
  tech_stack: string[]
  commit_count: number
  insertions: number
  deletions: number
  ai_provider: string
  ai_model: string
  tokens_used: number
  created_at: string
}

/** Diary list response with pagination */
export interface DiaryListResponse {
  items: Diary[]
  total: number
  page: number
  page_size: number
}

/** Project record */
export interface Project {
  id: number
  name: string
  repo_path: string
  description: string
  last_scanned: string | null
  total_commits: number
  languages: Record<string, number>
  created_at: string
}

/** Generate diary request params */
export interface GenerateParams {
  project_id: number
  date_from?: string
  date_to?: string
  style?: 'diary' | 'blog' | 'report'
  output_format?: 'markdown' | 'html' | 'both'
}

/** Stats overview */
export interface StatsOverview {
  total_diaries: number
  total_commits: number
  total_projects: number
  total_insertions: number
  total_deletions: number
  this_week_diaries: number
  this_week_commits: number
  recent_diaries: Diary[]
}

/** Language distribution */
export interface LanguageStats {
  language: string
  count: number
  percentage: number
  color: string
}

/** Commit activity for heatmap */
export interface CommitActivity {
  date: string
  count: number
  hour?: number
  day_of_week?: number
}

/** Project stats */
export interface ProjectStats {
  project: Project
  language_distribution: LanguageStats[]
  commit_trend: CommitActivity[]
  recent_commits: CommitInfo[]
}

/** Commit information */
export interface CommitInfo {
  hash: string
  author: string
  date: string
  message: string
  insertions: number
  deletions: number
  files_changed: number
}

/** Commit trend item for stats chart */
export interface CommitTrendItem {
  date: string
  commit_count: number
  insertions: number
  deletions: number
}

/** Commit trend API response */
export interface CommitTrendResponse {
  items: CommitTrendItem[]
}

/** Heatmap item for stats chart */
export interface HeatmapItem {
  hour: number
  day_of_week: number
  count: number
}

/** Heatmap API response */
export interface HeatmapResponse {
  items: HeatmapItem[]
}

/** Insights API response */
export interface InsightsResponse {
  most_active_hour: string
  most_active_day: string
  most_active_project: string
  current_streak: number
  total_diaries: number
  this_month_commits: number
}

/** Diary update request */
export interface DiaryUpdate {
  title?: string
  content?: string
  summary?: string
  style?: 'diary' | 'blog' | 'report'
}

/** Settings response from API */
export interface SettingsResponse {
  ai_provider: string
  api_key_masked: string
  model: string
  base_url: string
  repos: string[]
  output_dir: string
  output_format: 'markdown' | 'html' | 'both'
  output_style: 'diary' | 'blog' | 'report'
}

/** Settings update request */
export interface SettingsUpdate {
  ai_provider?: string
  api_key?: string
  model?: string
  base_url?: string
  output_dir?: string
  output_format?: 'markdown' | 'html' | 'both'
  output_style?: 'diary' | 'blog' | 'report'
}

/** Batch delete response */
export interface BatchDeleteResponse {
  deleted_count: number
}
