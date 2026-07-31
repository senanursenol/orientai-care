import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'

const isWindows = process.platform === 'win32'
const pythonCommand = isWindows ? 'python' : 'python3'

function runNpmScript(scriptName) {
  if (isWindows) {
    return spawn(
      process.env.ComSpec || 'C:\\Windows\\System32\\cmd.exe',
      ['/d', '/s', '/c', `npm run ${scriptName}`],
      {
        stdio: 'inherit',
        shell: false,
      },
    )
  }

  return spawn('npm', ['run', scriptName], {
    stdio: 'inherit',
    shell: false,
  })
}

function runAiApi() {
  const envFile = existsSync('.env') ? '.env' : '.env.example'

  return spawn(
    pythonCommand,
    [
      '-m',
      'uvicorn',
      'ai_api:app',
      '--reload',
      '--port',
      '8000',
      '--env-file',
      envFile,
    ],
    {
      stdio: 'inherit',
      shell: false,
    },
  )
}

const apiOnly = process.argv.includes('--api-only')
const children = apiOnly ? [runAiApi()] : [runNpmScript('dev:web'), runAiApi()]

let stopping = false

function stopAll(exitCode = 0) {
  if (stopping) return
  stopping = true

  for (const child of children) {
    if (!child.killed) child.kill()
  }
  process.exitCode = exitCode
}

for (const child of children) {
  child.on('error', (error) => {
    console.error(error.message)
    stopAll(1)
  })
  child.on('exit', (code, signal) => {
    if (!stopping && signal === null && code !== 0) stopAll(code || 1)
  })
}

process.on('SIGINT', () => stopAll(0))
process.on('SIGTERM', () => stopAll(0))
