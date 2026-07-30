import { Router } from 'express'
import multer from 'multer'
import { makeVoiceChatUseCase } from '../src/application/voice-chat.use-case.js'
import { makeLogInteractionUseCase } from '../../../core/service-mentes/src/application/use-cases/log-interaction.use-case.js'
import * as aiClient from '../src/infrastructure/ai-client/ai-client.js'
import { pool } from '../src/infrastructure/persistence/db-pool.js'
import { makeInteractionLogRepository } from '../src/infrastructure/persistence/interaction-log.repository.js'

export const voiceChatRouter = Router()

const upload = multer({ storage: multer.memoryStorage() })
const voiceChatUseCase = makeVoiceChatUseCase({ aiClient })
const logInteraction = makeLogInteractionUseCase({
  interactionLogRepository: makeInteractionLogRepository({ pool }),
})

voiceChatRouter.post('/voice-chat', upload.single('audio'), async (req, res) => {
  const { patientId } = req.body ?? {}
  const audioFile = req.file

  try {
    const result = await voiceChatUseCase({
      patientId,
      audioBuffer: audioFile?.buffer,
      mimetype: audioFile?.mimetype,
    })
    res.status(200).json({ status: 'ok', ...result })

    logInteraction({
      patientId,
      userInput: result.transcript,
      response: result.answer,
      inputType: 'voice',
      transcription: result.transcript,
    }).catch((error) => console.error('[interaction-log] failed:', error.message))
  } catch (error) {
    const isValidationError = /required/.test(error.message)
    res.status(isValidationError ? 400 : 502).json({ status: 'error', message: error.message })
  }
})
