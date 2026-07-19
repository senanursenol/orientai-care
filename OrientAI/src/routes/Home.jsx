import { useEffect, useRef, useState } from 'react'
import './Home.css'

const VOICE_API_URL =
  import.meta.env.VITE_VOICE_API_URL || 'http://localhost:8000/api/voice/ask'

function supportedAudioType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
  ]

  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || ''
}

function Home() {
  const [status, setStatus] = useState('idle')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [error, setError] = useState('')

  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const audioRef = useRef(null)

  const stopTracks = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }

  useEffect(() => () => stopTracks(), [])

  const sendAudio = async (audioBlob) => {
    setStatus('processing')
    setError('')

    const extension = audioBlob.type.includes('ogg') ? 'ogg' : 'webm'
    const formData = new FormData()
    formData.append('audio', audioBlob, `question.${extension}`)
    formData.append('patient_id', 'demo-patient')

    try {
      const response = await fetch(VOICE_API_URL, {
        method: 'POST',
        body: formData,
      })

      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(payload.detail || 'Sesli yanıt alınamadı.')
      }

      setQuestion(payload.question)
      setAnswer(payload.answer)

      const nextAudioUrl = `data:${payload.audio_content_type};base64,${payload.audio_base64}`
      setAudioUrl(nextAudioUrl)
      setStatus('ready')

      window.setTimeout(() => {
        audioRef.current?.play().catch(() => {
          // Some browsers require a second user gesture; the play button remains visible.
        })
      }, 0)
    } catch (requestError) {
      setError(requestError.message || 'Beklenmeyen bir hata oluştu.')
      setStatus('error')
    }
  }

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError('Bu tarayıcı mikrofonla ses kaydını desteklemiyor.')
      setStatus('error')
      return
    }

    setError('')
    setQuestion('')
    setAnswer('')
    setAudioUrl('')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = supportedAudioType()
      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined,
      )

      streamRef.current = stream
      recorderRef.current = recorder
      chunksRef.current = []

      recorder.addEventListener('dataavailable', (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      })

      recorder.addEventListener(
        'stop',
        () => {
          const audioBlob = new Blob(chunksRef.current, {
            type: recorder.mimeType || 'audio/webm',
          })
          stopTracks()
          void sendAudio(audioBlob)
        },
        { once: true },
      )

      recorder.start(250)
      setStatus('recording')
    } catch (microphoneError) {
      stopTracks()
      setError(
        microphoneError.name === 'NotAllowedError'
          ? 'Devam etmek için mikrofon izni vermelisiniz.'
          : 'Mikrofon başlatılamadı.',
      )
      setStatus('error')
    }
  }

  const stopRecording = () => {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
    }
  }

  const isRecording = status === 'recording'
  const isProcessing = status === 'processing'

  return (
    <main className="voice-page">
      <section className="voice-card" aria-labelledby="voice-title">
        <div className="brand-mark" aria-hidden="true">O</div>
        <p className="eyebrow">OrientAI Sesli Asistan</p>
        <h1 id="voice-title">Size nasıl yardımcı olabilirim?</h1>
        <p className="intro">
          Düğmeye dokunun, sorunuzu söyleyin ve ardından kaydı bitirin.
        </p>

        <button
          className={`record-button ${isRecording ? 'is-recording' : ''}`}
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          aria-pressed={isRecording}
        >
          <span className="record-icon" aria-hidden="true">
            {isRecording ? '■' : '●'}
          </span>
          <span>
            {isRecording
              ? 'Kaydı bitir'
              : isProcessing
                ? 'Yanıt hazırlanıyor…'
                : 'Konuşmaya başla'}
          </span>
        </button>

        <p className="status-text" role="status" aria-live="polite">
          {isRecording && 'Sizi dinliyorum…'}
          {isProcessing && 'Sorunuz anlaşılıyor ve sesli yanıt hazırlanıyor…'}
          {status === 'ready' && 'Yanıt hazır.'}
          {status === 'idle' && 'Mikrofon şu anda kapalı.'}
        </p>

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        {(question || answer) && (
          <div className="conversation" aria-live="polite">
            <article className="message question-message">
              <span className="message-label">Siz sordunuz</span>
              <p>{question}</p>
            </article>
            <article className="message answer-message">
              <span className="message-label">OrientAI yanıtladı</span>
              <p>{answer}</p>
            </article>
          </div>
        )}

        {audioUrl && (
          <audio ref={audioRef} className="audio-player" controls src={audioUrl}>
            Tarayıcınız ses oynatmayı desteklemiyor.
          </audio>
        )}

        <p className="privacy-note">
          Bu prototip tıbbi tanı veya acil durum hizmeti sunmaz.
        </p>
      </section>
    </main>
  )
}

export default Home
