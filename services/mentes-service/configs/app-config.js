import 'dotenv/config'

export const appConfig = {
  port: Number(process.env.PORT) || 4100,
  nodeEnv: process.env.NODE_ENV || 'development',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:4200',
}
