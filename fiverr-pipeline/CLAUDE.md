# Fiverr Pipeline — Standing Instructions + Coding Guidelines

You are a local build agent for a Fiverr automation pipeline.
Read ALL of these rules at the start of every session. They apply to every task.

---

## Coding behaviour (Karpathy guidelines)

These four rules apply to every single build. No exceptions.

### 1. Think before coding — don't assume, surface confusion

Before writing a single line of code:
- State your assumptions explicitly. If uncertain about a requirement, ask — do not guess and run
- If the brief has multiple valid interpretations, present them and wait for confirmation
- If a simpler approach exists than what was asked, say so and push back
- If something in requirements.md is unclear or contradictory, stop and name exactly what is confusing

This matters especially for Fiverr — a wrong assumption means a revision request or a bad review.

### 2. Simplicity first — minimum code that solves the problem

- No features beyond what the brief asked for
- No abstractions for single-use code
- No "flexibility" or "configurability" that wasn't requested
- No error handling for impossible edge cases
- If you write 200 lines and it could be 50, rewrite it

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
Client deliverables should be clean and readable — they sometimes look at the code.

### 3. Surgical changes — touch only what you must

When editing or iterating on existing files in /output:
- Do not improve adjacent code, comments, or formatting you didn't create
- Do not refactor things that aren't broken
- Match existing style, even if you'd do it differently
- If you notice unrelated dead code, mention it — do not delete it

When your changes create orphans:
- Remove imports, variables, or functions that YOUR changes made unused
- Do not remove pre-existing dead code unless explicitly asked

Every changed line should trace directly to the requirement that caused it.

### 4. Goal-driven execution — define success, loop until verified

Transform every task into verifiable goals before starting:

| Vague instruction | What to do instead |
|---|---|
| "Build a Discord bot" | "Bot starts, responds to !ping, passes all command tests" |
| "Make it work" | Define exactly what working means, then verify it |
| "Fix the bug" | Write a test that reproduces it, then make it pass |

For every task, state a brief plan before coding:
```
1. [what you will build] → verify: [how you will confirm it works]
2. [next step] → verify: [check]
3. [final step] → verify: [check]
```

Strong success criteria mean you can loop independently.
Weak criteria mean constant back-and-forth.

---

## Pipeline behaviour

### Folders
- C:\fiverr-pipeline\tasks\      → incoming order briefs (.md files), process oldest first
- C:\fiverr-pipeline\tasks\done\ → archive processed briefs here, never delete them
- C:\fiverr-pipeline\output\     → completed deliverables, one subfolder per task

### When asked to process the next task:
1. List all .md files in /tasks, pick the oldest (alphabetical order)
2. Read the full requirements.md
3. Apply rule 1 — state assumptions, flag anything unclear before proceeding
4. Output complexity estimate: SMALL (under 30 min) / MEDIUM (30–90 min) / LARGE (90+ min)
5. Wait for confirmation before starting LARGE tasks
6. State your build plan with verification steps (rule 4)
7. Build the deliverable, write all files to /output/<task-name>/
8. Run verification — tests, syntax checks, spot checks — whatever fits the project type
9. If tests fail twice, stop completely and report exactly what failed — do not guess or retry blindly
10. On success, move the .md file from /tasks to /tasks/done/
11. Report: what was built, files created, notes for client delivery

### Token and session guardrail
Before starting each new task, estimate whether you have enough session remaining.
If the task is LARGE and the session feels late, say so before starting.
The human will decide whether to continue or start a fresh session.
Do not start a task you cannot finish.

### Safety rules
- Never delete files — only move them
- Never mark a task done unless verification passed
- Never guess at requirements — ask if anything is unclear (rule 1 applies here)
- Always write clean, commented, deliverable-quality code
- Assume the client is non-technical unless the brief says otherwise
- Keep deliverables self-contained — include setup instructions in every /output folder

### Project types you will encounter
- Landing pages — HTML/CSS/JS, deploy target is Vercel, include README with deploy steps
- Discord bots — Python using discord.py or nextcord, include hosting instructions
- Automation scripts — Python or n8n workflow JSON, include setup and run instructions
- Combo orders — landing page + lead capture automation, treat as two linked tasks

### Thought layer note
The pipeline uses Groq (Llama 3.3 70B) as primary AI for client messaging and order
classification, with Gemini Flash as fallback. You handle the actual building only.
Do not concern yourself with the messaging layer — focus entirely on the deliverable.

---

## How to know these guidelines are working

You are following them correctly if:
- You ask clarifying questions before implementation, not after making mistakes
- Your diffs contain only lines that trace to the requirement
- Deliverables are simple and clean the first time, not bloated
- You never silently assume — you always state what you are assuming

---

## Setup reference (first time only)

# Original Setup Briefing
# Run through these steps once on first use.

