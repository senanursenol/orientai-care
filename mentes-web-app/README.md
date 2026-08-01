# OrientAI Frontend

React (Vite) tabanlı frontend iskeleti. Hasta etkileşim ekranı, bakım veren
dashboardu ve hatırlatıcı yönetimi bu yapı üzerine ilerleyen sprintlerde
geliştirilecek.

## Kurulum ve Çalıştırma

```bash
cd mentes-web-app
npm install
cp .env.example .env   # gerekirse API adresini güncelleyin
npm run dev
```

`npm run dev`, web uygulamasını `http://localhost:5173`'te başlatır.
Bu uygulama Python AI servisini içermez/başlatmaz — AI (chat, ses, görsel,
TTS) istekleri de dahil olmak üzere tüm istekler Node backend'ine
(`services/mentes-service`) gider; Node gerektiğinde Python AI servisine
(`services/mentes-ai-service`) köprü kurar. Üç servisi ayrı ayrı
çalıştırmak gerekir (bkz. kök `README.md`).

## Klasör Yapısı

```
src/
├── api/           # Backend API çağrıları (apiClient + servis dosyaları)
├── components/    # Tekrar kullanılabilir UI parçaları (Header, Card, ComingSoon...)
├── pages/         # Route'lara karşılık gelen sayfalar (HomePage, PatientChatPage, CaregiverDashboardPage)
├── App.jsx        # Route tanımları
└── main.jsx       # Uygulama giriş noktası (BrowserRouter burada sarmalanır)
```

## Yeni Sayfa Ekleme

1. `src/pages/` altına yeni sayfa componentini oluştur.
2. `src/App.jsx` içine `<Route>` ekle.
3. Gerekirse `src/components/Header.jsx` içine navigasyon linki ekle.
4. Sayfanın ihtiyaç duyduğu API çağrılarını `src/api/` altında ayrı bir
   dosyada topla (bkz. `patientService.js`, `caregiverService.js` örnekleri).

## Backend Bağlantısı

Tüm API istekleri (metin/ses/fotoğraf sohbeti, TTS dahil) `src/api/apiClient.js`
içindeki ortak axios instance'ı üzerinden **yalnızca Node backend'ine**
(`services/mentes-service`) gider — `VITE_API_BASE_URL` (`.env`) bu adresi
belirler. Frontend'in Python AI servisine (`services/mentes-ai-service`)
doğrudan bir bağlantısı yoktur; Node köprüyü kurar (bkz.
`services/mentes-service/README.md`). Backend henüz ayakta değilse
ana sayfadaki bağlantı durumu "offline" görünecektir; bu beklenen bir
durumdur ve backend hazır olduğunda otomatik olarak "online" olacaktır.
