export function makeInteractionLogRepository({ pool }) {
  return {
    async saveInteraction({ patientId, userInput, response, inputType = 'text', transcription = null }) {
      await pool.query(
        `INSERT INTO interaction_logs
          (patient_id, input_type, user_input, response, transcription)
         VALUES ($1, $2, $3, $4, $5)`,
        [patientId, inputType, userInput, response, transcription],
      )
    },
  }
}
