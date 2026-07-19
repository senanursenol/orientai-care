import Card from './Card'
import './ComingSoon.css'

/**
 * PatientChatPage ve CaregiverDashboardPage gibi henüz backend'i
 * hazır olmayan sayfalarda placeholder olarak kullanılır.
 * İlgili sprint'te gerçek UI ile değiştirilir.
 */
function ComingSoon({ icon, title, description, sprintLabel }) {
  return (
    <div className="coming-soon">
      <Card>
        <div className="coming-soon__icon" aria-hidden="true">{icon}</div>
        <h2 className="coming-soon__title">{title}</h2>
        <p className="coming-soon__description">{description}</p>
        {sprintLabel && <span className="coming-soon__badge">{sprintLabel}</span>}
      </Card>
    </div>
  )
}

export default ComingSoon
