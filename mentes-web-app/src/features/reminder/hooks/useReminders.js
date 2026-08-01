import { useCallback, useMemo, useState } from 'react'
import {
  createReminder,
  deleteReminder,
  isPersonaSource,
  updateReminder,
} from '../../../api/caregiverService'

/**
 * ORI-34 — hatırlatıcı yönetiminin state ve akış katmanı.
 *
 * Kabul kriterlerinden ikisi doğrudan buraya bakıyor:
 *   "Yeni hatırlatıcı ekleme alanı tasarlanmış olmalı"
 *   "Hatırlatıcı güncelleme veya silme akışı planlanmış olmalı"
 *
 * Akış iyimser (optimistic): kullanıcı ekle/sil/değiştir dediğinde liste hemen
 * güncellenir, istek arkada gider. İstek başarısız olursa liste eski haline
 * döndürülür ve hata gösterilir. Bakım veren panelinde her tıklamadan sonra
 * spinner beklemek yorucu; ama başarısızlığı sessizce yutmak da olmaz.
 *
 * Hatırlatıcı ile rutin ayrı iki tablodur (reminders.routine_id -> routines).
 * Başlık ve açıklama rutinde, saat ve aktiflik hatırlatıcıda durur. Bu hook
 * ikisini birleştirilmiş halde döndürür, component join'le uğraşmaz.
 */
export function useReminders({ patientId, reminders = [], routines = [] }) {
  const [localReminders, setLocalReminders] = useState(reminders)
  const [pendingAction, setPendingAction] = useState(null)
  const [error, setError] = useState(null)

  // Panel verisi yeniden yüklendiğinde (reload) dışarıdan gelen liste kazanır.
  const [syncedFrom, setSyncedFrom] = useState(reminders)
  if (syncedFrom !== reminders) {
    setSyncedFrom(reminders)
    setLocalReminders(reminders)
  }

  const routineById = useMemo(
    () => new Map(routines.map((routine) => [routine.routine_id, routine])),
    [routines],
  )

  /** Saate göre sıralı, rutin bilgisiyle birleştirilmiş liste. */
  const items = useMemo(
    () =>
      [...localReminders]
        .map((reminder) => {
          const routine = routineById.get(reminder.routine_id) || null
          return {
            ...reminder,
            routine,
            // Başlık ve açıklama normalde `routines` tablosundan gelir. Ama yeni
            // eklenen bir hatırlatıcının henüz kayıtlı rutini yoktur; o durumda
            // değerler kaydın kendi üzerinde durur. Sıralama önemli: önce rutin,
            // sonra kaydın kendisi, en son varsayılan.
            title: routine?.title || reminder.title || 'Hatırlatıcı',
            description: routine?.description || reminder.description || '',
          }
        })
        .sort((a, b) => String(a.reminder_time).localeCompare(String(b.reminder_time))),
    [localReminders, routineById],
  )

  const runAction = useCallback(
    async (actionKey, optimisticUpdate, request) => {
      const previous = localReminders
      setError(null)
      setPendingAction(actionKey)
      setLocalReminders(optimisticUpdate(previous))

      try {
        await request()
      } catch (failure) {
        setLocalReminders(previous)
        setError(
          failure?.response?.status === 404
            ? 'Hatırlatıcı endpointleri backend’de henüz açılmadı, değişiklik kaydedilemedi.'
            : failure?.message || 'Değişiklik kaydedilemedi.',
        )
      } finally {
        setPendingAction(null)
      }
    },
    [localReminders],
  )

  /**
   * Yeni hatırlatıcı. Kendi rutinini de oluşturur, çünkü başlık ve açıklama
   * `routines` tablosunda yaşıyor. Backend hazır olduğunda bu iki kaydın
   * tek istekte mi iki istekte mi oluşturulacağı backend ekibiyle netleşmeli —
   * şimdilik tek POST gövdesinde gönderiyoruz.
   */
  const addReminder = useCallback(
    ({ title, description, time }) => {
      const tempId = `new-${Date.now()}`
      const payload = { title, description, reminder_time: time, is_active: true }

      return runAction(
        'create',
        (current) => [
          ...current,
          { reminder_id: tempId, routine_id: tempId, reminder_time: time, is_active: true, title, description },
        ],
        () => createReminder(patientId, payload),
      )
    },
    [patientId, runAction],
  )

  const toggleActive = useCallback(
    (reminderId, nextActive) =>
      runAction(
        `toggle-${reminderId}`,
        (current) =>
          current.map((reminder) =>
            reminder.reminder_id === reminderId ? { ...reminder, is_active: nextActive } : reminder,
          ),
        () => updateReminder(patientId, reminderId, { is_active: nextActive }),
      ),
    [patientId, runAction],
  )

  const removeReminder = useCallback(
    (reminderId) =>
      runAction(
        `delete-${reminderId}`,
        (current) => current.filter((reminder) => reminder.reminder_id !== reminderId),
        () => deleteReminder(patientId, reminderId),
      ),
    [patientId, runAction],
  )

  return {
    items,
    error,
    pendingAction,
    isLocalOnly: isPersonaSource(),
    addReminder,
    toggleActive,
    removeReminder,
  }
}