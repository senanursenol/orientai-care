import { useMemo } from 'react'
import Card from '../../../components/Card'
import { SENTIMENT_KEYS, SENTIMENT_LABELS } from '../utils/dashboardMetrics'
import { buildDailyDistribution, buildOverallDistribution } from '../utils/sentimentAggregate'
import './SentimentChart.css'

/**
 * ORI-35 — Duygu durumu grafiklerinin dashboarda eklenmesi.
 *
 * Kabul kriterleri ve karşılıkları:
 *   ayrı bir alan             -> bu kart
 *   dört etiketin görseli     -> yığılmış çubuk + açıklama listesi
 *   günlük / konuşma bazlı    -> genel çubuk + gün gün çubuklar
 *   mock veya backend verisi  -> veri prop olarak geliyor, kaynak fark etmez
 *   riskli konuşmalar ayırt   -> risk şeridi + riskli günlerde işaret
 *   sade tasarım              -> tek renk ailesi, dört etiket, başka süs yok
 *   chart kütüphanesi VEYA
 *   temel component yapısı    -> flex tabanlı çubuklar, sıfır bağımlılık
 *
 * Neden kütüphane yok: dört kategorili bir yığılmış çubuk, flex-grow ile
 * tam olarak bu kadar kod. recharts eklemek package-lock çakışması ve
 * ~95 kB bundle maliyeti getirirdi, karşılığında hiçbir şey kazandırmazdı.
 *
 * Çubuklar SVG değil flex; böylece viewBox matematiği olmadan kapsayıcıya
 * göre esniyor ve mobilde de bozulmuyor.
 */

function StackedBar({ percentages, counts, ariaLabel }) {
  return (
    <div className="sent-bar" role="img" aria-label={ariaLabel}>
      {SENTIMENT_KEYS.filter((key) => percentages[key] > 0).map((key) => (
        <span
          key={key}
          className={`sent-bar__segment sent-bar__segment--${key}`}
          style={{ flexGrow: percentages[key] }}
          title={`${SENTIMENT_LABELS[key]}: ${counts[key]} konuşma (%${percentages[key]})`}
        />
      ))}
    </div>
  )
}

function SentimentChart({ logs = [] }) {
  const overall = useMemo(() => buildOverallDistribution(logs), [logs])
  const daily = useMemo(() => buildDailyDistribution(logs), [logs])

  if (overall.total === 0) {
    return (
      <Card className="sent-chart">
        <h3 className="sent-chart__title">Duygu durumu dağılımı</h3>
        <p className="sent-chart__empty">Grafik için yeterli konuşma kaydı yok.</p>
      </Card>
    )
  }

  const riskPercent = Math.round(overall.riskRatio * 100)

  return (
    <Card className="sent-chart">
      <div className="sent-chart__head">
        <h3 className="sent-chart__title">Duygu durumu dağılımı</h3>
        <span className="sent-chart__range">Son {daily.length} gün · {overall.total} konuşma</span>
      </div>

      <StackedBar
        percentages={overall.percentages}
        counts={overall.counts}
        ariaLabel={`Genel duygu dağılımı: ${SENTIMENT_KEYS.map(
          (key) => `${SENTIMENT_LABELS[key]} yüzde ${overall.percentages[key]}`,
        ).join(', ')}`}
      />

      <ul className="sent-chart__legend">
        {SENTIMENT_KEYS.map((key) => (
          <li key={key} className="sent-chart__legend-item">
            <span className={`sent-chart__dot sent-chart__dot--${key}`} aria-hidden="true" />
            <span className="sent-chart__legend-label">{SENTIMENT_LABELS[key]}</span>
            <span className="sent-chart__legend-value">
              {overall.counts[key]} · %{overall.percentages[key]}
            </span>
          </li>
        ))}
      </ul>

      <p className={`sent-chart__risk ${overall.riskCount > 0 ? 'sent-chart__risk--active' : ''}`}>
        <strong>{overall.riskCount}</strong> konuşma takip gerektiriyor (kaygılı veya negatif) —
        toplamın %{riskPercent}’i.
      </p>

      <div className="sent-chart__daily">
        <h4 className="sent-chart__subtitle">Gün gün dağılım</h4>

        <ul className="sent-chart__days">
          {daily.map((day) => (
            <li key={day.dayKey} className="sent-chart__day">
              <span className="sent-chart__day-label">
                {day.dayLabel}
                {day.isRiskyDay && (
                  <span className="sent-chart__day-flag" title="Riskli konuşma oranı yüksek">
                    takip
                  </span>
                )}
              </span>

              <StackedBar
                percentages={day.percentages}
                counts={day.counts}
                ariaLabel={`${day.dayLabel}: ${day.total} konuşma, ${day.riskCount} tanesi takip gerektiriyor`}
              />

              <span className="sent-chart__day-total">{day.total}</span>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  )
}

export default SentimentChart
