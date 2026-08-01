import { NavLink } from 'react-router-dom'
import BrandMark from './BrandMark'
import './Header.css'

/**
 * Uygulama genelinde kullanılan üst navigasyon.
 *
 * Header yapışkan (sticky): bakım veren paneli uzun bir sayfa, aşağı
 * kaydırıldığında hasta ekranına geçmek için başa dönmek gerekmesin.
 * Yeni sayfa eklendikçe buraya bir NavLink eklenmesi yeterli.
 */
function Header() {
  return (
    <header className="app-header">
      <NavLink to="/" className="app-header__brand">
        <BrandMark size={26} className="app-header__mark" />
        <span className="app-header__title">OrientAI</span>
      </NavLink>

      <nav className="app-header__nav" aria-label="Ana gezinme">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
          Ana sayfa
        </NavLink>
        <NavLink to="/patient" className={({ isActive }) => (isActive ? 'active' : '')}>
          Hasta ekranı
        </NavLink>
        <NavLink to="/caregiver" className={({ isActive }) => (isActive ? 'active' : '')}>
          Bakım veren paneli
        </NavLink>
      </nav>
    </header>
  )
}

export default Header