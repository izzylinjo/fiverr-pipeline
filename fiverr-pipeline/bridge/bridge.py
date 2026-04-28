from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
import os, re, logging

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

app = Flask(__name__)

# PIPELINE_ROOT in .env overrides; default is the repo root (works on any machine after git clone)
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.environ.get("PIPELINE_ROOT", _repo_root)
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
{os.path.join(BASE_DIR, 'output', project_name)}

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
    port = int(os.environ.get("BRIDGE_PORT", 8000))
    print(f"Bridge running on http://0.0.0.0:{port}")
    print(f"Tasks folder: {TASKS_DIR}")
    app.run(host='0.0.0.0', port=port, debug=False)
