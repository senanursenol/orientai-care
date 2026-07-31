import apiClient from './apiClient'

/**
 * Backend health-check endpoint'ini çağırır.
 * Backend Sprint 1 kapsamında hazırlanan `/health` endpoint'i ile eşleşir.
 */
export async function checkBackendHealth() {
  const { data } = await apiClient.get('/health')
  return data
}
