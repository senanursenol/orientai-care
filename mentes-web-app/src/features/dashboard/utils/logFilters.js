/**
 * ORI-36: "Dashboard üzerinde temel filtreleme veya sıralama yapılabilmeli."
 *
 * Filtreleme ve sıralama saf fonksiyonlar olarak burada duruyor; component
 * yalnızca hangi filtrenin seçili olduğunu tutar. Böylece mantık test
 * edilebilir kalır ve aynı fonksiyonlar ORI-35 grafiğinde de kullanılabilir.
 */

import { SENTIMENT_LABELS } from './dashboardMetrics'

export const SENTIMENT_FILTER_OPTIONS = [
  { value: 'all', label: 'Tüm duygular' },
  ...Object.entries(SENTIMENT_LABELS).map(([value, label]) => ({ value, label })),
]

export const SORT_OPTIONS = [
  { value: 'newest', label: 'En yeni önce' },
  { value: 'oldest', label: 'En eski önce' },
]

export const INPUT_TYPE_LABELS = {
  text: 'Yazılı',
  voice: 'Sesli',
  image: 'Fotoğraf',
}

/**
 * Konuşma kayıtlarını filtreler ve sıralar.
 * Girdi dizisini değiştirmez — kopya üzerinde çalışır.
 */
export function filterAndSortLogs(logs = [], { sentiment = 'all', sort = 'newest' } = {}) {
  const filtered = sentiment === 'all' ? [...logs] : logs.filter((log) => log.sentiment === sentiment)

  return filtered.sort((a, b) => {
    const diff = new Date(b.timestamp) - new Date(a.timestamp)
    return sort === 'newest' ? diff : -diff
  })
}

/** Bugün / Dün / gün-ay biçiminde okunabilir gün başlığı. */
export function formatDayLabel(isoString) {
  const date = new Date(isoString)
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)

  const sameDay = (a, b) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()

  if (sameDay(date, today)) return 'Bugün'
  if (sameDay(date, yesterday)) return 'Dün'

  return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })
}

export function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
}

/**
 * Kayıtları güne göre gruplar: [{ dayKey, dayLabel, items }]
 * Sıra korunur — çağıran önce sıraladığı için gruplar da o sırada gelir.
 */
export function groupByDay(records = [], dateField) {
  const groups = new Map()

  for (const record of records) {
    const value = record[dateField]
    const dayKey = new Date(value).toDateString()

    if (!groups.has(dayKey)) {
      groups.set(dayKey, { dayKey, dayLabel: formatDayLabel(value), items: [] })
    }
    groups.get(dayKey).items.push(record)
  }

  return [...groups.values()]
}

/**
 * Rutin kayıtlarını rutin başlıklarıyla birleştirir.
 * `logs` tablosunda yalnızca routine_id var; başlık ve açıklama `routines`
 * tablosunda. Backend join'i döndürene kadar birleştirmeyi burada yapıyoruz.
 */
export function joinRoutineLogs(routineLogs = [], routines = []) {
  const byId = new Map(routines.map((routine) => [routine.routine_id, routine]))

  return routineLogs.map((log) => ({
    ...log,
    routine: byId.get(log.routine_id) || null,
    title: byId.get(log.routine_id)?.title || 'Rutin',
  }))
}

/** Rutin kayıtlarını en yeni önce sıralar. */
export function sortRoutineLogs(routineLogs = []) {
  return [...routineLogs].sort((a, b) => new Date(b.log_date) - new Date(a.log_date))
}
