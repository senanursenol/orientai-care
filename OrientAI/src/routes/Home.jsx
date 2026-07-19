import { useEffect, useRef, useState } from 'react'
import './Home.css'

const VOICE_API_URL =
  import.meta.env.VITE_VOICE_API_URL ||
  'http://localhost:8000/api/voice/transcribe'

const TEXT_API_URL =
  import.meta.env.VITE_TEXT_API_URL ||
  'http://localhost:8000/api/text/analyze'

const SENTIMENT_PRESENTATION = {
  anxious: {
    label: 'Kaygılı',
    description:
      'İçerikte kaygı, korku veya huzursuzluk işaretleri algılandı.',
  },
  negative: {
    label: 'Olumsuz',
    description:
      'İçerikte üzüntü, öfke veya memnuniyetsizlik işaretleri algılandı.',
  },
  neutral: {
    label: 'Sakin / Nötr',
    description:
      'İçerikte belirgin bir olumlu ya da olumsuz duygu algılanmadı.',
  },
  positive: {
    label: 'Olumlu',
    description:
      'İçerikte mutluluk, memnuniyet veya umut işaretleri algılandı.',
  },
  unknown: {
    label: 'Belirsiz',
    description: 'İçeriğin duygusu güvenilir biçimde belirlenemedi.',
  },
}

const SAFETY_PRESENTATION = {
  violent_threat: {
    title: 'Şiddet tehdidi algılandı',
    description:
      'İçerikte başka kişilere veya çevreye zarar verme niyeti bulunuyor olabilir.',
  },
  self_harm: {
    title: 'Kendine zarar riski algılandı',
    description:
      'İçerikte kişinin kendisine zarar verme niyeti bulunuyor olabilir.',
  },
  reported_threat: {
    title: 'Aktarılan risk ifadesi',
    description:
      'Tehdit içeren söz bir alıntı, haber veya kurgu bağlamında aktarılıyor olabilir.',
  },
  unknown: {
    title: 'Güvenlik analizi yapılamadı',
    description: 'İçeriğin güvenlik durumu belirlenemedi.',
  },
}

function supportedAudioType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
  ]

  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || ''
}

function requestError(payload, fallback) {
  if (typeof payload?.detail === 'string') return payload.detail
  return fallback
}

function SentimentCard({ sentiment }) {
  const view =
    SENTIMENT_PRESENTATION[sentiment.label] || SENTIMENT_PRESENTATION.unknown
  const score = Math.round(
    Math.max(0, Math.min(1, Number(sentiment.score) || 0)) * 100,
  )
  const safety = sentiment.safety
  const safetyView =
    safety && safety.label !== 'safe'
      ? SAFETY_PRESENTATION[safety.label] || SAFETY_PRESENTATION.unknown
      : null

  return (
    <article className={`analysis-card sentiment-${sentiment.label}`}>
      <div className="analysis-title-row">
        <div>
          <span className="analysis-kicker">Duygu analizi</span>
          <h2>{view.label}</h2>
        </div>
        <span className="analysis-ready">Analiz tamamlandı</span>
      </div>

      <p className="analysis-description">{view.description}</p>

      {safetyView && (
        <div
          className={`safety-alert ${safety.needs_attention ? 'is-critical' : 'is-reported'}`}
          role={safety.needs_attention ? 'alert' : 'status'}
        >
          <div className="safety-alert-heading">
            <span className="safety-symbol" aria-hidden="true">!</span>
            <div>
              <span className="safety-kicker">Güvenlik analizi</span>
              <strong>{safetyView.title}</strong>
            </div>
          </div>
          <p>{safetyView.description}</p>
          {safety.needs_attention && (
            <span className="safety-action">
              Gecikmeden bir insan tarafından değerlendirilmesi önerilir.
            </span>
          )}
        </div>
      )}

      <div className="analysis-metrics">
        <div className="metric confidence-metric">
          <span className="metric-label">Karar güveni</span>
          <div className="confidence-value-row">
            <strong>%{score}</strong>
            <div
              className="confidence-track"
              role="progressbar"
              aria-label="Karar güveni"
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow={score}
            >
              <span style={{ width: `${score}%` }} />
            </div>
          </div>
        </div>

        <div className="metric">
          <span className="metric-label">Düşük güven</span>
          <strong
            className={`confidence-state ${sentiment.low_confidence ? 'is-low' : 'is-reliable'}`}
          >
            {sentiment.low_confidence ? 'Evet' : 'Hayır'}
          </strong>
        </div>
      </div>

      {sentiment.low_confidence && (
        <p className="analysis-notice warning-notice">
          Sonuç belirsiz olabilir. Kişinin ne hissettiğini kendisine sorarak
          doğrulayın.
        </p>
      )}

      {sentiment.needs_attention && !safety?.needs_attention && (
        <p className="analysis-notice attention-notice">
          Destekleyici, sakin ve yargılamayan bir yaklaşım önerilir.
        </p>
      )}
    </article>
  )
}

