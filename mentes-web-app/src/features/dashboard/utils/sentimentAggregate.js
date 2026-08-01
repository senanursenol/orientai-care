/**
 * ORI-35 — duygu durumu grafiklerinin veri katmanı.
 *
 * Grafik componenti hiç hesap yapmaz, yalnızca burada üretilen sayıları çizer.
 * Aynı sayımlar özet kartlarında da kullanıldığı için (dashboardMetrics)
 * grafik ile kart hiçbir zaman ayrışmaz.
 */

import {
  SENTIMENT_KEYS,
  countSentiments,
  toSentimentPercentages,
} from './dashboardMetrics'
import { formatDayLabel, groupByDay } from './logFilters'

/**
 * ORI-35: "Riskli konuşmalar grafik veya tablo üzerinde ayırt edilebilir olmalı."
 *
 * Riskli sayılan etiketler: kaygılı ve negatif. Bakım verenin müdahale etmesi
 * gereken durumlar bunlar; pozitif ve nötr konuşmalar takip gerektirmez.
 */
export const RISK_KEYS = ['anxious', 'negative']

/** Bir günün riskli sayılması için gereken oran eşiği. */
export const RISK_DAY_THRESHOLD = 0.4

export function countRisky(logs = []) {
  return logs.filter((log) => RISK_KEYS.includes(log.sentiment)).length
}

/**
 * Tüm kayıtların genel dağılımı.
 * { counts, percentages, total, riskCount, riskRatio }
 */
export function buildOverallDistribution(logs = []) {
  const counts = countSentiments(logs)
  const total = SENTIMENT_KEYS.reduce((sum, key) => sum + counts[key], 0)
  const riskCount = countRisky(logs)

  return {
    counts,
    percentages: toSentimentPercentages(counts),
    total,
    riskCount,
    riskRatio: total === 0 ? 0 : riskCount / total,
  }
}

/**
 * Güne göre dağılım — en yeni gün önce.
 * [{ dayKey, dayLabel, counts, percentages, total, riskCount, isRiskyDay }]
 */
export function buildDailyDistribution(logs = []) {
  const sorted = [...logs].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

  return groupByDay(sorted, 'timestamp').map((group) => {
    const counts = countSentiments(group.items)
    const total = group.items.length
    const riskCount = countRisky(group.items)

    return {
      dayKey: group.dayKey,
      dayLabel: group.dayLabel || formatDayLabel(group.items[0].timestamp),
      counts,
      percentages: toSentimentPercentages(counts),
      total,
      riskCount,
      isRiskyDay: total > 0 && riskCount / total >= RISK_DAY_THRESHOLD,
    }
  })
}
