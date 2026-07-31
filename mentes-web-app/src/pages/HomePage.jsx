import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import BrandMark from '../components/BrandMark'
import { checkBackendHealth } from '../api/healthService'
import './HomePage.css'

/**
 * Karşılama ekranı.
 *
 * Sayfanın tek işi rol seçimi: bu ekranı açan kişi hasta mı, bakım veren mi?
 * İki kullanıcının ihtiyacı birbirine benzemiyor, bu yüzden iki kart kasten
 * eşit ağırlıkta değil — hasta kartı daha büyük tipografi ve tek eylem
 * taşıyor, bakım veren kartı içindekileri sayıyor.
 *
 * İMZA ÖĞESİ — oryantasyon paneli:
 * Demans hastasının ilk kaybettiği şeylerden biri zamana yönelim; ürünün adı
 * da bu yüzden OrientAI. Sayfanın en üstünde marka logosu yerine bugünün
 * tarihi, gün adı ve saate göre selamlama duruyor. Bu bir süs değil, ürünün
 * yaptığı işin ta kendisi ve saatten hesaplanıyor.
 *
 * Erişilebilirlik, burada olağandan önemli: kullanıcılar bilişsel güçlük
 * yaşayan bireyler ve çoğu zaman yaşlı bakım verenler. Bu yüzden kartların
 * tamamı tıklanabilir, dokunma alanları büyük, metin kontrastı yüksek ve
 * hareket `prefers-reduced-motion` ile devre dışı bırakılabiliyor.
 */

const GREETINGS = [
  { until: 5, text: 'İyi geceler' },
  { until: 11, text: 'Günaydın' },
  { until: 17, text: 'İyi günler' },
  { until: 22, text: 'İyi akşamlar' },
  { until: 24, text: 'İyi geceler' },
]

function greetingFor(date) {
  const hour = date.getHours()
  return GREETINGS.find((entry) => hour < entry.until)?.text || 'Merhaba'
}

function HomePage() {
  const [now, setNow] = useState(() => new Date())
  const [backendStatus, setBackendStatus] = useState('checking') // checking | online | offline

  // Saat panelde yazılı olduğu için canlı tutuyoruz. Dakika hassasiyeti yeterli.
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    let isMounted = true
    checkBackendHealth()
      .then(() => isMounted && setBackendStatus('online'))
      .catch(() => isMounted && setBackendStatus('offline'))
    return () => {
      isMounted = false
    }
  }, [])

  const dayName = now.toLocaleDateString('tr-TR', { weekday: 'long' })
  const fullDate = now.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })
  const clock = now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="home">
      <section className="orient" aria-label="Bugünün tarihi ve saati">
        <div className="orient__body">
          <p className="orient__greeting">{greetingFor(now)}</p>
          <p className="orient__day">{dayName}</p>
          <p className="orient__date">
            {fullDate}
            <span className="orient__clock">
              <time dateTime={now.toISOString()}>{clock}</time>
            </span>
          </p>
        </div>

        {/* Pusula, panelin anlamının görsel karşılığı: bu blok kullanıcıyı
            zamanda yönlendiriyor. Düşük kontrastta, okumayı engellemiyor. */}
        <BrandMark size={124} className="orient__mark" />
      </section>

      <header className="home__intro">
        <span className="home__eyebrow">OrientAI</span>
        <h1>Bugün kim için buradayız?</h1>
        <p className="home__tagline">
          Demans ve Alzheimer hastaları için oryantasyon ve hafıza desteği; bakım verenler için
          günün özeti.
        </p>
      </header>

      <nav className="home__roles" aria-label="Rol seçimi">
        <Link to="/patient" className="role role--patient">
          <span className="role__eyebrow">Hasta</span>
          <span className="role__title">Asistanla konuş</span>
          <span className="role__lead">
            Yazabilir, konuşabilir veya bir fotoğraf paylaşabilirsiniz.
          </span>
          <span className="role__action">Başla</span>
        </Link>

        <Link to="/caregiver" className="role role--caregiver">
          <span className="role__eyebrow">Bakım veren</span>
          <span className="role__title">Günün özetini gör</span>
          <span className="role__lead">
            Hastanın gün içindeki konuşmaları, rutin uyumu ve duygu durumu.
          </span>
          <ul className="role__list">
            <li>Konuşma kayıtları ve duygu etiketleri</li>
            <li>Rutin ve hatırlatıcı takibi</li>
            <li>Duygu durumu dağılımı</li>
          </ul>
          <span className="role__action">Panele git</span>
        </Link>
      </nav>

      <footer className="home__footer">
        <p className="home__disclaimer">
          OrientAI destek amaçlıdır; tıbbi tanı veya acil durum hizmeti değildir.
        </p>
        <p className="home__status">
          <span className={`status-dot status-dot--${backendStatus}`} aria-hidden="true" />
          {backendStatus === 'checking' && 'Sunucu bağlantısı kontrol ediliyor'}
          {backendStatus === 'online' && 'Sunucu bağlantısı aktif'}
          {backendStatus === 'offline' && 'Sunucuya bağlanılamadı'}
        </p>
      </footer>
    </div>
  )
}

export default HomePage