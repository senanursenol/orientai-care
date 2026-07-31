# OrientAI Frontend

React (Vite) tabanlı frontend iskeleti. Hasta etkileşim ekranı, bakım veren
dashboardu ve hatırlatıcı yönetimi bu yapı üzerine ilerleyen sprintlerde
geliştirilecek.

## Kurulum ve Çalıştırma

```bash
cd mentes-web-app
npm install
npm run setup:ai
cp .env.example .env   # gerekirse API adreslerini güncelleyin
npm run dev
```

`npm run dev`, web uygulamasını `http://localhost:5173` ve yerel AI API'sini
`http://localhost:8000` adresinde birlikte başlatır. Yalnızca web arayüzünü
çalıştırmak için `npm run dev:web` kullanılabilir.
Çalıştırıcı `.env` dosyası varsa onu, yoksa `.env.example` dosyasını
otomatik kullanır.

## Klasör Yapısı

```
src/
├── components/    # Tekrar kullanılabilir UI parçaları (Header, Card, ComingSoon...)
├── pages/         # Route'lara karşılık gelen sayfalar (HomePage, PatientChatPage, CaregiverDashboardPage)
├── services/      # Backend API çağrıları (apiClient + servis dosyaları)
├── App.jsx        # Route tanımları
└── main.jsx       # Uygulama giriş noktası (BrowserRouter burada sarmalanır)
services/           # Yerel AI, RAG, STT, TTS, duygu ve görsel servisleri
prompts/            # AI sistem ve hasta asistanı promptları
ai_api.py           # FastAPI giriş noktası
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
`VITE_API_BASE_URL` değişkeninden okunur. Hasta asistanının metin, ses,
fotoğraf ve TTS istekleri ise `src/services/aiService.js` üzerinden
`VITE_AI_API_BASE_URL` adresine gider. Bu değer boşsa geliştirme sunucusu
istekleri `/ai-api` proxy'siyle `http://127.0.0.1:8000/api` adresine aktarır.
Backend henüz ayakta değilse
ana sayfadaki bağlantı durumu "offline" görünecektir; bu beklenen bir
durumdur ve backend hazır olduğunda otomatik olarak "online" olacaktır.
