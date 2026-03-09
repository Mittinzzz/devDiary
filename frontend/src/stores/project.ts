import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, ProjectStats } from '@/types'
import { fetchProjects, createProject, fetchProjectStats, deleteProject } from '@/api'

export const useProjectStore = defineStore('project', () => {
  // State
  const projects = ref<Project[]>([])
  const currentStats = ref<ProjectStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const hasProjects = computed(() => projects.value.length > 0)
  const projectOptions = computed(() =>
    projects.value.map((p) => ({ label: p.name, value: p.id }))
  )

  // Actions
  async function loadProjects() {
    loading.value = true
    error.value = null
    try {
      projects.value = await fetchProjects()
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message
    } finally {
      loading.value = false
    }
  }

  async function addProject(data: { name: string; repo_path: string; description?: string }) {
    loading.value = true
    error.value = null
    try {
      const project = await createProject(data)
      projects.value.unshift(project)
      return project
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function removeProject(id: number) {
    await deleteProject(id)
    projects.value = projects.value.filter((p) => p.id !== id)
  }

  async function loadProjectStats(id: number) {
    loading.value = true
    error.value = null
    try {
      currentStats.value = await fetchProjectStats(id)
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message
    } finally {
      loading.value = false
    }
  }

  return {
    projects,
    currentStats,
    loading,
    error,
    hasProjects,
    projectOptions,
    loadProjects,
    addProject,
    removeProject,
    loadProjectStats,
  }
})
