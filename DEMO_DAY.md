# Pineapple Corp — Demo Day Runbook

## Prerequisites

- Python environment with dependencies installed (`pip install -r RAG-Chatbot/requirements.txt`)
- cloudflared installed (`winget install cloudflare.cloudflared`)
- GPU machine with CUDA (model runs on local GPU)
- Vercel project linked to GitHub: https://github.com/ryanflash66/pineapple-corp-dashboard
- Dashboard URL: https://pineapple-corp.vercel.app

---

## Step 1: Start the backend

Open a terminal:

```bash
cd RAG-Chatbot
uvicorn dashboard:app --port 8050
```

Wait for the model to finish loading (you'll see the Unsloth/LoRA output and `Uvicorn running on http://0.0.0.0:8050`).

Verify it works: open http://localhost:8050 in your browser.

## Step 2: Start the tunnel

Open a **second terminal**:

```bash
cloudflared tunnel --url http://localhost:8050
```

It will print something like:

```
Your quick Tunnel has been created! Visit it at:
https://something-random-words.trycloudflare.com
```

Copy that URL.

## Step 3: Set the tunnel URL in Vercel

1. Go to https://vercel.com/ryanflash66s-projects/pineapple-corp/settings/environment-variables
2. Set `CHAT_BACKEND` to your tunnel URL **with `/chat` appended**, e.g.:
   ```
   https://something-random-words.trycloudflare.com/chat
   ```
3. Go to https://vercel.com/ryanflash66s-projects/pineapple-corp/deployments
4. Click the **three dots** on the latest deployment → **Redeploy**

Wait ~15 seconds for the deploy to finish.

## Step 4: Verify

Open https://pineapple-corp.vercel.app — the chat iframe should load with the AI assistant. Try asking it something like:

> "Generate an incident response playbook for a ransomware attack on our file server"

## Step 5: Share with audience

Share this link via QR code or in chat:

```
https://pineapple-corp.vercel.app
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Chat shows "AI Chat Offline" | Check that both terminals (uvicorn + cloudflared) are still running |
| Tunnel URL changed | cloudflared quick tunnels give a new URL each session — update the `CHAT_BACKEND` env var in Vercel and redeploy |
| Model takes too long to load | Normal on first run (~2-5 min). The tunnel can start before the model finishes loading |
| Dashboard looks fine but chat won't connect | Make sure you appended `/chat` to the tunnel URL in the env var |
| Theme toggle doesn't sync to chat | The iframe needs to fully load first — give it a few seconds |

## Architecture

```
Audience → pineapple-corp.vercel.app (static dashboard)
               ↓ iframe src from CHAT_BACKEND env var
           cloudflared tunnel
               ↓
           localhost:8050 (uvicorn + Chainlit + Llama 3.1 8B LoRA)
```
