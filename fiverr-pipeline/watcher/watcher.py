import time, os
from dotenv import load_dotenv
from plyer import notification

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# PIPELINE_ROOT in .env overrides; default is the repo root (works on any machine after git clone)
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.environ.get("PIPELINE_ROOT", _repo_root)
TASKS_DIR = os.path.join(BASE_DIR, "tasks")
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
