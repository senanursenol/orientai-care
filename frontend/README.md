# OrientAI Frontend

React (Vite) tabanlı frontend iskeleti. Hasta etkileşim ekranı, bakım veren
dashboardu ve hatırlatıcı yönetimi bu yapı üzerine ilerleyen sprintlerde
geliştirilecek.

## Kurulum ve Çalıştırma

```bash
cd frontend
npm install
cp .env.example .env   # gerekirse VITE_API_BASE_URL güncelleyin
npm run dev
```

Uygulama varsayılan olarak `http://localhost:5173` adresinde açılır.

## Klasör Yapısı

```
src/
├── components/    # Tekrar kullanılabilir UI parçaları (Header, Card, ComingSoon...)
├── pages/         # Route'lara karşılık gelen sayfalar (HomePage, PatientChatPage, CaregiverDashboardPage)
├── services/      # Backend API çağrıları (apiClient + servis dosyaları)
├── App.jsx        # Route tanımları
└── main.jsx       # Uygulama giriş noktası (BrowserRouter burada sarmalanır)
```

## Yeni Sayfa Ekleme

1. `src/pages/` altına yeni sayfa componentini oluştur.
2. `src/App.jsx` içine `<Route>` ekle.
3. Gerekirse `src/components/Header.jsx` içine navigasyon linki ekle.
4. Sayfanın ihtiyaç duyduğu API çağrılarını `src/services/` altında ayrı bir
   dosyada topla (bkz. `patientService.js`, `caregiverService.js` örnekleri).

## Backend Bağlantısı

Tüm API istekleri `src/services/apiClient.js` içindeki ortak axios
instance'ı üzerinden yapılır. Base URL `.env` dosyasındaki
`VITE_API_BASE_URL` değişkeninden okunur. Backend henüz ayakta değilse
ana sayfadaki bağlantı durumu "offline" görünecektir; bu beklenen bir
durumdur ve backend hazır olduğunda otomatik olarak "online" olacaktır.