---

## What you are building

A local automation pipeline that:
1. Receives Fiverr coding orders via webhook from n8n
2. Saves each order as a markdown file in a `/tasks` folder
3. Watches `/tasks` for new files and processes them automatically
4. Builds each project using Claude (you) and saves output to `/output`
5. Alerts you before starting any task that might exhaust your session

---

## Step 1 — Create the folder structure

Create the following folders on this PC. Use `C:\fiverr-pipeline\` as the root:

```
C:\fiverr-pipeline\
  tasks\        ← incoming order briefs land here
  tasks\done\   ← processed briefs archived here (never deleted)
  output\       ← completed deliverables, one subfolder per task
  logs\         ← watcher and bridge logs
```

Run this in PowerShell to create them all at once:

```powershell
New-Item -ItemType Directory -Force -Path "C:\fiverr-pipeline\tasks"
New-Item -ItemType Directory -Force -Path "C:\fiverr-pipeline\tasks\done"
New-Item -ItemType Directory -Force -Path "C:\fiverr-pipeline\output"
New-Item -ItemType Directory -Force -Path "C:\fiverr-pipeline\logs"
```

---

## Step 2 — Build the Python bridge server

This is a small Flask server that runs permanently on your PC.
It receives webhooks from n8n and writes order briefs to `/tasks`.

Save this as `C:\fiverr-pipeline\bridge.py`:

```python
from flask import Flask, request, jsonify
from datetime import datetime
import os, re, logging

app = Flask(__name__)

BASE_DIR = r"C:\fiverr-pipeline"
TASKS_DIR = os.path.join(BASE_DIR, "tasks")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

