import { ref } from 'vue'

// Pomoćnik za dohvat podataka s ISPRAVNA TRI STANJA: loading / error / data.
// Korištenje:  const { data, loading, error, load } = useLoader(() => api.pozovi())
export function useLoader(fetcher) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref('')

  async function load() {
    loading.value = true
    error.value = ''
    try {
      data.value = await fetcher()
    } catch (e) {
      error.value = e.message || 'Došlo je do greške.'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, load }
}
