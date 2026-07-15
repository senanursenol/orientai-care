import { makeChatUseCase } from './chat.use-case.js'

export function makeVoiceChatUseCase({ aiClient }) {
  const chatUseCase = makeChatUseCase({ aiClient })

  return async function voiceChatUseCase({ patientId, audioBuffer, mimetype }) {
    if (!patientId) {
      throw new Error('patientId is required')
    }
    if (!audioBuffer || audioBuffer.length === 0) {
      throw new Error('audio file is required')
    }

    const { transcript } = await aiClient.transcribeAudio(audioBuffer, mimetype)
    const { answer, context } = await chatUseCase({ patientId, message: transcript })
    const { audio_url: audioUrl } = await aiClient.synthesizeSpeech(answer)

    return { transcript, answer, context, audioUrl }
  }
}