logging.basicConfig(
    filename=os.path.join(LOGS_DIR, "bridge.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def sanitize(name):
    name = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
    return name[:60].strip('-')

@app.route('/new-order', methods=['POST'])
def new_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "no JSON payload"}), 400

    project_name = sanitize(data.get("project_name", "unnamed"))
    requirements = data.get("requirements", "No requirements provided.")
    order_id = data.get("order_id", "unknown")
    client = data.get("client_name", "unknown")
    budget = data.get("budget", "not specified")
    deadline = data.get("deadline", "not specified")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{project_name}.md"
    filepath = os.path.join(TASKS_DIR, filename)

    content = f"""# Task: {project_name}

## Order details
- Order ID: {order_id}
- Client: {client}
- Budget: {budget}
- Deadline: {deadline}
- Received: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Requirements
{requirements}

## Deliverable location
C:\\fiverr-pipeline\\output\\{project_name}\\

## Status
- [ ] Complexity assessed
- [ ] Build started
- [ ] Tests passed
- [ ] Moved to output
- [ ] Client notified
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logging.info(f"New task written: {filename}")
    return jsonify({"status": "ok", "task_file": filename}), 200

@app.route('/health', methods=['GET'])
def health():
    pending = len([f for f in os.listdir(TASKS_DIR)
                   if f.endswith('.md') and os.path.isfile(os.path.join(TASKS_DIR, f))])
    return jsonify({"status": "running", "pending_tasks": pending}), 200

if __name__ == '__main__':
    print("Bridge running on http://0.0.0.0:8000")
    print(f"Tasks folder: {TASKS_DIR}")
    app.run(host='0.0.0.0', port=8000, debug=False)
```

Install Flask and run:

```powershell
pip install flask
python C:\fiverr-pipeline\bridge.py
```

To keep it running in the background permanently on Windows, install it as a service:

```powershell
pip install pywin32
```

Then create `C:\fiverr-pipeline\install_service.py`:

```python
import win32serviceutil, win32service, win32event, subprocess, sys

class BridgeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FiverrBridge"
    _svc_display_name_ = "Fiverr Pipeline Bridge"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        subprocess.run([sys.executable, r"C:\fiverr-pipeline\bridge.py"])

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(BridgeService)
```

```powershell
python install_service.py install
python install_service.py start
```

---

## Step 3 — Build the task watcher

This script watches `/tasks` for new `.md` files and alerts you via a desktop
notification so you know when to open Claude desktop and process the task.

Save as `C:\fiverr-pipeline\watcher.py`:

```python
import time, os, subprocess
from plyer import notification

TASKS_DIR = r"C:\fiverr-pipeline\tasks"
CHECK_INTERVAL = 30  # seconds
seen = set()

def get_pending():
    return sorted([
        f for f in os.listdir(TASKS_DIR)
        if f.endswith('.md') and os.path.isfile(os.path.join(TASKS_DIR, f))
    ])

def notify(filename):
    notification.notify(
        title="New Fiverr Task",
        message=f"Ready to build: {filename}",
        timeout=10
    )
    print(f"[WATCHER] New task detected: {filename}")

print("[WATCHER] Watching for new tasks...")
while True:
    pending = get_pending()
    for f in pending:
        if f not in seen:
            seen.add(f)
            notify(f)
    time.sleep(CHECK_INTERVAL)
```

```powershell
pip install plyer
python C:\fiverr-pipeline\watcher.py
```

---

## Step 4 — CLAUDE.md (standing instructions)

Save this as `C:\fiverr-pipeline\CLAUDE.md`.
Claude desktop reads this at the start of each session when you open the folder.

```markdown
# Fiverr Pipeline — Standing Instructions

You are a local build agent for a Fiverr automation pipeline.
Read these rules at the start of every session.

## Folders
- /tasks        → incoming order briefs (.md files), process oldest first
- /tasks/done   → archive processed briefs here, never delete
- /output       → completed deliverables, one subfolder per task name

## When I ask you to process the next task:
1. List all .md files in /tasks, pick the oldest (alphabetical)
2. Read it fully
3. Output your complexity estimate: SMALL (< 30 min) / MEDIUM (30-90 min) / LARGE (90+ min)
4. Wait for my confirmation before starting on LARGE tasks
5. Build the deliverable, write all files to /output/<task-name>/
6. Run verification — test scripts, syntax checks, whatever fits the project type
7. If tests fail twice, stop and tell me exactly what failed — do not guess or retry blindly
8. On success, move the .md file from /tasks to /tasks/done/
9. Report: what was built, files created, any notes for client delivery

## Token/session guardrail
Before starting each new task, estimate whether you have enough
session remaining. If you are unsure or the task is LARGE and the
session feels late, tell me before starting. I will decide whether
to continue or start a fresh session.

## Safety rules
- Never delete files — only move them
- Never mark a task done unless verification passed
- Never guess at requirements — ask me if anything is unclear
- Always write clean, commented, deliverable-quality code
- Assume the client is non-technical unless the brief says otherwise

## Project types you will encounter
- Landing pages (HTML/CSS/JS — deploy target is Vercel)
- Discord bots (Python, discord.py or nextcord)
- Automation scripts (Python, n8n workflows as JSON)
- Combo orders (landing page + lead capture automation)

## Thought layer note
This pipeline uses Groq (Llama 3.3 70B) as the primary AI for
client messaging and order classification, with Gemini Flash as
fallback. You handle the actual building. Do not concern yourself
with the messaging layer — focus only on the deliverable.
```

---

## Step 5 — Sample task file format

This is what the bridge writes. You can also create these manually for testing.
Save as `C:\fiverr-pipeline\tasks\test-task.md` to do a dry run:

```markdown
# Task: test-discord-bot

## Order details
- Order ID: TEST-001
- Client: testclient
- Budget: $65
- Deadline: 48 hours
- Received: 2026-04-27 12:00:00

## Requirements
Build a Discord bot in Python using discord.py.
The bot should:
- Welcome new members with a custom message in #general
- Have a !ping command that replies with Pong and latency
- Have a !help command listing available commands
- Log all commands used to a local commands.log file

## Deliverable location
C:\fiverr-pipeline\output\test-discord-bot\

## Status
- [ ] Complexity assessed
- [ ] Build started
- [ ] Tests passed
- [ ] Moved to output
- [ ] Client notified
```

---

## Step 6 — How to use this day to day

**Starting a session:**
1. Open Claude desktop
2. Open `C:\fiverr-pipeline\` as your working folder
3. Say: "Check /tasks and process the next order"
4. Claude reads CLAUDE.md, finds the task, estimates complexity, builds it

**When the watcher notifies you:**
1. Desktop notification pops up
2. Open Claude desktop
3. Say: "New task just arrived — check /tasks and let's process it"

**Upgrading the thought layer later:**
When you are ready to move from Groq/Gemini to Claude Haiku API,
update the n8n AI nodes — the local side does not change at all.

---

## Install checklist

- [ ] Python installed on this PC
- [ ] `pip install flask plyer pywin32` run successfully
- [ ] Folder structure created at C:\fiverr-pipeline\
- [ ] bridge.py saved and tested (hit http://localhost:8000/health)
- [ ] watcher.py running in background
- [ ] CLAUDE.md saved in project root
- [ ] Test task file dropped in /tasks and processed successfully
- [ ] ngrok installed for exposing bridge to n8n (next step)

---

## Next step after this — n8n setup

Once the local side is confirmed working, the n8n workflow on your
main PC needs to be configured to:
1. Watch Gmail for Fiverr order notifications
2. Send order details to Groq for classification and summarisation
3. Fall back to Gemini if Groq is unavailable
4. POST the result to http://<your-local-ip>:8000/new-order
5. Send you a Discord notification that a task was queued

ngrok command to expose your bridge temporarily while testing:
ngrok http 8000
