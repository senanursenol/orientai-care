import { useEffect, useRef, useState } from 'react'
import { sendPatientMessage } from '../api/patientService'
import './PatientChatPage.css'

/**
 * Hasta sohbet ekranı (ORI-59).
 *
 * Backend kontratı (services/mentes-service/routes/chat-route.js):
 *   POST /chat { patientId, message } -> { answer, context[] }
 * Bu ekran src/api/patientService.js -> sendPatientMessage() üzerinden konuşur.
 * Backend ayakta değilse ekran çökmez; bir hata balonu gösterir.
 *
 * Sesli akış (Sprint 2): mikrofon butonu şimdilik pasif. İleride aktif
 * edildiğinde src/api/patientService.js -> sendPatientVoiceMessage() kullanılacak.
 */

// Geliştirme sırasında sabit test hastası (bkz. data/synthetic_personas/).
// İleride oturum/route parametresinden gelecek.
const DEFAULT_PATIENT_ID = 'P-1001'

let messageIdCounter = 0
const nextId = () => `m-${messageIdCounter++}`

function PatientChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Yeni mesaj geldikçe otomatik en alta kaydır
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

  // Textarea yüksekliğini içeriğe göre ayarla
  const handleInputChange = (e) => {
    setInput(e.target.value)
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 140)}px`
    }
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isSending) return

    const patientMsg = { id: nextId(), role: 'patient', text }
    setMessages((prev) => [...prev, patientMsg])
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setIsSending(true)

    try {
      const data = await sendPatientMessage(DEFAULT_PATIENT_ID, text)
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: 'assistant',
          text: data.answer ?? 'Yanıt alınamadı.',
          context: Array.isArray(data.context) ? data.context : [],
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: 'error',
          text: 'Şu anda bağlantı kurulamadı. Lütfen biraz sonra tekrar deneyin.',
        },
      ])
    } finally {
      setIsSending(false)
      textareaRef.current?.focus()
    }
  }

  // Enter = gönder, Shift+Enter = yeni satır
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__avatar" aria-hidden="true">🧭</div>
        <div>
          <h1 className="chat__title">Hasta Etkileşim Ekranı</h1>
          <p className="chat__subtitle">Bir şey sormak için yazın, size yardımcı olayım.</p>
        </div>
      </div>

      <div className="chat__messages" role="log" aria-live="polite" aria-label="Sohbet mesajları">
        {messages.length === 0 && !isSending && (
          <div className="chat__empty">
            <span className="chat__empty-icon" aria-hidden="true">💬</span>
            <p>
              Merhaba! Aklınıza takılan bir şey mi var? Ailenizi, gününüzü ya da
              hatırlamak istediğiniz bir şeyi sorabilirsiniz.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <Message key={msg.id} msg={msg} />
        ))}

        {isSending && (
          <div className="chat__typing" aria-label="Asistan yazıyor">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat__input-area">
        <button
          type="button"
          className="chat__btn chat__btn--mic"
          disabled
          title="Sesli soru — yakında eklenecek"
          aria-label="Sesli soru — yakında eklenecek"
        >
          🎤
        </button>

        <textarea
          ref={textareaRef}
          className="chat__textarea"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Mesajınızı buraya yazın…"
          rows={1}
          disabled={isSending}
          aria-label="Mesaj yazma alanı"
        />

        <button
          type="button"
          className="chat__btn chat__btn--send"
          onClick={handleSend}
          disabled={!input.trim() || isSending}
        >
          Gönder
        </button>
      </div>

      <p className="chat__hint">Sesli konuşma özelliği yakında eklenecek.</p>
    </div>
  )
}

/** Tek bir mesaj balonu (hasta / asistan / hata). */
function Message({ msg }) {
  const isPatient = msg.role === 'patient'
  const isError = msg.role === 'error'
  const label = isPatient ? 'Siz' : isError ? 'Sistem' : 'Asistan'

  return (
    <div className={`msg msg--${msg.role}`}>
      <span className="msg__label">{label}</span>
      <div className="msg__bubble">{msg.text}</div>

      {msg.context && msg.context.length > 0 && (
        <div className="msg__context">
          <p className="msg__context-title">Hatırlatılan bilgiler:</p>
          <ul>
            {msg.context.map((item, i) => (
              <li key={i}>
                {typeof item === 'string' ? item : item.content ?? JSON.stringify(item)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default PatientChatPage
