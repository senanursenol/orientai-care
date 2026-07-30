import { Router } from 'express'
import { makeChatUseCase } from '../src/application/chat.use-case.js'
import { makeLogInteractionUseCase } from '../../../core/service-mentes/src/application/use-cases/log-interaction.use-case.js'
import * as aiClient from '../src/infrastructure/ai-client/ai-client.js'
import { pool } from '../src/infrastructure/persistence/db-pool.js'
import { makeInteractionLogRepository } from '../src/infrastructure/persistence/interaction-log.repository.js'

export const chatRouter = Router()

const chatUseCase = makeChatUseCase({ aiClient })
const logInteraction = makeLogInteractionUseCase({
  interactionLogRepository: makeInteractionLogRepository({ pool }),
})

chatRouter.post('/chat', async (req, res) => {
  const { patientId, message } = req.body ?? {}

  try {
    const result = await chatUseCase({ patientId, message })
    res.status(200).json({ status: 'ok', ...result })

    logInteraction({
      patientId,
      userInput: message,
      response: result.answer,
      inputType: 'text',
    }).catch((error) => console.error('[interaction-log] failed:', error.message))
  } catch (error) {
    const isValidationError = /required/.test(error.message)
    res.status(isValidationError ? 400 : 502).json({ status: 'error', message: error.message })
  }
})
