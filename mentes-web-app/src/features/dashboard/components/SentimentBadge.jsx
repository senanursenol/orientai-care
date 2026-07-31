import { SENTIMENT_LABELS } from '../utils/dashboardMetrics'
import './SentimentBadge.css'

/**
 * Duygu durumu rozeti.
 *
 * ORI-36 log listesinde ve ORI-35 grafiğinin açıklamasında aynı component
 * kullanılıyor; böylece "kaygılı" etiketi panelin her yerinde aynı renkte
 * görünür. Renkler index.css'teki --color-sentiment-* tokenlarından gelir.
 */
function SentimentBadge({ sentiment, size = 'default' }) {
  if (!sentiment || !(sentiment in SENTIMENT_LABELS)) {
    return <span className="sentiment-badge sentiment-badge--unknown">Etiketsiz</span>
  }

  return (
    <span className={`sentiment-badge sentiment-badge--${sentiment} sentiment-badge--${size}`}>
      {SENTIMENT_LABELS[sentiment]}
    </span>
  )
}

export default SentimentBadge
