import './Card.css'

/**
 * Genel amaçlı kart componenti. Caregiver dashboard'daki
 * özet kartları ve patient ekranındaki mesaj balonları gibi
 * ileride birçok yerde tekrar kullanılabilir.
 */
function Card({ title, children, className = '' }) {
  return (
    <div className={`card ${className}`.trim()}>
      {title && <h3 className="card__title">{title}</h3>}
      <div className="card__body">{children}</div>
    </div>
  )
}

export default Card
