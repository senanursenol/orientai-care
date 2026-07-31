import Card from '../../../components/Card'
import { calculateAge } from '../utils/dashboardMetrics'
import './PatientSummaryCard.css'

/**
 * ORI-32: "Hastanın temel bilgileri gösterilmeli."
 *
 * Panelin en üstünde duran kimlik şeridi. Bakım veren paneli açtığında ilk
 * soru "kimin verisine bakıyorum" olduğu için isim ve tanı en yüksek
 * kontrastta, geri kalan bağlam sessiz tonda veriliyor.
 */

function initials(name = '') {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] || '')
    .join('')
    .toLocaleUpperCase('tr-TR')
}

function PatientSummaryCard({ patient }) {
  if (!patient) return null

  const age = calculateAge(patient.birth_date)
  const caregiver = patient.caregiver

  const context = [
    age !== null ? `${age} yaşında` : null,
    patient.disease,
    patient.disease_stage ? `${patient.disease_stage} seyir` : null,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <Card className="patient-summary">
      <div className="patient-summary__identity">
        <span className="patient-summary__avatar" aria-hidden="true">
          {initials(patient.name)}
        </span>
        <div className="patient-summary__names">
          <h2 className="patient-summary__name">{patient.name}</h2>
          <p className="patient-summary__context">{context}</p>
        </div>
        {caregiver && (
          <div className="patient-summary__caregiver">
            <span className="patient-summary__caregiver-label">Bakım veren</span>
            <span className="patient-summary__caregiver-name">{caregiver.name}</span>
            {caregiver.relation && (
              <span className="patient-summary__caregiver-relation">{caregiver.relation}</span>
            )}
          </div>
        )}
      </div>

      <dl className="patient-summary__details">
        {patient.former_profession && (
          <div className="patient-summary__detail">
            <dt>Eski meslek</dt>
            <dd>{patient.former_profession}</dd>
          </div>
        )}
        {patient.living_status && (
          <div className="patient-summary__detail">
            <dt>Yaşam durumu</dt>
            <dd>{patient.living_status}</dd>
          </div>
        )}
        {caregiver?.phone && (
          <div className="patient-summary__detail">
            <dt>İletişim</dt>
            <dd>{caregiver.phone}</dd>
          </div>
        )}
      </dl>
    </Card>
  )
}

export default PatientSummaryCard
