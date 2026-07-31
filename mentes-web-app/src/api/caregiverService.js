import apiClient from './apiClient'
import { buildPersonaDashboardData } from '../features/dashboard/data/personaDataSource'

/**
 * Bakım veren (caregiver) paneli servis katmanı.
 *
 * React yalnızca Node backend'ine (mentes-service) konuşur. Aşağıdaki endpoint
 * yolları backend ekibiyle üzerinde anlaşılan sözleşmedir.
 *
 * ── VERİ KAYNAĞI ANAHTARI ────────────────────────────────────────────────
 * .env dosyasındaki VITE_DASHBOARD_SOURCE değeri:
 *
 *   persona  (varsayılan) Ekibin sentetik persona dosyasından türetilmiş veri.
 *                         Bkz. features/dashboard/data/personaDataSource.js —
 *                         hangi alanın nereden geldiği orada satır satır yazılı.
 *   backend               Gerçek Node endpointleri.
 *
 * Backend endpointleri açıldığında yapılacak tek şey:
 *     VITE_DASHBOARD_SOURCE=backend
 * Component, hook ve util katmanlarında hiçbir değişiklik gerekmez.
 *
 * Endpointlerin durumu (31.07.2026 itibarıyla test edildi): hepsi 404.
 *   GET    /patients/:id
 *   GET    /patients/:id/routines
 *   GET    /patients/:id/reminders
 *   GET    /patients/:id/routine-logs      (logs tablosu)
 *   GET    /patients/:id/logs              (interaction_logs + sentiment)
 *   POST   /patients/:id/reminders
 *   PATCH  /patients/:id/reminders/:reminderId
 *   DELETE /patients/:id/reminders/:reminderId
 *
 * Ayrıca /patients/:id/logs yanıtının `sentiment` alanını içermesi gerekiyor.
 * interaction_logs tablosunda bu kolon yok ve Node, AI servisinden dönen
 * etiketi kaydetmiyor (bkz. routes/chat-route.js).
 * ─────────────────────────────────────────────────────────────────────────
 */

const SOURCE = import.meta.env.VITE_DASHBOARD_SOURCE || 'persona'

export const DASHBOARD_SOURCE = SOURCE

export function isPersonaSource() {
  return SOURCE !== 'backend'
}

/** Persona kaynağında sunucu gecikmesini taklit eder — loading state'leri gerçekten test edilsin. */
const PERSONA_LATENCY_MS = 220

function resolvePersona(value) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), PERSONA_LATENCY_MS)
  })
}

/**
 * Panelin ihtiyaç duyduğu bütün veriyi tek çağrıda getirir.
 * Persona kaynağında tek üretim, backend kaynağında beş paralel istek.
 */
export async function getDashboardData(patientId) {
  if (isPersonaSource()) {
    return resolvePersona(buildPersonaDashboardData())
  }

  const [patient, routines, reminders, routineLogs, interactionLogs] = await Promise.all([
    apiClient.get(`/patients/${patientId}`).then((r) => r.data),
    apiClient.get(`/patients/${patientId}/routines`).then((r) => r.data),
    apiClient.get(`/patients/${patientId}/reminders`).then((r) => r.data),
    apiClient.get(`/patients/${patientId}/routine-logs`).then((r) => r.data),
    apiClient.get(`/patients/${patientId}/logs`).then((r) => r.data),
  ])

  return { patient, routines, reminders, routineLogs, interactionLogs }
}

// ------------------------------------------------------------- yazma işlemleri
// ORI-34: hatırlatıcı ekleme, güncelleme ve silme.
// Persona kaynağında sunucuya gitmez; çağıran kendi state'ini günceller.
// Bu, ORI-34'ün "backend bağlantısı yoksa mock veriyle gösterim yapılabilmeli"
// kriterini karşılar ve sözleşmeyi de belgelemiş olur.

export async function createReminder(patientId, reminder) {
  if (isPersonaSource()) {
    return resolvePersona({ ...reminder, reminder_id: Date.now() })
  }
  const { data } = await apiClient.post(`/patients/${patientId}/reminders`, reminder)
  return data
}

export async function updateReminder(patientId, reminderId, changes) {
  if (isPersonaSource()) {
    return resolvePersona({ reminder_id: reminderId, ...changes })
  }
  const { data } = await apiClient.patch(`/patients/${patientId}/reminders/${reminderId}`, changes)
  return data
}

export async function deleteReminder(patientId, reminderId) {
  if (isPersonaSource()) {
    return resolvePersona({ reminder_id: reminderId, deleted: true })
  }
  const { data } = await apiClient.delete(`/patients/${patientId}/reminders/${reminderId}`)
  return data
}
