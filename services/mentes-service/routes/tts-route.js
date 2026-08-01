import { Router } from 'express'
import * as aiClient from '../src/infrastructure/ai-client/ai-client.js'

export const ttsRouter = Router()

ttsRouter.post('/tts', async (req, res) => {
  const { text } = req.body ?? {}

  if (!text || !text.trim()) {
    res.status(400).json({ status: 'error', message: 'text is required' })
    return
  }

  try {
    const { audioBuffer, mimetype } = await aiClient.synthesizeSpeech(text)
    if (!audioBuffer) {
      res.status(200).json({ status: 'ok', audioBuffer: null })
      return
    }
    res.status(200).set('Content-Type', mimetype).send(audioBuffer)
  } catch (error) {
    res.status(502).json({ status: 'error', message: error.message })
  }
})
