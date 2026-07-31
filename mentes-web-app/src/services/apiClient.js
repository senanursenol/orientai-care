import axios from 'axios'

/**
 * Merkezi API client.
 *
 * Backend base URL'i .env dosyasından okunur (bkz. .env.example).
 * Node.js/Express backend'i henüz hazır olmasa bile frontend bu
 * client üzerinden geliştirilebilir; backend hazır olduğunda sadece
 * VITE_API_BASE_URL güncellenir.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// İleride auth token eklemek için hazır interceptor iskeleti
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('orientai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Ortak hata loglama - ileride toast/error UI entegrasyonu buraya bağlanabilir
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error?.response?.status, error?.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
