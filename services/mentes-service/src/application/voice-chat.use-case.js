export function makeVoiceChatUseCase({ aiClient }) {
  return async function voiceChatUseCase({ patientId, audioBuffer, mimetype }) {
    if (!patientId) {
      throw new Error('patientId is required')
    }
    if (!audioBuffer || audioBuffer.length === 0) {
      throw new Error('audio file is required')
    }

    // Python /api/chat/voice tek istekte STT + RAG + LLM + safety zincirini yapar.
    const { transcript, answer, context } = await aiClient.transcribeAudio(audioBuffer, mimetype, patientId)

    return { transcript, answer, context }
  }
}
