export function makeLogInteractionUseCase({ interactionLogRepository }) {
  return async function logInteractionUseCase({ patientId, userInput, response, inputType = 'text', transcription = null }) {
    await interactionLogRepository.saveInteraction({
      patientId,
      userInput,
      response,
      inputType,
      transcription,
    })
  }
}
