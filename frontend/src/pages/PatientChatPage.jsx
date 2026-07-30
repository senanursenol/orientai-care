import { useEffect, useRef, useState } from 'react'
import {
  analyzePatientText,
  describePatientPhoto,
  synthesizePatientSpeech,
  transcribePatientVoice,
} from '../services/aiService'
import './PatientChatPage.css'

function supportedAudioType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
  ]
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || ''
}

function PatientChatPage() {
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [voiceSupportEnabled, setVoiceSupportEnabled] = useState(true)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [speechError, setSpeechError] = useState('')

  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const fileInputRef = useRef(null)
  const threadEndRef = useRef(null)
  const previewUrlsRef = useRef([])
  const voiceSupportRef = useRef(true)
  const speechAbortRef = useRef(null)
  const speechAudioRef = useRef(null)
  const speechUrlRef = useRef(null)

  const stopTracks = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }

  const stopSpeech = () => {
    speechAbortRef.current?.abort()
    speechAbortRef.current = null

    if (speechAudioRef.current) {
      speechAudioRef.current.pause()
      speechAudioRef.current.currentTime = 0
      speechAudioRef.current = null
    }

    if (speechUrlRef.current) {
      URL.revokeObjectURL(speechUrlRef.current)
      speechUrlRef.current = null
    }

    setIsSpeaking(false)
  }

  const speakAssistantText = async (text) => {
    if (!voiceSupportRef.current || !text.trim()) return

    stopSpeech()
    setSpeechError('')
    setIsSpeaking(true)

    const controller = new AbortController()
    speechAbortRef.current = controller

    try {
      const audioBlob = await synthesizePatientSpeech(text, controller.signal)
      if (controller.signal.aborted || !voiceSupportRef.current) return

      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      speechUrlRef.current = audioUrl
      speechAudioRef.current = audio

      audio.addEventListener(
        'ended',
        () => {
          if (speechAudioRef.current === audio) {
            speechAudioRef.current = null
            URL.revokeObjectURL(audioUrl)
            speechUrlRef.current = null
            setIsSpeaking(false)
          }
        },
        { once: true },
      )
      audio.addEventListener(
        'error',
        () => {
          setSpeechError('Ses oynatılamadı. Lütfen ses çıkışınızı kontrol edin.')
          stopSpeech()
        },
        { once: true },
      )

      await audio.play()
    } catch (speechFailure) {
      if (speechFailure.name !== 'AbortError') {
        setSpeechError(
          speechFailure.name === 'NotAllowedError'
            ? 'Tarayıcı otomatik sesi engelledi. Sesli desteği kapatıp yeniden açın.'
            : speechFailure.message || 'Sesli destek oluşturulamadı.',
        )
      }
      stopSpeech()
    } finally {
      if (speechAbortRef.current === controller) {
        speechAbortRef.current = null
      }
    }
  }

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, status])

  useEffect(
    () => () => {
      stopTracks()
      stopSpeech()
      previewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url))
    },
    [],
  )

  const appendMessages = (...newMessages) => {
    setMessages((current) => [
      ...current,
      ...newMessages.map((message, index) => ({
        id: `${Date.now()}-${current.length}-${index}`,
        ...message,
      })),
    ])
  }

  const sendText = async () => {
    const text = draft.trim()
    if (!text || status !== 'idle') return

    setDraft('')
    setError('')
    setStatus('text')
    appendMessages({ role: 'user', kind: 'text', text })

    try {
      const result = await analyzePatientText(text)
      const assistantText = result.assistant_response
      appendMessages({
        role: 'assistant',
        kind: 'response',
        text: assistantText,
      })
      void speakAssistantText(assistantText)
    } catch (requestError) {
      setError(requestError.message || 'Beklenmeyen bir hata oluştu.')
    } finally {
      setStatus('idle')
    }
  }

  const sendAudio = async (audioBlob) => {
    setError('')
    setStatus('voice')

    try {
      const result = await transcribePatientVoice(audioBlob)
      const assistantText = result.assistant_response
      appendMessages(
        {
          role: 'user',
          kind: 'voice',
          text: result.ai_input,
          meta: 'Ses kaydından yazıya çevrildi',
        },
        {
          role: 'assistant',
          kind: 'response',
          text: assistantText,
        },
      )
      void speakAssistantText(assistantText)
    } catch (requestError) {
      setError(requestError.message || 'Ses kaydı işlenemedi.')
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

          if (!audioBlob.size) {
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
      setStatus('idle')
      setError(
        microphoneError.name === 'NotAllowedError'
          ? 'Devam etmek için mikrofon izni vermelisiniz.'
          : 'Mikrofon başlatılamadı.',
      )
    }
  }

  const toggleRecording = () => {
    if (status === 'recording') {
      recorderRef.current?.stop()
    } else if (status === 'idle') {
      void startRecording()
    }
  }

  const handlePhoto = async (event) => {
    const image = event.target.files?.[0]
    event.target.value = ''
    if (!image || status !== 'idle') return

    if (!image.type.startsWith('image/')) {
      setError('Lütfen bir fotoğraf dosyası seçin.')
      return
    }
    if (image.size > 10 * 1024 * 1024) {
      setError('Fotoğraf 10 MB’tan küçük olmalıdır.')
      return
    }

    const previewUrl = URL.createObjectURL(image)
    previewUrlsRef.current.push(previewUrl)
    setError('')
    setStatus('image')
    appendMessages({
      role: 'user',
      kind: 'image',
      text: image.name,
      imageUrl: previewUrl,
    })

    try {
      const result = await describePatientPhoto(image)
      appendMessages({
        role: 'assistant',
        kind: 'vision',
        text: result.description,
        meta: 'Fotoğraf açıklaması',
      })
      void speakAssistantText(result.description)
    } catch (requestError) {
      setError(requestError.message || 'Fotoğraf açıklanamadı.')
    } finally {
      setStatus('idle')
    }
  }

  const clearConversation = () => {
    stopSpeech()
    previewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url))
    previewUrlsRef.current = []
    setMessages([])
    setError('')
    setSpeechError('')
  }

  const toggleVoiceSupport = () => {
    const nextValue = !voiceSupportEnabled
    voiceSupportRef.current = nextValue
    setVoiceSupportEnabled(nextValue)
    setSpeechError('')

    if (!nextValue) stopSpeech()
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    void sendText()
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void sendText()
    }
  }

  const isBusy = status !== 'idle' && status !== 'recording'
  const statusText = {
    idle: 'Mesajınızı yazın veya bir giriş türü seçin',
    recording: 'Dinliyorum… Bitirmek için mikrofona yeniden basın',
    voice: 'Ses çözümleniyor ve yanıt hazırlanıyor…',
    image: 'Fotoğraf inceleniyor…',
    text: 'Mesajınız için yanıt hazırlanıyor…',
  }[status]

  return (
    <section className="patient-chat">
      <div className="patient-chat__frame">
        <header className="patient-chat__intro">
          <div>
            <span className="patient-chat__eyebrow">ORIENTAI HASTA ASİSTANI</span>
            <h1>Size nasıl yardımcı olabilirim?</h1>
            <p>Yazabilir, konuşabilir veya hatırlamak istediğiniz bir fotoğrafı paylaşabilirsiniz.</p>
          </div>
          {messages.length > 0 && (
            <button
              className="patient-chat__clear"
              type="button"
              onClick={clearConversation}
              disabled={status !== 'idle'}
            >
              Yeni sohbet
            </button>
          )}
        </header>

        <div className="patient-chat__thread" aria-live="polite">
          {messages.length === 0 ? (
            <div className="patient-chat__empty">
              <div className="patient-chat__mark" aria-hidden="true">O</div>
              <p>Buradayım. Aklınızdaki bir şeyi anlatmakla başlayabilirsiniz.</p>
              <div>
                <span>Yazılı mesaj</span>
                <span>Sesli anlatım</span>
                <span>Fotoğraf açıklama</span>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <article
                className={`chat-message chat-message--${message.role}`}
                key={message.id}
              >
                <div className="chat-message__avatar" aria-hidden="true">
                  {message.role === 'assistant' ? 'O' : 'S'}
                </div>
                <div className="chat-message__content">
                  {message.imageUrl && (
                    <img src={message.imageUrl} alt="Kullanıcının yüklediği fotoğraf" />
                  )}
                  {message.meta && <span>{message.meta}</span>}
                  <p>{message.text}</p>
                </div>
              </article>
            ))
          )}

          {isBusy && (
            <div className="patient-chat__thinking" role="status">
              <span />
              <span />
              <span />
              {statusText}
            </div>
          )}
          <div ref={threadEndRef} />
        </div>

        <div className="patient-chat__composer-wrap">
          {error && <p className="patient-chat__error" role="alert">{error}</p>}

          <form
            className={`patient-chat__composer ${status === 'recording' ? 'is-recording' : ''}`}
            onSubmit={handleSubmit}
          >
            <textarea
              rows="1"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Mesajınızı yazın…"
              aria-label="Hasta mesajı"
              disabled={isBusy}
            />

            <div className="patient-chat__actions">
              <div>
                <button
                  className="composer-icon-button"
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={status !== 'idle'}
                  aria-label="Fotoğraf yükle ve açıkla"
                  title="Fotoğraf yükle"
                >
                  <span className="image-icon" aria-hidden="true" />
                </button>
                <input
                  ref={fileInputRef}
                  className="sr-only"
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                  onChange={handlePhoto}
                  tabIndex="-1"
                />

                <button
                  className={`composer-icon-button ${status === 'recording' ? 'is-active' : ''}`}
                  type="button"
                  onClick={toggleRecording}
                  disabled={isBusy}
                  aria-label={status === 'recording' ? 'Ses kaydını bitir' : 'Ses kaydet'}
                  title="Sesli mesaj"
                >
                  <span className="speaker-icon" aria-hidden="true" />
                </button>
              </div>

              <span className="patient-chat__status">{statusText}</span>

              <button
                className="composer-send-button"
                type="submit"
                disabled={!draft.trim() || status !== 'idle'}
                aria-label="Mesajı gönder"
              >
                ↑
              </button>
            </div>
          </form>

          <div className="voice-support">
            <label className="voice-support__control">
              <input
                type="checkbox"
                checked={voiceSupportEnabled}
                onChange={toggleVoiceSupport}
              />
              <span className="voice-support__switch" aria-hidden="true">
                <span />
              </span>
              <span className="voice-support__label">Sesli destek</span>
            </label>
            <span className="voice-support__state" role="status">
              {isSpeaking
                ? 'Yanıt okunuyor…'
                : voiceSupportEnabled
                  ? 'Açık'
                  : 'Kapalı'}
            </span>
          </div>

          {speechError && (
            <p className="voice-support__error" role="alert">{speechError}</p>
          )}

          <p className="patient-chat__disclaimer">
            OrientAI destek amaçlıdır; tıbbi tanı veya acil durum hizmeti değildir.
          </p>
        </div>
      </div>
    </section>
  )
}

export default PatientChatPage
