import Card from '../components/Card'
import ConversationLogList from '../features/dashboard/components/ConversationLogList'
import PatientSummaryCard from '../features/dashboard/components/PatientSummaryCard'
import RoutineLogList from '../features/dashboard/components/RoutineLogList'
import SentimentChart from '../features/dashboard/components/SentimentChart'
import ReminderPanel from '../features/reminder/components/ReminderPanel'
import { useCaregiverDashboard } from '../features/dashboard/hooks/useCaregiverDashboard'
import { buildDashboardMetrics } from '../features/dashboard/utils/dashboardMetrics'
import './CaregiverDashboardPage.css'

/**
 * Bakım veren (caregiver) paneli — ORI-32.
 *
 * Bu sayfa kasten "ince" tutuldu: veriyi hook çeker, sayıları util hesaplar,
 * görünümü feature altındaki componentler kurar. Sayfanın tek işi yerleşim.
 *
 * ORI-32 kabul kriterleri ve karşılıkları:
 *   React dashboardu oluşturulmuş        -> bu sayfa
 *   backend'den veri alabilecek şekilde  -> caregiverService sözleşmesi + kaynak anahtarı
 *   hastanın temel bilgileri             -> <PatientSummaryCard />
 *   konuşma logları için ayrı alan       -> <ConversationLogList />  (ORI-36)
 *   duygu özetleri ve grafikler          -> özet kartları + <SentimentChart />  (ORI-35)
 *   rutin ve hatırlatıcı bilgileri       -> <RoutineLogList /> + <ReminderPanel />  (ORI-34)
 *
 * TODO(auth): hasta kimliği şimdilik sabit. Oturum yönetimi geldiğinde seçili
 * hasta context/store üzerinden okunacak. Aynı geçici sabit PatientChatPage
 * içinde de duruyor; auth işinde ikisi tek kaynağa bağlanmalı.
 */
const PATIENT_ID = 'P-1001'

function MetricCard({ label, value, tone = 'default' }) {
  return (
    <div className={`metric metric--${tone}`}>
      <span className="metric__label">{label}</span>
      <span className="metric__value">{value}</span>
    </div>
  )
}

function CaregiverDashboardPage() {
  const { status, data, backendUnavailable, error, reload } = useCaregiverDashboard(PATIENT_ID)
  const metrics = buildDashboardMetrics(data)

  return (
    <div className="dashboard">
      <header className="dashboard__intro">
        <span className="dashboard__eyebrow">Bakım veren paneli</span>
        <h1>Hastanızın günü</h1>
        <p className="dashboard__tagline">
          Konuşma kayıtları, rutin uyumu, hatırlatıcılar ve duygu durumu tek ekranda.
        </p>
      </header>

      {status === 'loading' && (
        <Card className="dashboard__state">
          <p>Panel verileri yükleniyor…</p>
        </Card>
      )}

      {status === 'error' && (
        <Card className="dashboard__state dashboard__state--error">
          <p>{error}</p>
          <button type="button" className="dashboard__retry" onClick={reload}>
            Yeniden dene
          </button>
        </Card>
      )}

      {status === 'ready' && (
        <>
          {backendUnavailable && (
            <Card className="dashboard__notice">
              <h2 className="dashboard__notice-title">Backend endpointleri bulunamadı</h2>
              <p className="dashboard__notice-text">
                <code>VITE_DASHBOARD_SOURCE=backend</code> seçili ama caregiver endpointleri
                yanıt vermiyor. Panelin yerleşimi ve bileşenleri hazır; endpointler
                açıldığında veriler otomatik dolacak.
              </p>
              <button type="button" className="dashboard__retry" onClick={reload}>
                Yeniden dene
              </button>
            </Card>
          )}

          {data.patient ? (
            <PatientSummaryCard patient={data.patient} />
          ) : (
            <Card className="dashboard__empty-slot">
              <span className="dashboard__empty-label">Hasta bilgileri</span>
              <p>
                Hasta kimliği <code>{PATIENT_ID}</code> için bilgi alınamadı.
              </p>
            </Card>
          )}

          <section className="dashboard__metrics" aria-label="Günün özeti">
            <MetricCard label="Bugünkü konuşma" value={metrics.conversationCount} />
            <MetricCard
              label={metrics.routineCompletion.cardLabel}
              value={metrics.routineCompletion.label}
            />
            <MetricCard label="Aktif hatırlatıcı" value={metrics.activeReminderCount} />
            <MetricCard
              label="Baskın duygu"
              value={metrics.dominantSentimentLabel}
              tone={metrics.dominantSentiment || 'default'}
            />
          </section>

          <section className="dashboard__panels">
            <SentimentChart logs={data.interactionLogs} />
            <ConversationLogList logs={data.interactionLogs} />
            <RoutineLogList routineLogs={data.routineLogs} routines={data.routines} />
            <ReminderPanel
              patientId={PATIENT_ID}
              reminders={data.reminders}
              routines={data.routines}
            />
          </section>
        </>
      )}
    </div>
  )
}

export default CaregiverDashboardPage