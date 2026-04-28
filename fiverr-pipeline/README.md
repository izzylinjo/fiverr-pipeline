# fiverr-pipeline

Automated Fiverr order pipeline. Receives orders via webhook, writes task files, builds deliverables using Claude Code, deploys automatically.

## Stack
- n8n (workflow automation) — main PC
- Groq Llama 3.3 70B (thought layer, primary) — free
- Gemini Flash (thought layer, fallback) — free
- Python Flask (webhook bridge) — second PC
- Claude Code via Claude desktop (build agent) — Pro plan, free
- Vercel (landing page deployment) — free tier

## Upgrade path
When revenue justifies it: swap Groq/Gemini for Claude Haiku API, move to a VPS, add Discord bot for two-way control.

---

## Setup order

### 1. Second PC (local build machine)
```
git clone https://github.com/YOUR_USERNAME/fiverr-pipeline.git
cd fiverr-pipeline
pip install -r bridge/requirements.txt
pip install -r watcher/requirements.txt
```
Create folders:
```
mkdir tasks tasks/done output logs
```
Start the bridge:
```
python bridge/bridge.py
```
Confirm it works:
```
http://localhost:8000/health
```
Start the watcher:
```
python watcher/watcher.py
```

### 2. Main PC (n8n workflow)
```
npm install -g n8n pm2
n8n start
```
Open http://localhost:5678 → import n8n/workflow.json → add credentials → activate.

### 3. Expose bridge for testing
```
ngrok http 8000
```
Copy the ngrok URL → paste into n8n Node 9 (POST to bridge).

### 4. Test end to end
Drop a file into /tasks manually or send a test webhook:
```
curl -X POST http://localhost:8000/new-order \
  -H "Content-Type: application/json" \
  -d '{"project_name":"test-bot","requirements":"Build a ping bot","client_name":"testclient","deadline_hours":48}'
```
Check /tasks for the new .md file.
Open Claude desktop → paste CLAUDE.md contents → say: "process the next task in /tasks"

---

## Folder structure

```
fiverr-pipeline/
  CLAUDE.md                   Claude's standing instructions (read every session)
  README.md                   This file
  .gitignore                  Keeps keys and client data out of git
  .env.example                Template for environment variables
  bridge/
    bridge.py                 Flask webhook server — receives n8n orders
    install_service.py        Windows service installer for bridge
    requirements.txt          flask, pywin32
  watcher/
    watcher.py                Watches /tasks, sends desktop notifications
    requirements.txt          plyer
  n8n/
    workflow.json             Exportable n8n workflow — import directly
    workflow_guide.md         Node by node setup instructions
  tasks/                      GITIGNORED — incoming order briefs
  tasks/done/                 GITIGNORED — processed briefs archive
  output/                     GITIGNORED — completed deliverables
  logs/                       GITIGNORED — bridge and watcher logs
  docs/
    architecture.md           How the whole system fits together
    upgrade_path.md           Steps to move to VPS + Haiku + Discord bot
```

---

## Environment variables

Copy .env.example to .env and fill in your keys. Never commit .env.

```
GROQ_API_KEY=
GEMINI_API_KEY=
DISCORD_WEBHOOK_URL=
BRIDGE_PORT=8000
PIPELINE_ROOT=C:\fiverr-pipeline
```

---

## Daily use

1. Fiverr order arrives
2. n8n detects it → Groq classifies it → bridge writes /tasks/order.md
3. Desktop notification fires (watcher.py)
4. Open Claude desktop → "process the next task in /tasks"
5. Claude estimates complexity → builds → tests → moves to /output
6. You review /output → approve
7. n8n delivers to client + schedules review follow-up

---

## Keys needed

| Key | Where to get it | Cost |
|-----|----------------|------|
| Groq API key | console.groq.com | Free |
| Gemini API key | aistudio.google.com | Free |
| Discord webhook | Discord channel settings | Free |
| ngrok authtoken | ngrok.com | Free |

---

## Costs

| Component | Cost |
|-----------|------|
| n8n self-hosted | $0 |
| Groq API | ~$0.01/order |
| Gemini API | $0 fallback only |
| Claude Code builds | $0 (Pro plan) |
| Vercel deployment | $0 free tier |
| Total | ~pennies/day |