function Home() {
  const [draft, setDraft] = useState('')
  const [entries, setEntries] = useState([])
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const textareaRef = useRef(null)
  const threadEndRef = useRef(null)

  const stopTracks = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }

  useEffect(() => () => stopTracks(), [])

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ block: 'nearest' })
  }, [entries])

  const appendEntry = (entry) => {
    setEntries((current) => [
      ...current,
      {
        id: `${Date.now()}-${current.length}`,
        ...entry,
      },
    ])
  }

  const sendText = async () => {
    const text = draft.trim()
    if (!text || status !== 'idle') return

    setStatus('processing-text')
    setError('')
    try {
      const response = await fetch(TEXT_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(
          requestError(payload, 'Metin duygu analizi yapılamadı.'),
        )
      }

      appendEntry({
        source: 'text',
        content: payload.input,
        sentiment: payload.sentiment,
      })
      setDraft('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
    } catch (requestFailure) {
      setError(requestFailure.message || 'Beklenmeyen bir hata oluştu.')
    } finally {
      setStatus('idle')
    }
  }

  const sendAudio = async (audioBlob) => {
    setStatus('processing-voice')
    setError('')

    const extension = audioBlob.type.includes('ogg') ? 'ogg' : 'webm'
    const formData = new FormData()
    formData.append('audio', audioBlob, `voice-input.${extension}`)

    try {
      const response = await fetch(VOICE_API_URL, {
        method: 'POST',
        body: formData,
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(
          requestError(payload, 'Ses kaydı çözümlenemedi.'),
        )
      }

      appendEntry({
        source: 'voice',
        content: payload.ai_input,
        sentiment: payload.sentiment,
        transcription: {
          language: payload.detected_language,
          probability: payload.language_probability,
          duration: payload.input_duration_seconds,
          confidence: payload.transcription_confidence,
          lowConfidence: payload.transcription_low_confidence,
          model: payload.transcription_model,
        },
      })
    } catch (requestFailure) {
      setError(requestFailure.message || 'Beklenmeyen bir hata oluştu.')
    } finally {
      setStatus('idle')
    }
  }

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError('Bu tarayıcı mikrofonla ses kaydını desteklemiyor.')
      return
    }

    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: { ideal: 1 },
          echoCancellation: { ideal: true },
          noiseSuppression: { ideal: true },
          autoGainControl: { ideal: true },
          sampleRate: { ideal: 48000 },
        },
      })
      const mimeType = supportedAudioType()
      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType, audioBitsPerSecond: 64000 } : undefined,
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
          recorderRef.current = null
          stopTracks()
          if (audioBlob.size === 0) {
            setStatus('idle')
            setError('Ses kaydı boş geldi. Lütfen yeniden deneyin.')
            return
          }
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
      setStatus('idle')
    }
  }

  const toggleRecording = () => {
    if (status === 'recording') {
      recorderRef.current?.stop()
      return
    }
    if (status === 'idle') void startRecording()
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    void sendText()
  }

  const handleTextareaKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void sendText()
    }
  }

  const handleDraftChange = (event) => {
    setDraft(event.target.value)
    event.target.style.height = 'auto'
    event.target.style.height = `${Math.min(event.target.scrollHeight, 160)}px`
  }

  const isRecording = status === 'recording'
  const isProcessing = status.startsWith('processing')
  const hasConversation = entries.length > 0

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="OrientAI ana sayfa">
          <span className="brand-symbol" aria-hidden="true">O</span>
          <span className="brand-copy">
            <strong>OrientAI</strong>
            <small>Duygu Analiz Alanı</small>
          </span>
        </a>

        <div className="header-actions">
          <span className="model-status">
            <span className="status-dot" aria-hidden="true" />
            Yanıt modeli kapalı · Analiz modu
          </span>
          {hasConversation && (
            <button
              className="new-chat-button"
              type="button"
              onClick={() => {
                setEntries([])
                setError('')
              }}
              disabled={status !== 'idle'}
            >
              Yeni sohbet
            </button>
          )}
        </div>
      </header>

      <section className={`workspace ${hasConversation ? 'has-thread' : ''}`}>
        {!hasConversation && (
          <div className="welcome" aria-labelledby="welcome-title">
            <div className="welcome-mark" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <p className="welcome-kicker">GÜVENLİ ANALİZ ALANI</p>
            <h1 id="welcome-title">Bugün nasıl hissediyorsunuz?</h1>
            <p>
              Dilerseniz yazın, dilerseniz mikrofon düğmesine basıp konuşun.
              OrientAI içeriği analiz ederek duyguyu ve karar güvenini göstersin.
            </p>
            <div className="capability-list" aria-label="Kullanılabilir girişler">
              <span>Yazılı giriş</span>
              <span>Sesli giriş</span>
              <span>Duygu analizi</span>
            </div>
          </div>
        )}

        {hasConversation && (
          <div className="thread" aria-live="polite">
            {entries.map((entry) => (
              <section className="exchange" key={entry.id}>
                <div className="user-row">
                  <span className={`source-avatar source-${entry.source}`} aria-hidden="true">
                    {entry.source === 'voice' ? <span className="mini-microphone" /> : 'Aa'}
                  </span>
                  <div className="user-message">
                    <span className="message-source">
                      {entry.source === 'voice'
                        ? 'Sesten anlaşılan'
                        : 'Yazdığınız metin'}
                    </span>
                    <p>{entry.content}</p>
                    {entry.transcription && (
                      <div className="transcription-details">
                        <span>Dil: {entry.transcription.language.toUpperCase()}</span>
                        <span>{entry.transcription.duration.toFixed(1)} sn</span>
                        <span>
                          STT güveni %{Math.round((entry.transcription.confidence ?? entry.transcription.probability) * 100)}
                        </span>
                        <span>Model: {entry.transcription.model || 'Whisper'}</span>
                      </div>
                    )}
                    {entry.transcription?.lowConfidence && (
                      <p className="transcription-warning">
                        Bazı kelimeler yanlış anlaşılmış olabilir. Metni kontrol edin;
                        gerekirse yazılı olarak düzeltin.
                      </p>
                    )}
                  </div>
                </div>

                <div className="analysis-row">
                  <span className="analysis-avatar" aria-hidden="true">O</span>
                  <SentimentCard sentiment={entry.sentiment} />
                </div>
              </section>
            ))}
            <div ref={threadEndRef} />
          </div>
        )}

        <div className="composer-zone">
          {error && (
            <div className="composer-error" role="alert">
              {error}
            </div>
          )}

          <form className={`composer ${isRecording ? 'is-recording' : ''}`} onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="message-input">
              Analiz edilecek metin
            </label>
            <textarea
              id="message-input"
              ref={textareaRef}
              value={draft}
              onChange={handleDraftChange}
              onKeyDown={handleTextareaKeyDown}
              placeholder={isRecording ? 'Sizi dinliyorum…' : 'Bir şeyler yazın veya sesli anlatın…'}
              rows="1"
              maxLength="2000"
              disabled={isRecording || isProcessing}
            />

            <div className="composer-footer">
              <div className="voice-control">
                <button
                  className={`microphone-button ${isRecording ? 'is-active' : ''}`}
                  type="button"
                  onClick={toggleRecording}
                  disabled={isProcessing}
                  aria-label={isRecording ? 'Ses kaydını bitir' : 'Sesli giriş başlat'}
                  aria-pressed={isRecording}
                >
                  <span className="microphone-shape" aria-hidden="true" />
                </button>
                <span className="composer-status" role="status" aria-live="polite">
                  {isRecording && 'Dinliyorum · Bitirmek için mikrofona dokunun'}
                  {status === 'processing-voice' && 'Ses çözümleniyor ve analiz ediliyor…'}
                  {status === 'processing-text' && 'Metin analiz ediliyor…'}
                  {status === 'idle' && 'Sesli giriş'}
                </span>
              </div>

              <button
                className="send-button"
                type="submit"
                disabled={!draft.trim() || status !== 'idle'}
                aria-label="Metni analiz et"
              >
                <span aria-hidden="true">↑</span>
              </button>
            </div>
          </form>

          <p className="disclaimer">
            Sonuçlar yazılı içeriğe dayalı tahmindir; tıbbi veya klinik değerlendirme değildir.
          </p>
        </div>
      </section>
    </main>
  )
}

export default Home
