# Master Handoff — Exact Order for Claude Desktop
# Read this first. Follow it exactly. Do not skip steps.

---

## Before you open Claude desktop

Have these ready:
- [ ] Groq API key (get from console.groq.com)
- [ ] Gemini API key (get from aistudio.google.com)
- [ ] Discord webhook URL (get from your Discord channel settings)
- [ ] Git installed on both PCs (git-scm.com)
- [ ] Python installed on second PC (python.org — get 3.11+)
- [ ] Node.js installed on main PC (nodejs.org — get LTS version)
- [ ] ngrok account created (ngrok.com — free)

---

## SESSION 1 — Second PC (the build machine)
### Goal: get the bridge running and repo cloned

Open Claude desktop on the second PC.
Paste this exactly:

---
"I am setting up a Fiverr automation pipeline on this PC. This is the local build machine. Please help me do the following in order:

1. Create a GitHub repository called fiverr-pipeline (guide me through this if I haven't done it)
2. Clone it to C:\fiverr-pipeline
3. Create this exact folder structure inside it:
   - bridge/
   - watcher/
   - n8n/
   - docs/
   - tasks/ (gitignored)
   - tasks/done/ (gitignored)
   - output/ (gitignored)
   - logs/ (gitignored)

4. Write the following files exactly as I give them to you — I will paste them one at a time
5. After all files are written, install dependencies and start the bridge
6. Confirm the bridge is working by hitting the health endpoint

Ask me for each file one at a time. Start by asking me for README.md"
---

Then paste each file when Claude asks for it, in this order:
1. README.md
2. .gitignore
3. .env.example
4. CLAUDE.md
5. bridge/bridge.py
6. bridge/install_service.py
7. bridge/requirements.txt
8. watcher/watcher.py
9. watcher/requirements.txt

After all files are written, tell Claude:
"Now install the dependencies and start the bridge. Tell me the exact commands to run."

Then run the commands it gives you.
Confirm the bridge is alive: open browser → http://localhost:8000/health
You should see: {"status": "running", "pending_tasks": 0}

Then tell Claude:
"Now help me set up ngrok so n8n can reach this bridge from the other PC."

Then commit everything:
"Now help me commit all these files to git and push to GitHub."

SESSION 1 IS DONE when:
- [ ] Bridge is running at localhost:8000
- [ ] Health endpoint returns OK
- [ ] ngrok is running and you have a public URL
- [ ] Everything is pushed to GitHub

---

## SESSION 2 — Second PC (same machine)
### Goal: test the bridge with a fake order

Open Claude desktop.
Paste this:

---
"I have a Flask bridge running at localhost:8000 for my Fiverr pipeline. 
I want to test it by sending a fake webhook order. 
Please send a test POST request to http://localhost:8000/new-order with realistic fake order data for a Discord bot project. 
Then check C:\fiverr-pipeline\tasks\ and confirm the .md file was written correctly.
Then read the file and process it as if it were a real order — estimate complexity, build a simple test Discord bot, save output to C:\fiverr-pipeline\output\test-discord-bot\"
---

SESSION 2 IS DONE when:
- [ ] Fake order webhook worked
- [ ] .md file appeared in /tasks
- [ ] Claude built something and put it in /output
- [ ] You reviewed the output and it looks right

---

## SESSION 3 — Main PC (the n8n machine)
### Goal: install n8n and build the workflow

Open Claude desktop on your main PC.
Paste this:

---
"I am setting up n8n on this PC as part of a Fiverr automation pipeline. 
Please help me:
1. Install n8n using npm
2. Install pm2 to keep it running in the background
3. Start n8n and confirm it opens at localhost:5678
4. I will then paste you the full workflow setup guide and you walk me through building it node by node

Here are my credentials:
- Groq API key: PASTE_YOUR_KEY_HERE
- Gemini API key: PASTE_YOUR_KEY_HERE  
- Discord webhook URL: PASTE_YOUR_URL_HERE
- Bridge URL (ngrok): PASTE_YOUR_NGROK_URL_HERE

After n8n is installed, ask me to paste the workflow guide."
---

Then paste the full contents of n8n/workflow_guide.md when it asks.

Tell Claude to walk you through each node one at a time.
Do not rush this — build one node, confirm it, then move to the next.

SESSION 3 IS DONE when:
- [ ] n8n is installed and running
- [ ] All 12 nodes are built
- [ ] Workflow tested with a fake Gmail trigger
- [ ] Fake order flowed all the way through to /tasks on second PC
- [ ] Discord notification received
- [ ] Workflow set to Active

---

## SESSION 4 — Second PC
### Goal: set up the watcher and Claude routine

Open Claude desktop on the second PC.
Paste this:

---
"The pipeline is now connected. n8n is running on my main PC and sending webhooks to the bridge on this PC. 
Now I need to:
1. Start watcher.py in the background so I get desktop notifications when new tasks arrive
2. Set up the CLAUDE.md routine so you automatically know what to do each session
3. Do a full end to end test — I will trigger a fake order from n8n and we process it together

Start by reading CLAUDE.md in C:\fiverr-pipeline\ and confirm you understand the standing instructions."
---

SESSION 4 IS DONE when:
- [ ] Watcher is running and you got a test desktop notification
- [ ] Claude read CLAUDE.md and confirmed the rules
- [ ] Full end to end test completed — fake order → webhook → tasks file → Claude built it → output folder
- [ ] You are confident you could process a real order

---

## SESSION 5 — Any PC
### Goal: post your Fiverr gigs

This session has nothing to do with code.

Open Claude desktop.
Paste this:

---
"I have finished setting up my Fiverr automation pipeline. Now I need to post my first two Fiverr gigs today. 
I have the gig descriptions already written. Please help me:
1. Review gig 1 (landing page) and gig 2 (Discord bot) descriptions
2. Suggest the best thumbnail strategy for each
3. Help me write my Fiverr profile bio
4. Remind me of the pricing strategy — start cheap, raise after reviews

Here are the gig descriptions: [paste from the fiverr_gigs_with_bots.html content]"
---

SESSION 5 IS DONE when:
- [ ] Fiverr account created
- [ ] Gig 1 (landing page) posted and live
- [ ] Gig 2 (Discord bot) posted and live
- [ ] Profile bio written and saved
- [ ] Reddit r/forhire post drafted for extra early traction

---

## After all sessions — daily routine

When a new order arrives:
1. Desktop notification fires on second PC
2. Open Claude desktop on second PC
3. Say: "New order arrived — read CLAUDE.md and process the next task in /tasks"
4. Claude estimates complexity, builds, tests, moves to /output
5. You review /output
6. Approve → n8n handles delivery message and review follow-up

That is the entire system. You touch it at step 3 and step 5 only.

---

## If something breaks

Bridge not responding:
→ python C:\fiverr-pipeline\bridge\bridge.py (restart it)

ngrok URL changed:
→ restart ngrok, copy new URL, update Node 9 in n8n

n8n workflow not triggering:
→ open localhost:5678, check workflow is Active, check Gmail credentials

Claude not finding tasks:
→ check C:\fiverr-pipeline\tasks\ manually, confirm .md files are there

Groq down:
→ n8n automatically falls back to Gemini — nothing to do

---

## Git workflow going forward

After any change to pipeline files:
```
git add .
git commit -m "describe what changed"
git push
```

On second PC to get latest:
```
git pull
```

Never commit: .env, tasks/, output/, logs/
