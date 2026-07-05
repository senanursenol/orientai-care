# Veritabanı Tasarımı

## Amaç

Bu veritabanı, hasta bakım ve takip sisteminde kullanılmak üzere tasarlanmıştır. Sistem; hasta bilgilerini, bakım veren bilgilerini, rutinleri, hatırlatıcıları ve günlük kayıtları düzenli bir şekilde saklamayı amaçlamaktadır.

## Tablolar

### caregivers (Bakım Verenler)

Bakım veren kişilere ait bilgileri saklar.

Alanlar:
- `caregiver_id` (Primary Key)
- `name`
- `email`
- `phone`

---

### patients (Hastalar)

Hastalara ait temel bilgileri saklar ve ilgili bakım verene bağlanır.

Alanlar:
- `patient_id` (Primary Key)
- `caregiver_id` (Foreign Key)
- `name`
- `birth_date`
- `disease`
- `created_at`

---

### routines (Rutinler)

Hastaların günlük veya periyodik rutinlerini saklar.

Alanlar:
- `routine_id` (Primary Key)
- `patient_id` (Foreign Key)
- `title`
- `description`
- `frequency`

---

### reminders (Hatırlatıcılar)

Rutinlere bağlı hatırlatıcı bilgilerini saklar.

Alanlar:
- `reminder_id` (Primary Key)
- `routine_id` (Foreign Key)
- `reminder_time`
- `is_active`

---

### logs (Günlük Kayıtlar)

Hastalara ait günlük gözlem, not ve durum kayıtlarını saklar.

Alanlar:
- `log_id` (Primary Key)
- `patient_id` (Foreign Key)
- `log_date`
- `note`
- `status`

---

## Tablolar Arası İlişkiler

- Bir bakım veren birden fazla hastadan sorumlu olabilir.
- Bir hasta birden fazla rutine sahip olabilir.
- Bir rutin birden fazla hatırlatıcı içerebilir.
- Bir hasta birden fazla günlük kayıt oluşturabilir.

## Anahtar Yapısı

### Primary Key (PK)
- `caregiver_id`
- `patient_id`
- `routine_id`
- `reminder_id`
- `log_id`

### Foreign Key (FK)
- `patients.caregiver_id → caregivers.caregiver_id`
- `routines.patient_id → patients.patient_id`
- `reminders.routine_id → routines.routine_id`
- `logs.patient_id → patients.patient_id`