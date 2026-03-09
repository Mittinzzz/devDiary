import { ref, type Ref } from 'vue'

interface UseApiReturn<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  execute: (...args: any[]) => Promise<T | null>
}

export function useApi<T>(
  apiFn: (...args: any[]) => Promise<T>
): UseApiReturn<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute(...args: any[]): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await apiFn(...args)
      data.value = result
      return result
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Unknown error'
      return null
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
