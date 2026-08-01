import { Router } from 'express'
import multer from 'multer'
import * as aiClient from '../src/infrastructure/ai-client/ai-client.js'

export const visionRouter = Router()

const upload = multer({ storage: multer.memoryStorage() })

visionRouter.post('/vision/describe', upload.single('image'), async (req, res) => {
  const { patientId } = req.body ?? {}
  const imageFile = req.file

  if (!imageFile) {
    res.status(400).json({ status: 'error', message: 'image file is required' })
    return
  }

  try {
    const result = await aiClient.describePhoto(imageFile.buffer, imageFile.mimetype, patientId)
    res.status(200).json({ status: 'ok', ...result })
  } catch (error) {
    res.status(502).json({ status: 'error', message: error.message })
  }
})
