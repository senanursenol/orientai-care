import { Router } from 'express'
import { makeChatUseCase } from '../src/application/chat.use-case.js'
import * as aiClient from '../src/infrastructure/ai-client/ai-client.js'

export const chatRouter = Router()

const chatUseCase = makeChatUseCase({ aiClient })

chatRouter.post('/chat', async (req, res) => {
  const { patientId, message } = req.body ?? {}

  try {
    const result = await chatUseCase({ patientId, message })
    res.status(200).json({ status: 'ok', ...result })
  } catch (error) {
    const isValidationError = /required/.test(error.message)
    res.status(isValidationError ? 400 : 502).json({ status: 'error', message: error.message })
  }
})
