export function makeChatUseCase({ aiClient }) {
  return async function chatUseCase({ patientId, message }) {
    if (!patientId) {
      throw new Error('patientId is required')
    }
    if (!message || !message.trim()) {
      throw new Error('message is required')
    }

    return aiClient.chatWithRag({ patientId, message })
  }
}
