import express from 'express'
import cors from 'cors'
import { appConfig } from '../configs/app-config.js'
import { healthRouter } from '../routes/health-route.js'
import { chatRouter } from '../routes/chat-route.js'
import { voiceChatRouter } from '../routes/voice-chat-route.js'
import { ttsRouter } from '../routes/tts-route.js'
import { visionRouter } from '../routes/vision-route.js'

export function createApp() {
  const app = express()

  app.use(cors({ origin: appConfig.corsOrigin }))
  app.use(express.json())

  app.use('/api', healthRouter)
  app.use('/api', chatRouter)
  app.use('/api', voiceChatRouter)
  app.use('/api', ttsRouter)
  app.use('/api', visionRouter)

  app.use((req, res) => {
    res.status(404).json({ status: 'error', message: 'Not found' })
  })

  return app
}
