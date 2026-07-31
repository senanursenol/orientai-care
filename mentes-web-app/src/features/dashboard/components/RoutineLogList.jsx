import { useMemo } from 'react'
import Card from '../../../components/Card'
import { COMPLETION_STATUSES, ROUTINE_STATUS_LABELS } from '../utils/dashboardMetrics'
import { formatTime, groupByDay, joinRoutineLogs, sortRoutineLogs } from '../utils/logFilters'
import './RoutineLogList.css'

/**
 * ORI-36 — "Rutin ve hatırlatıcı kayıtları ayrı bir bölümde gösterilmeli.
 *           Tamamlanan ve tamamlanmayan rutinler ayırt edilebilir olmalı."
 *
 * Ayırt etme yalnızca renkle yapılmıyor; her satırda metin etiketi de var
 * (Tamamlandı / Kaçırıldı / Bekliyor). Renk körlüğü olan bir bakım veren de
 * durumu okuyabilsin diye.
 *
 * Rutin başlığı `routines`, kayıt ise `logs` tablosundan geliyor; ikisini
 * routine_id üzerinden burada birleştiriyoruz (bkz. joinRoutineLogs).
 */
function RoutineLogList({ routineLogs = [], routines = [] }) {
  const groups = useMemo(() => {
    const joined = joinRoutineLogs(routineLogs, routines)
    return groupByDay(sortRoutineLogs(joined), 'log_date')
  }, [routineLogs, routines])

  const todaysGroup = groups[0]
  const todaysCompleted = todaysGroup
    ? todaysGroup.items.filter((log) => log.status === 'completed').length
    : 0

  // Tamamlanma kaydı hiç yoksa "0 / 4 tamamlandı" yazmak hastanın bütün
  // rutinlerini kaçırdığı izlenimi verir. Böyle bir durumda yalnızca rutin
  // sayısını söylüyoruz.
  const hasCompletionData = todaysGroup
    ? todaysGroup.items.some((log) => COMPLETION_STATUSES.includes(log.status))
    : false

  return (
    <Card className="routine-log">
      <div className="routine-log__head">
        <h3 className="routine-log__title">Rutin uyumu</h3>
        {todaysGroup && (
          <span className="routine-log__summary">
            {hasCompletionData
              ? `${todaysGroup.dayLabel}: ${todaysCompleted} / ${todaysGroup.items.length} tamamlandı`
              : `${todaysGroup.dayLabel}: ${todaysGroup.items.length} rutin`}
          </span>
        )}
      </div>

      {groups.length === 0 ? (
        <p className="routine-log__empty">Henüz rutin kaydı yok.</p>
      ) : (
        <div className="routine-log__groups">
          {groups.map((group) => (
            <section key={group.dayKey} className="routine-log__group">
              <h4 className="routine-log__day">{group.dayLabel}</h4>

              <ul className="routine-log__list">
                {group.items.map((log) => (
                  <li key={log.log_id} className={`routine-log__row routine-log__row--${log.status}`}>
                    <time className="routine-log__time" dateTime={log.log_date}>
                      {formatTime(log.log_date)}
                    </time>

                    <div className="routine-log__body">
                      <p className="routine-log__name">{log.title}</p>
                      {log.note && <p className="routine-log__note">{log.note}</p>}
                    </div>

                    <span className={`routine-log__status routine-log__status--${log.status}`}>
                      {ROUTINE_STATUS_LABELS[log.status] || log.status}
                    </span>
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

export default RoutineLogList