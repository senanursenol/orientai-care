import { createApp } from './src/app.js'
import { appConfig } from './configs/app-config.js'

const app = createApp()

app.listen(appConfig.port, () => {
  console.log(`mentes-service listening on :${appConfig.port}`)
})
