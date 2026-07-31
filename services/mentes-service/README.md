# mentes-service (Node.js Backend)

## Local Çalıştırma

```bash
cd services/mentes-service
npm install
cp .env.example .env
npm run dev
```

Backend `http://localhost:4100` üzerinde ayağa kalkar.

## Health Check

```bash
curl http://localhost:4100/api/health
```

Beklenen yanıt:

```json
{ "status": "ok", "service": "mentes-service", "timestamp": "..." }
```

## Endpoints

### `POST /api/chat` (ORI-21)

```json
{ "patientId": "P-1001", "message": "Torunum nerede okuyor?" }
```
→ `{ "status": "ok", "answer": "...", "context": [...] }`

### `POST /api/voice-chat` (ORI-22)

`multipart/form-data`: `patientId` (text), `audio` (dosya) →
`{ "status": "ok", "transcript": "...", "answer": "...", "context": [...] }`

### `POST /api/tts`

```json
{ "text": "Merhaba, nasılsınız?" }
```
→ ses (audio/mpeg, binary)

### `POST /api/vision/describe`

`multipart/form-data`: `patientId` (text), `image` (dosya) →
`{ "status": "ok", "description": "...", "model": "..." }`

## Python AI servisi (mentes-ai-service) kontratı

`AI_SERVICE_URL` (varsayılan `http://localhost:4200`) üzerinden çağrılan,
`src/infrastructure/ai-client/ai-client.js`'in beklediği format
(bkz. `services/mentes-ai-service/app/api/app.py`):

- `POST /api/chat/text` → `{ text, patient_id }` → conversation result (RAG destekli)
- `POST /api/chat/voice` → multipart `audio` + `patient_id` → conversation result + transcript
- `POST /api/vision/describe` → multipart `image` + `patient_id` → `{ description, model }`
- `POST /api/tts/synthesize` → `{ text }` → audio/mpeg (binary)
- `POST /api/rag/chat` → `{ patient_id, message }` → `{ answer, context: [{ content, metadata }] }`

Python servisi hazır olmadan geliştirmek için `.env`'de `AI_MOCK=true` kullanılabilir.

## Konuşma logları

`/api/chat` ve `/api/voice-chat`, `DATABASE_URL` üzerinden `interaction_logs` tablosuna
(bkz. `db-schemas/01-patient-care-schema.sql`) fire-and-forget olarak yazar — DB erişilemezse
istek yine de normal yanıt döner, hata sadece console'a loglanır (bkz. `routes/chat-route.js`).
