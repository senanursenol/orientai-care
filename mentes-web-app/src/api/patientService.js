import apiClient from './apiClient'

/**
 * Hasta chat/sohbet/ses/görsel servis katmanı.
 *
 * Node backend (mentes-service) React'in tek konuştuğu kapıdır; AI istekleri
 * (chat, ses, fotoğraf, TTS) burada Python AI servisine köprülenir —
 * bkz. services/mentes-service/routes/{chat,voice-chat,tts,vision}-route.js.
 */

export async function sendPatientMessage(patientId, message) {
  const { data } = await apiClient.post('/chat', { patientId, message })
  return { assistant_response: data.answer, context: data.context }
}

export async function sendPatientVoiceMessage(patientId, audioBlob) {
  const formData = new FormData()
  formData.append('patientId', patientId)
  formData.append('audio', audioBlob)
  const { data } = await apiClient.post('/voice-chat', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return { ai_input: data.transcript, assistant_response: data.answer, context: data.context }
}

export async function describePatientPhoto(patientId, imageFile) {
  const formData = new FormData()
  formData.append('patientId', patientId)
  formData.append('image', imageFile)
  const { data } = await apiClient.post('/vision/describe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return { description: data.description }
}

export async function synthesizePatientSpeech(text, signal) {
  const { data } = await apiClient.post(
    '/tts',
    { text },
    { responseType: 'blob', signal },
  )
  return data
}
