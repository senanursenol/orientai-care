import apiClient from './apiClient'

/**
 * Bakım veren (caregiver) dashboard servis katmanı.
 *
 * Sprint 3 kapsamında log, rutin ve duygu-durumu (sentiment) verilerini
 * backend'den çekecek. Şimdilik CaregiverDashboardPage.jsx bu contract'a
 * karşı geliştirilebilir.
 */

export async function getPatientRoutines(patientId) {
  const { data } = await apiClient.get(`/patients/${patientId}/routines`)
  return data
}

export async function getPatientLogs(patientId) {
  const { data } = await apiClient.get(`/patients/${patientId}/logs`)
  return data
}

export async function getPatientSentimentSummary(patientId) {
  const { data } = await apiClient.get(`/patients/${patientId}/sentiment-summary`)
  return data
}
