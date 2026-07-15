import apiClient from './apiClient'

/**
 * Hasta chat/sohbet servis katmanı.
 *
 * ORI-21 (/api/chat) ve ORI-22 (/api/voice-chat) backend'de hazır —
 * bkz. services/mentes-service/routes/{chat,voice-chat}-route.js.
 */

export async function sendPatientMessage(patientId, message) {
  const { data } = await apiClient.post('/chat', { patientId, message })
  return data
}

export async function sendPatientVoiceMessage(patientId, audioBlob) {
  const formData = new FormData()
  formData.append('patientId', patientId)
  formData.append('audio', audioBlob)
  const { data } = await apiClient.post('/voice-chat', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
