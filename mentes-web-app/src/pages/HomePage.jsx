import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../components/Card'
import { checkBackendHealth } from '../services/healthService'
import './HomePage.css'

/**
 * Uygulama açıldığında karşılanan başlangıç ekranı.
 * Ayrıca backend bağlantısını (health-check) test ederek
 * frontend <-> backend entegrasyonunun canlı bir örneğini gösterir.
 */
function HomePage() {
  const [backendStatus, setBackendStatus] = useState('checking') // checking | online | offline

  useEffect(() => {
    let isMounted = true
    checkBackendHealth()
      .then(() => {
        if (isMounted) setBackendStatus('online')
      })
      .catch(() => {
        if (isMounted) setBackendStatus('offline')
      })
    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="home">
      <section className="home__hero">
        <span className="home__hero-icon" aria-hidden="true">🧭</span>
        <h1>OrientAI</h1>
        <p className="home__tagline">
          Demans ve Alzheimer hastaları için çok modlu oryantasyon ve hafıza destek asistanı.
        </p>
        <div className="home__status">
          <span className={`status-dot status-dot--${backendStatus}`} aria-hidden="true" />
          {backendStatus === 'checking' && 'Backend bağlantısı kontrol ediliyor…'}
          {backendStatus === 'online' && 'Backend bağlantısı aktif'}
          {backendStatus === 'offline' && 'Backend henüz ayakta değil (bu normal, henüz kurulmadıysa)'}
        </div>
      </section>

      <section className="home__cards">
        <Card title="🗣️ Hasta Etkileşim Ekranı">
          Sesli ve yazılı sohbet, kişiselleştirilmiş hafıza desteği. Sprint 2-3'te geliştirilecek.
          <div className="home__card-link">
            <Link to="/patient">Önizlemeyi gör →</Link>
          </div>
        </Card>
        <Card title="📊 Bakım Veren Paneli">
          Günlük rutinler, hatırlatıcılar ve duygu durumu takibi. Sprint 3'te geliştirilecek.
          <div className="home__card-link">
            <Link to="/caregiver">Önizlemeyi gör →</Link>
          </div>
        </Card>
      </section>
    </div>
  )
}

export default HomePage
