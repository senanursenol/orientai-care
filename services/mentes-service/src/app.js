import express from 'express'
import cors from 'cors'
import { appConfig } from '../configs/app-config.js'
import { healthRouter } from '../routes/health-route.js'

export function createApp() {
  const app = express()

  app.use(cors({ origin: appConfig.corsOrigin }))
  app.use(express.json())

  app.use('/api', healthRouter)

  app.use((req, res) => {
    res.status(404).json({ status: 'error', message: 'Not found' })
  })

  return app
}
