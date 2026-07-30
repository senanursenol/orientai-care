const AI_API_BASE_URL =
  import.meta.env.VITE_AI_API_BASE_URL || 'http://localhost:8000/api'

async function readResponse(response, fallbackMessage) {
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(
      typeof payload?.detail === 'string' ? payload.detail : fallbackMessage,
    )
  }
  return payload
}

export async function analyzePatientText(text) {
  const response = await fetch(`${AI_API_BASE_URL}/chat/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return readResponse(response, 'Mesaja şu anda yanıt oluşturulamadı.')
}

export async function transcribePatientVoice(audioBlob) {
  const extension = audioBlob.type.includes('ogg') ? 'ogg' : 'webm'
  const formData = new FormData()
  formData.append('audio', audioBlob, `patient-voice.${extension}`)

  const response = await fetch(`${AI_API_BASE_URL}/chat/voice`, {
    method: 'POST',
    body: formData,
  })
  return readResponse(response, 'Sesli mesaja şu anda yanıt oluşturulamadı.')
}

export async function describePatientPhoto(imageFile) {
  const formData = new FormData()
  formData.append('image', imageFile, imageFile.name)

  const response = await fetch(`${AI_API_BASE_URL}/vision/describe`, {
    method: 'POST',
    body: formData,
  })
  return readResponse(response, 'Fotoğraf şu anda açıklanamadı.')
}

export async function synthesizePatientSpeech(text, signal) {
  const response = await fetch(`${AI_API_BASE_URL}/tts/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
    signal,
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(
      typeof payload?.detail === 'string'
        ? payload.detail
        : 'Sesli destek şu anda oluşturulamadı.',
    )
  }

  return response.blob()
}
