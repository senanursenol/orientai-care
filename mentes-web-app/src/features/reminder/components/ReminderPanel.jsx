import { useState } from 'react'
import Card from '../../../components/Card'
import { useReminders } from '../hooks/useReminders'
import './ReminderPanel.css'

/**
 * ORI-34 — Hatırlatıcı yönetim ekranı.
 *
 * Kabul kriterleri ve karşılıkları:
 *   listeleme ekranı           -> .reminder-panel__list
 *   ad, saat, açıklama, durum  -> her satırda dördü birlikte
 *   yeni ekleme alanı          -> "Yeni hatırlatıcı" formu
 *   güncelleme/silme akışı     -> aktiflik anahtarı + sil düğmesi (useReminders)
 *   backend yoksa mock gösterim-> persona kaynağı, değişiklik yerelde tutulur
 *   dashboard içinde erişilebilir -> panel doğrudan dashboard sayfasında
 *   reminder endpointleriyle çalışabilir -> caregiverService sözleşmesi hazır
 *
 * Form ayrı bir dosyaya çıkarılmadı; tek yerde kullanılan üç alanlı bir form
 * için ayrı component katmanı okumayı zorlaştırırdı.
 */

const EMPTY_FORM = { title: '', description: '', time: '' }

function ReminderPanel({ patientId, reminders, routines }) {
  const { items, error, pendingAction, isLocalOnly, addReminder, toggleActive, removeReminder } =
    useReminders({ patientId, reminders, routines })

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState('')

  const activeCount = items.filter((item) => item.is_active).length

  const updateField = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
  }

  const submit = async () => {
    if (!form.title.trim()) {
      setFormError('Hatırlatıcı adı gerekli.')
      return
    }
    if (!form.time) {
      setFormError('Saat gerekli.')
      return
    }

    setFormError('')
    await addReminder({
      title: form.title.trim(),
      description: form.description.trim(),
      time: form.time,
    })
    setForm(EMPTY_FORM)
    setIsFormOpen(false)
  }

  const cancel = () => {
    setForm(EMPTY_FORM)
    setFormError('')
    setIsFormOpen(false)
  }

  return (
    <Card className="reminder-panel">
      <div className="reminder-panel__head">
        <div className="reminder-panel__heading">
          <h3 className="reminder-panel__title">Hatırlatıcılar</h3>
          <span className="reminder-panel__count">
            {items.length} tanımlı · {activeCount} aktif
          </span>
        </div>

        {!isFormOpen && (
          <button
            type="button"
            className="reminder-panel__add"
            onClick={() => setIsFormOpen(true)}
          >
            Yeni hatırlatıcı
          </button>
        )}
      </div>

      {error && <p className="reminder-panel__error">{error}</p>}

      {isFormOpen && (
        <div className="reminder-form">
          <div className="reminder-form__row">
            <label className="reminder-form__field reminder-form__field--grow">
              <span className="reminder-form__label">Ad</span>
              <input
                type="text"
                value={form.title}
                onChange={updateField('title')}
                placeholder="Akşam ilacı"
              />
            </label>

            <label className="reminder-form__field">
              <span className="reminder-form__label">Saat</span>
              <input type="time" value={form.time} onChange={updateField('time')} />
            </label>
          </div>

          <label className="reminder-form__field">
            <span className="reminder-form__label">Açıklama</span>
            <input
              type="text"
              value={form.description}
              onChange={updateField('description')}
              placeholder="Yatmadan önce alınır"
            />
          </label>

          {formError && <p className="reminder-form__error">{formError}</p>}

          <div className="reminder-form__actions">
            <button
              type="button"
              className="reminder-form__submit"
              onClick={submit}
              disabled={pendingAction === 'create'}
            >
              {pendingAction === 'create' ? 'Ekleniyor…' : 'Ekle'}
            </button>
            <button type="button" className="reminder-form__cancel" onClick={cancel}>
              Vazgeç
            </button>
          </div>

          {isLocalOnly && (
            <p className="reminder-form__note">
              Backend hatırlatıcı endpointleri açılmadığı için eklenen kayıt yalnızca bu
              ekranda görünür, sunucuya yazılmaz.
            </p>
          )}
        </div>
      )}

      {items.length === 0 ? (
        <p className="reminder-panel__empty">
          Tanımlı hatırlatıcı yok. “Yeni hatırlatıcı” ile ekleyebilirsiniz.
        </p>
      ) : (
        <ul className="reminder-panel__list">
          {items.map((item) => (
            <li
              key={item.reminder_id}
              className={`reminder-row ${item.is_active ? '' : 'reminder-row--inactive'}`}
            >
              <time className="reminder-row__time">{item.reminder_time}</time>

              <div className="reminder-row__body">
                <p className="reminder-row__title">{item.title}</p>
                {item.description && <p className="reminder-row__desc">{item.description}</p>}
              </div>

              <span
                className={`reminder-row__status reminder-row__status--${
                  item.is_active ? 'active' : 'inactive'
                }`}
              >
                {item.is_active ? 'Aktif' : 'Kapalı'}
              </span>

              <div className="reminder-row__actions">
                <button
                  type="button"
                  onClick={() => toggleActive(item.reminder_id, !item.is_active)}
                  disabled={pendingAction === `toggle-${item.reminder_id}`}
                >
                  {item.is_active ? 'Kapat' : 'Aç'}
                </button>
                <button
                  type="button"
                  className="reminder-row__delete"
                  onClick={() => removeReminder(item.reminder_id)}
                  disabled={pendingAction === `delete-${item.reminder_id}`}
                >
                  Sil
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

export default ReminderPanel
