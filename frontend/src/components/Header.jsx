import { NavLink } from 'react-router-dom'
import './Header.css'

/**
 * Uygulama genelinde kullanılan üst navigasyon.
 * Hasta chat ve caregiver dashboard sayfaları eklendikçe
 * buraya yeni NavLink'ler eklenmesi yeterli.
 */
function Header() {
  return (
    <header className="app-header">
      <div className="app-header__brand">
        <span className="app-header__icon" aria-hidden="true">🧭</span>
        <span className="app-header__title">OrientAI</span>
      </div>
      <nav className="app-header__nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
          Ana Sayfa
        </NavLink>
        <NavLink to="/patient" className={({ isActive }) => (isActive ? 'active' : '')}>
          Hasta Ekranı
        </NavLink>
        <NavLink to="/caregiver" className={({ isActive }) => (isActive ? 'active' : '')}>
          Bakım Veren Paneli
        </NavLink>
      </nav>
    </header>
  )
}

export default Header
