import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import HomePage from './pages/HomePage'
import PatientChatPage from './pages/PatientChatPage'
import CaregiverDashboardPage from './pages/CaregiverDashboardPage'

/**
 * Uygulamanın route tanımları burada tutulur.
 * Yeni bir sayfa eklemek için:
 *   1. src/pages altına yeni sayfa componenti oluştur
 *   2. Aşağıya <Route> ekle
 *   3. Gerekirse Header.jsx içine navigasyon linki ekle
 */
function App() {
  return (
    <>
      <Header />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/patient" element={<PatientChatPage />} />
          <Route path="/caregiver" element={<CaregiverDashboardPage />} />
        </Routes>
      </main>
    </>
  )
}

export default App
