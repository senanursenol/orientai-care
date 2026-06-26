# orientai-care
# OrientAI: Multimodal Orientation and Memory Support Assistant

## Takım İsmi

Team OrientAI

## Takım Üyeleri

| İsim | Rol |
|---|---|
| Üye 1 | Product Owner & Veri Tasarımcısı |
| Üye 2 | AI & Model Entegrasyon Geliştiricisi |
| Üye 3 | Backend Developer |
| Üye 4 | Database & RAG Developer |
| Üye 5 | Frontend & UI Developer |

> Takım üyelerinin gerçek isimleri daha sonra eklenecektir.

---

## Ürün İsmi

**OrientAI**

---

## Ürün Açıklaması

OrientAI, hafif ve orta seviye demans hastalarının günlük yaşamda karşılaştığı unutkanlık, yönelim kaybı ve rutin takibi problemlerini azaltmak amacıyla geliştirilen çoklu modal yapay zeka destekli bilişsel destek asistanıdır.

Sistem; sesli etkileşim, görsel anlama, kişisel hafıza desteği, günlük rutin takibi, duygu durumu analizi ve bakım veren kontrol paneli özelliklerini bir araya getirir. Böylece hem hastanın günlük yaşamını desteklemeyi hem de bakım veren kişinin hastanın durumu hakkında daha düzenli içgörü elde etmesini amaçlar.

---

## Ürün Özellikleri

- Sesli soru-cevap desteği
- Whisper tabanlı konuşmadan metne dönüştürme
- TTS ile sesli yanıt üretimi
- RAG tabanlı kişisel hafıza desteği
- Sentetik hasta persona yönetimi
- Günlük rutin ve ilaç hatırlatma sistemi
- Görsel analiz ve fotoğraf açıklama modülü
- Görsel üzerinden anı terapisi akışı
- Bakım veren kontrol paneli
- Duygu durumu analizi
- Konuşma ve rutin loglarının takibi
- Çift ajanlı hasta simülasyonu
- Halüsinasyon ve güvenlik testleri

---

## Hedef Kitle

- Hafif ve orta seviye demans hastaları
- Alzheimer hastaları
- Bakım veren aile üyeleri
- Yaşlı bakım merkezleri
- Klinik karar verici olmayan bilişsel destek sistemleri

---

## Kullanılan Teknolojiler

| Alan | Teknoloji |
|---|---|
| Backend | FastAPI, Python |
| Frontend | Streamlit |
| Speech-to-Text | Whisper |
| Text-to-Speech | TTS servisleri |
| Multimodal AI | LLaVA / Vision API |
| RAG | ChromaDB |
| Database | PostgreSQL / SQL Server |
| Project Management | Jira |
| Version Control | Git & GitHub |

---

## Product Backlog URL

[Jira Product Backlog](BURAYA_JIRA_LINKI_EKLENECEK)

---

# Sprint 1

## Sprint İsmi

**Sprint 1 - Altyapı ve Veri Mimarisi**

## Sprint Amacı

Sprint 1’in amacı; proje klasör yapısını, FastAPI backend iskeletini, veritabanı tasarımını, sentetik hasta persona yapısını ve ChromaDB tabanlı RAG başlangıç altyapısını oluşturmaktır.

## Sprint İçinde Tamamlanması Tahmin Edilen Puan

**100 Story Point**

## Sprint Backlog

- Proje klasör yapısının oluşturulması
- FastAPI backend iskeletinin kurulması
- Health check endpointinin oluşturulması
- Veritabanı tablo tasarımının hazırlanması
- Kullanıcı, hasta, rutin ve log tablolarının oluşturulması
- Sentetik hasta persona JSON şemasının hazırlanması
- Örnek sentetik hasta profillerinin oluşturulması
- ChromaDB vektör veritabanı yapısının hazırlanması
- Persona verilerinin vektör veritabanına indekslenmesi
- README başlangıç dokümantasyonunun hazırlanması
- Requirements ve .gitignore dosyalarının hazırlanması
- Backend environment ayarlarının oluşturulması
- Sprint 1 board ekran görüntülerinin README için hazırlanması
- Sprint 1 review ve retrospective notlarının yazılması

