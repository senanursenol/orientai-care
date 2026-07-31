/**
 * Panel metrikleri — hepsi ham log verisinden türetilir, hiçbiri elle yazılmaz.
 *
 * Faz 3'teki duygu grafiği (ORI-35) de aynı fonksiyonları kullanacak; böylece
 * "kartta yazan sayı" ile "grafikteki dilim" hiçbir zaman birbirinden ayrışmaz.
 */

/** Python servisindeki SENTIMENT_LABELS ile aynı küme ve aynı sıra. */
export const SENTIMENT_KEYS = ['positive', 'neutral', 'negative', 'anxious']

export const SENTIMENT_LABELS = {
  positive: 'Pozitif',
  neutral: 'Nötr',
  negative: 'Negatif',
  anxious: 'Kaygılı',
}

export const ROUTINE_STATUS_LABELS = {
  completed: 'Tamamlandı',
  missed: 'Kaçırıldı',
  pending: 'Bekliyor',
  // Saati geçmiş ama tamamlanma kaydı olmayan rutin. Persona kaynağında bütün
  // geçmiş rutinler bu durumda olur; "tamamlandı" demek uydurma, "kaçırıldı"
  // demek de haksız olurdu.
  unknown: 'Kayıt yok',
}

/** Tamamlanma bilgisi taşıyan durumlar. `pending` ve `unknown` bilgi taşımaz. */
export const COMPLETION_STATUSES = ['completed', 'missed']

function isSameDay(isoString, reference) {
  const date = new Date(isoString)
  return (
    date.getFullYear() === reference.getFullYear() &&
    date.getMonth() === reference.getMonth() &&
    date.getDate() === reference.getDate()
  )
}

/** Doğum tarihinden yaş — ay/gün geçmediyse bir yaş eksiltir. */
export function calculateAge(birthDate) {
  if (!birthDate) return null
  const birth = new Date(birthDate)
  if (Number.isNaN(birth.getTime())) return null

  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age -= 1
  }
  return age
}

/** { positive: 6, neutral: 4, negative: 2, anxious: 3 } */
export function countSentiments(interactionLogs = []) {
  const counts = Object.fromEntries(SENTIMENT_KEYS.map((key) => [key, 0]))
  for (const log of interactionLogs) {
    if (log?.sentiment in counts) counts[log.sentiment] += 1
  }
  return counts
}

/**
 * Yüzdeye çevirir ve toplamı tam 100 yapar.
 * Ham yuvarlama 99 veya 101 üretebilir; en büyük dilime artığı ekleyerek
 * yığılmış çubuğun (ORI-35) kenarında boşluk/taşma oluşmasını engelliyoruz.
 */
export function toSentimentPercentages(counts) {
  const total = SENTIMENT_KEYS.reduce((sum, key) => sum + (counts[key] || 0), 0)
  if (total === 0) return Object.fromEntries(SENTIMENT_KEYS.map((key) => [key, 0]))

  const percentages = {}
  for (const key of SENTIMENT_KEYS) {
    percentages[key] = Math.round(((counts[key] || 0) / total) * 100)
  }

  const drift = 100 - SENTIMENT_KEYS.reduce((sum, key) => sum + percentages[key], 0)
  if (drift !== 0) {
    const largest = SENTIMENT_KEYS.reduce((best, key) =>
      percentages[key] > percentages[best] ? key : best,
    )
    percentages[largest] += drift
  }

  return percentages
}

/** En çok görülen duygu. Eşitlikte SENTIMENT_KEYS sırası belirleyici olur. */
export function dominantSentiment(counts) {
  let winner = null
  for (const key of SENTIMENT_KEYS) {
    if (counts[key] > 0 && (winner === null || counts[key] > counts[winner])) {
      winner = key
    }
  }
  return winner
}

/**
 * Panel üstündeki dört özet kart.
 * Rutin sayımı yalnızca BUGÜNÜN kayıtlarına bakar — "4/6" ifadesi ancak
 * tek güne aitse anlamlı, yoksa geçmiş günler toplamı şişirir.
 */
export function buildDashboardMetrics({ interactionLogs = [], routineLogs = [], reminders = [] } = {}) {
  const today = new Date()

  const todaysConversations = interactionLogs.filter((log) => isSameDay(log.timestamp, today))
  const todaysRoutines = routineLogs.filter((log) => isSameDay(log.log_date, today))
  const completedToday = todaysRoutines.filter((log) => log.status === 'completed').length

  const counts = countSentiments(interactionLogs)
  const dominant = dominantSentiment(counts)

  // Tamamlanma verisi hiç yoksa "0/4" göstermek hastanın rutinlerini
  // kaçırdığı izlenimi verir. Bu yüzden veri olup olmadığını ayrıca bildiriyoruz;
  // sayfa etiketi ona göre seçiyor.
  const hasCompletionData = todaysRoutines.some((log) =>
    COMPLETION_STATUSES.includes(log.status),
  )

  return {
    conversationCount: todaysConversations.length,
    routineCompletion: {
      completed: completedToday,
      total: todaysRoutines.length,
      hasCompletionData,
      label: !hasCompletionData
        ? String(todaysRoutines.length || '—')
        : `${completedToday}/${todaysRoutines.length}`,
      cardLabel: hasCompletionData ? 'Tamamlanan rutin' : 'Bugünkü rutin',
    },
    activeReminderCount: reminders.filter((reminder) => reminder.is_active).length,
    dominantSentiment: dominant,
    dominantSentimentLabel: dominant ? SENTIMENT_LABELS[dominant] : '—',
    sentimentCounts: counts,
    sentimentPercentages: toSentimentPercentages(counts),
  }
}
