import { useMemo, useState } from 'react'
import Card from '../../../components/Card'
import SentimentBadge from './SentimentBadge'
import {
  INPUT_TYPE_LABELS,
  SENTIMENT_FILTER_OPTIONS,
  SORT_OPTIONS,
  filterAndSortLogs,
  formatTime,
  groupByDay,
} from '../utils/logFilters'
import './ConversationLogList.css'

/**
 * ORI-36 — Konuşma kayıtlarının dashboardda gösterilmesi.
 *
 * Kabul kriterleri ve karşılıkları:
 *   tarih + saat            -> gün başlığı (Bugün / Dün / 28 Temmuz) + saat
 *   hasta girdisi           -> .conv-log__input
 *   asistan yanıtı          -> .conv-log__response
 *   duygu etiketi           -> <SentimentBadge />
 *   filtreleme / sıralama   -> duygu seçimi + sıra seçimi
 *   kart/tablo yapısı       -> güne göre gruplanmış satırlar
 *
 * Kayıtlar güne göre gruplanıyor çünkü bakım verenin sorusu "bugün nasıl
 * geçti" biçiminde; düz bir liste günleri birbirine karıştırır.
 */
function ConversationLogList({ logs = [] }) {
  const [sentiment, setSentiment] = useState('all')
  const [sort, setSort] = useState('newest')

  const groups = useMemo(() => {
    const visible = filterAndSortLogs(logs, { sentiment, sort })
    return groupByDay(visible, 'timestamp')
  }, [logs, sentiment, sort])

  const visibleCount = groups.reduce((sum, group) => sum + group.items.length, 0)

  return (
    <Card className="conv-log">
      <div className="conv-log__head">
        <div className="conv-log__heading">
          <h3 className="conv-log__title">Konuşma kayıtları</h3>
          <span className="conv-log__count">
            {visibleCount === logs.length
              ? `${logs.length} kayıt`
              : `${visibleCount} / ${logs.length} kayıt`}
          </span>
        </div>

        {logs.length > 0 && (
          <div className="conv-log__controls">
            <label className="conv-log__control">
              <span className="conv-log__control-label">Duygu</span>
              <select value={sentiment} onChange={(event) => setSentiment(event.target.value)}>
                {SENTIMENT_FILTER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="conv-log__control">
              <span className="conv-log__control-label">Sıra</span>
              <select value={sort} onChange={(event) => setSort(event.target.value)}>
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
      </div>

      {visibleCount === 0 ? (
        <p className="conv-log__empty">
          {logs.length === 0
            ? 'Kayıt yok. Hasta asistanla konuştukça kayıtlar burada listelenecek.'
            : 'Bu filtreye uyan kayıt yok. Duygu seçimini “Tüm duygular” yaparak hepsini görebilirsiniz.'}
        </p>
      ) : (
        <div className="conv-log__groups">
          {groups.map((group) => (
            <section key={group.dayKey} className="conv-log__group">
              <h4 className="conv-log__day">{group.dayLabel}</h4>

              <ul className="conv-log__list">
                {group.items.map((log) => (
                  <li key={log.log_id} className="conv-log__row">
                    <div className="conv-log__meta">
                      <time className="conv-log__time" dateTime={log.timestamp}>
                        {formatTime(log.timestamp)}
                      </time>
                      <span className="conv-log__type">
                        {INPUT_TYPE_LABELS[log.input_type] || log.input_type}
                      </span>
                    </div>

                    <div className="conv-log__body">
                      <p className="conv-log__input">{log.user_input}</p>
                      <p className="conv-log__response">{log.response}</p>
                    </div>

                    <SentimentBadge sentiment={log.sentiment} />
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </Card>
  )
}

export default ConversationLogList