## Sprint Board Screenshot

![Sprint 1 Backlog](assets/sprint_boards/sprint_1_backlog.png)

## Sprint Review

Sprint sonunda doldurulacaktır.

## Sprint Retrospective

Sprint sonunda doldurulacaktır.

---

# Sprint 2

## Sprint İsmi

**Sprint 2 - LLM, RAG ve Sesli Etkileşim**

## Sprint Amacı

Sprint 2’nin amacı; Whisper STT, TTS, RAG destekli LLM sohbeti, sesli soru-cevap akışı ve duygu durumu analizi modüllerini geliştirerek sistemin MVP seviyesinde hasta ile etkileşime girebilmesini sağlamaktır.

## Sprint İçinde Tamamlanması Tahmin Edilen Puan

**100 Story Point**

## Sprint Backlog

- Whisper STT servis entegrasyonunun yapılması
- TTS servis entegrasyonunun yapılması
- Sesli soru-cevap akışının oluşturulması
- RAG retriever servisinin geliştirilmesi
- LLM prompt yapısının RAG bağlamına uygun hazırlanması
- Hafıza destekli sohbet endpointinin oluşturulması
- Sesli sohbet endpointinin oluşturulması
- Konuşma geçmişinin veritabanına kaydedilmesi
- Duygu durumu analizi modülünün geliştirilmesi
- Kaygılı veya negatif duygu içeren konuşmaların işaretlenmesi
- Sprint 2 demo çıktıları için ekran görüntülerinin hazırlanması
- Sprint 2 review ve retrospective notlarının yazılması

## Sprint Board Screenshot

![Sprint 2 Backlog](assets/sprint_boards/sprint_2_backlog.png)

## Sprint Review

Sprint sonunda doldurulacaktır.

## Sprint Retrospective

Sprint sonunda doldurulacaktır.

---

# Sprint 3

## Sprint İsmi

**Sprint 3 - Görsel Anlama, Dashboard ve Final Testleri**

## Sprint Amacı

Sprint 3’ün amacı; görsel analiz, fotoğraf açıklama, anı terapisi, bakım veren dashboardu, çift ajanlı hasta simülasyonu, halüsinasyon/güvenlik testleri ve final demo çıktısını tamamlamaktır.

## Sprint İçinde Tamamlanması Tahmin Edilen Puan

**100 Story Point**

## Sprint Backlog

- LLaVA veya Vision API entegrasyonunun yapılması
- Fotoğraf açıklama modülünün oluşturulması
- Görsel üzerinden anı terapisi akışının geliştirilmesi
- Görsel analiz sonucunun RAG hafıza sistemiyle bağlanması
- Streamlit bakım veren dashboardunun oluşturulması
- Hasta etkileşim ekranı simülasyonunun hazırlanması
- Hatırlatıcı yönetim ekranının geliştirilmesi
- Duygu durumu grafiklerinin dashboarda eklenmesi
- Konuşma ve rutin loglarının dashboardda gösterilmesi
- Çift ajanlı hasta simülatörünün oluşturulması
- Asistan ajanı değerlendirme akışının oluşturulması
- Halüsinasyon ve güvenlik testlerinin yapılması
- Final demo senaryosunun hazırlanması
- Sprint 3 ürün ekran görüntülerinin README için hazırlanması
- Sprint 3 review ve retrospective notlarının yazılması

## Sprint Board Screenshot

![Sprint 3 Backlog](assets/sprint_boards/sprint_3_backlog.png)

## Sprint Review

Sprint sonunda doldurulacaktır.

## Sprint Retrospective

Sprint sonunda doldurulacaktır.

---

## Etik ve KVKK Notu

Bu proje geliştirme ve test aşamalarında gerçek hasta verisi kullanmaz. Kullanılan hasta profilleri, anılar, rutinler ve konuşma örnekleri sentetik olarak oluşturulacaktır. Proje klinik karar verme amacı taşımaz; bilişsel destek, günlük yaşam asistanlığı ve bakım veren bilgilendirme prototipi olarak tasarlanmıştır.

---

## Proje Durumu

Proje geliştirme aşamasındadır.
