import { Router } from 'express'

export const healthRouter = Router()

healthRouter.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    service: 'mentes-service',
    timestamp: new Date().toISOString(),
  })
})
