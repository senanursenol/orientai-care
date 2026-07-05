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
