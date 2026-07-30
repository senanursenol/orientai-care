# mentes-service (Node.js Backend)

## Local Çalıştırma

```bash
cd services/mentes-service
npm install
cp .env.example .env
npm run dev
```

Backend `http://localhost:5000` üzerinde ayağa kalkar.

## Health Check

```bash
curl http://localhost:5000/api/health
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
`{ "status": "ok", "transcript": "...", "answer": "...", "context": [...], "audioUrl": "..." }`

## Python AI servisi (mentes-ai-service) kontratı

`AI_SERVICE_URL` üzerinden çağrılan, `src/infrastructure/ai-client/ai-client.js`'in beklediği format:

- `POST /api/rag/chat` → `{ patient_id, message }` → `{ answer, context: [{ content, metadata }] }`
- `POST /api/stt` → multipart `audio` → `{ transcript }`
- `POST /api/tts` → `{ text }` → `{ audio_url }`

Python servisi hazır olmadan geliştirmek için `.env`'de `AI_MOCK=true` kullanılabilir.

## Konuşma logları

`/api/chat` ve `/api/voice-chat`, `DATABASE_URL` üzerinden `interaction_logs` tablosuna
(bkz. `db-schemas/01-patient-care-schema.sql`) fire-and-forget olarak yazar — DB erişilemezse
istek yine de normal yanıt döner, hata sadece console'a loglanır (bkz. `routes/chat-route.js`).
