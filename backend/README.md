# Deploying the Backend to Vercel

Prerequisites:

- Python 3.10+ installed locally
- `requirements.txt` present in this `backend/` folder
- Node.js + `npm` (for Vercel CLI installation) or use `npx`

Quick deploy (recommended):

1. Install/vercel login

```bash
npm install -g vercel
vercel login
```

2. From this folder, test locally with Vercel dev:

```bash
cd backend
vercel dev
```

3. Deploy to production:

```bash
cd backend
vercel --prod
```

Environment variables:

- Vercel does not automatically read your local `.env`. Add required keys in the Vercel dashboard under Project Settings → Environment Variables, or use the CLI:

```bash
vercel env add <KEY> production
```

Notes & troubleshooting:

- The `vercel.json` routes requests to `main.py`. Ensure `main.py` exposes a WSGI/ASGI-compatible handler or uses frameworks compatible with `@vercel/python`.
- Native binary dependencies (for example `faiss`) may not be supported on Vercel serverless. If your app depends on those, consider using a VM-style host (Render, Railway, or a Docker-capable provider).

If you want, I can also add a small `Procfile` or example `main.py` entry wrapper for Vercel compatibility.
