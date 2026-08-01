import { appConfig } from '../../../configs/app-config.js'

/**
 * Python AI servisine (mentes-ai-service) giden tüm HTTP çağrılarının tek merkezi.
 * Node, React'in tek konuştuğu kapı; Python AI servisine burada köprü kurulur,
 * React Python'a hiçbir zaman doğrudan istek atmaz.
 *
 * Kontrat (bkz. services/mentes-ai-service/app/api/app.py):
 *   POST /api/chat/text      { text, patient_id }              -> conversation result (RAG-backed)
 *   POST /api/chat/voice      multipart audio + patient_id      -> conversation result + transcript
 *   POST /api/vision/describe multipart image + patient_id      -> { description, model }
 *   POST /api/tts/synthesize  { text }                          -> audio/mpeg (binary)
 *   POST /api/rag/chat        { patient_id, message }           -> { answer, context[] }  (ORI-21 kontratı)
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

async function postFormData(path, formData) {
  const res = await fetch(`${appConfig.aiServiceUrl}${path}`, {
    method: 'POST',
    body: formData,
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

  return postJson('/api/chat/text', { text: message, patient_id: patientId })
}

export async function transcribeAudio(audioBuffer, mimetype, patientId) {
  if (isMock) {
    return {
      transcript: '(mock) sesten çevrilen örnek metin',
      answer: `(mock) sesli mesaja ${patientId} hasta bağlamıyla örnek yanıt.`,
      context: [],
    }
  }

  const formData = new FormData()
  formData.append('audio', new Blob([audioBuffer], { type: mimetype }), 'audio')
  if (patientId) formData.append('patient_id', patientId)

  const result = await postFormData('/api/chat/voice', formData)
  return {
    transcript: result.input,
    answer: result.assistant_response,
    context: [],
  }
}

export async function synthesizeSpeech(text) {
  if (isMock) {
    return { audioBuffer: null, mimetype: null }
  }

  const res = await fetch(`${appConfig.aiServiceUrl}/api/tts/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })

  if (!res.ok) {
    throw new Error(`AI service error ${res.status} on /api/tts/synthesize`)
  }

  const arrayBuffer = await res.arrayBuffer()
  return { audioBuffer: Buffer.from(arrayBuffer), mimetype: res.headers.get('content-type') || 'audio/mpeg' }
}

export async function describePhoto(imageBuffer, mimetype, patientId) {
  if (isMock) {
    return { description: `(mock) ${patientId} hastasının fotoğrafı için örnek açıklama.`, model: 'mock' }
  }

  const formData = new FormData()
  formData.append('image', new Blob([imageBuffer], { type: mimetype }), 'photo')
  if (patientId) formData.append('patient_id', patientId)

  return postFormData('/api/vision/describe', formData)
}
