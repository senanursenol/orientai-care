# Hasta Bakım ve Takip Sistemi Veritabanı

Bu proje, hasta bakım ve takip sisteminde kullanılacak temel veritabanı yapısını içermektedir.

## İçerik

Sistemde aşağıdaki bilgiler saklanmaktadır:

- Hasta bilgileri
- Bakım veren bilgileri
- Hasta rutinleri
- Hatırlatıcılar
- Günlük kayıtlar (loglar)

## Veritabanı Yapısı

Veritabanı şeması aşağıdaki dosyada bulunmaktadır:

```text
database/schema.sql
```

Veritabanı tasarımına ait açıklamalar ise aşağıdaki dosyada yer almaktadır:

```text
docs/database-design.md
```

## Tablolar

- `caregivers`
- `patients`
- `routines`
- `reminders`
- `logs`

## Tablolar Arası İlişkiler

- Bir bakım veren birden fazla hastadan sorumlu olabilir.
- Bir hasta birden fazla rutine sahip olabilir.
- Bir rutin birden fazla hatırlatıcı içerebilir.
- Bir hasta birden fazla günlük kayıt oluşturabilir.

## Kullanılan Teknolojiler

- PostgreSQL 17
- pgAdmin 4
- SQL