import { appConfig } from '../../../configs/app-config.js'

/**
 * Python AI servisine (mentes-ai-service) giden tüm HTTP çağrılarının tek merkezi.
 * Kontrat (bkz. services/mentes-service/README.md):
 *   POST /api/rag/chat  { patient_id, message } -> { answer, context[] }
 *   POST /api/stt       multipart audio         -> { transcript }
 *   POST /api/tts       { text }                -> { audio_url }
 *
 * AI_MOCK=true iken Python servisi olmadan da Node tarafı uçtan uca test edilebilir.
 */

const isMock = process.env.AI_MOCK === 'true'

async function postJson(path, body) {
  const res = await fetch(`${appConfig.aiServiceUrl}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    throw new Error(`AI service error ${res.status} on ${path}`)
  }

  return res.json()
}

export async function chatWithRag({ patientId, message }) {
  if (isMock) {
    return {
      answer: `(mock) "${message}" mesajına ${patientId} hasta bağlamıyla örnek yanıt.`,
      context: [],
    }
  }

  return postJson('/api/rag/chat', { patient_id: patientId, message })
}

export async function transcribeAudio(audioBuffer, mimetype) {
  if (isMock) {
    return { transcript: '(mock) sesten çevrilen örnek metin' }
  }

  const formData = new FormData()
  formData.append('audio', new Blob([audioBuffer], { type: mimetype }), 'audio')

  const res = await fetch(`${appConfig.aiServiceUrl}/api/stt`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    throw new Error(`AI service error ${res.status} on /api/stt`)
  }

  return res.json()
}

export async function synthesizeSpeech(text) {
  if (isMock) {
    return { audio_url: null }
  }

  return postJson('/api/tts', { text })
}
