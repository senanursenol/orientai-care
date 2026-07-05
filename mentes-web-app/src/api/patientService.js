import apiClient from './apiClient'

/**
 * Hasta chat/sohbet servis katmanı.
 *
 * Sprint 2 kapsamında Whisper STT + RAG destekli chat endpoint'i
 * backend'de hazırlandığında bu fonksiyonlar gerçek isteklere bağlanacak.
 * Şu an sadece arayüzü (contract) tanımlıyoruz ki PatientChatPage.jsx
 * bu servise karşı geliştirilebilsin.
 */

export async function sendPatientMessage(patientId, message) {
  const { data } = await apiClient.post(`/patients/${patientId}/chat`, { message })
  return data
}

export async function sendPatientVoiceMessage(patientId, audioBlob) {
  const formData = new FormData()
  formData.append('audio', audioBlob)
  const { data } = await apiClient.post(`/patients/${patientId}/chat/voice`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
