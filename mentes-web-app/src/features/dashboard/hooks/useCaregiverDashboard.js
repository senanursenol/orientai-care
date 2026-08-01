import { useCallback, useEffect, useRef, useState } from 'react'
import { getDashboardData } from '../../../api/caregiverService'

const EMPTY_DATA = {
  patient: null,
  routines: [],
  reminders: [],
  routineLogs: [],
  interactionLogs: [],
}

/**
 * Bakım veren panelinin TEK veri giriş noktası.
 *
 * Neden tek hook: ORI-32/34/35/36 aynı hastanın aynı verisini gösteriyor.
 * Her panel kendi fetch'ini yaparsa aynı istek beş kez atılır ve panellerin
 * loading state'leri birbirinden bağımsız titrer.
 *
 * Duygu özetini ayrıca çekmiyoruz — konuşma kayıtlarından türetiliyor
 * (bkz. utils/dashboardMetrics.js ve utils/sentimentAggregate.js). Böylece
 * grafikteki dilim ile listedeki satır hiçbir zaman ayrışmaz.
 *
 * Backend kaynağı seçiliyken endpoint bulunamazsa (404 veya bağlantı hatası)
 * bu bir arıza değil, "endpoint henüz açılmadı" durumudur; panel boş yapıyla
 * çizilir ve `backendUnavailable` true döner. Beklenmeyen hatalar (500, bozuk
 * yanıt) gerçek hata olarak gösterilir — sessizce boş veriye düşmek gerçek
 * bir arızayı gizler.
 *
 * requestId guard'ı unmount sonrası setState'i ve hızlı reload'da eski yanıtın
 * yeniyi ezmesini birlikte engeller. StrictMode effect'i iki kez çalıştırdığı
 * için bu şart.
 */
export function useCaregiverDashboard(patientId) {
  const [status, setStatus] = useState('loading') // loading | ready | error
  const [data, setData] = useState(EMPTY_DATA)
  const [backendUnavailable, setBackendUnavailable] = useState(false)
  const [error, setError] = useState(null)
  const requestIdRef = useRef(0)

  const load = useCallback(async () => {
    if (!patientId) return

    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId

    setStatus('loading')
    setError(null)

    try {
      const loaded = await getDashboardData(patientId)
      if (requestId !== requestIdRef.current) return

      setData({ ...EMPTY_DATA, ...loaded })
      setBackendUnavailable(false)
      setStatus('ready')
    } catch (loadFailure) {
      if (requestId !== requestIdRef.current) return

      const httpStatus = loadFailure?.response?.status
      if (httpStatus === 404 || httpStatus === undefined) {
        setData(EMPTY_DATA)
        setBackendUnavailable(true)
        setStatus('ready')
        return
      }

      setError(`Panel verileri alınamadı (HTTP ${httpStatus}).`)
      setStatus('error')
    }
  }, [patientId])

  useEffect(() => {
    load()
  }, [load])

  useEffect(
    () => () => {
      requestIdRef.current += 1
    },
    [],
  )

  return { status, data, backendUnavailable, error, reload: load }
}
