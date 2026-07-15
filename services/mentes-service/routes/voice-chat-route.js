import { Router } from 'express'
import multer from 'multer'
import { makeVoiceChatUseCase } from '../src/application/voice-chat.use-case.js'
import * as aiClient from '../src/infrastructure/ai-client/ai-client.js'

export const voiceChatRouter = Router()

const upload = multer({ storage: multer.memoryStorage() })
const voiceChatUseCase = makeVoiceChatUseCase({ aiClient })

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
  } catch (error) {
    const isValidationError = /required/.test(error.message)
    res.status(isValidationError ? 400 : 502).json({ status: 'error', message: error.message })
  }
})
