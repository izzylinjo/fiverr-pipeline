# n8n Workflow Setup — Fiverr Automation Pipeline
# Groq (primary) + Gemini (fallback) thought layer
# Paste this into Claude desktop on your main PC to get full setup help

---

## What this workflow does

1. Watches Gmail for Fiverr order notification emails
2. Extracts the order brief using Groq (Llama 3.3 70B)
3. Falls back to Gemini Flash if Groq is unavailable
4. Classifies the order — coding or non-coding
5. Sends an automatic acknowledgement to the client via Gmail
6. POSTs the order to your local Python bridge (which writes /tasks/*.md)
7. Pings you on Discord with a clean summary
8. Schedules a review request follow-up 3 days after delivery

---

## Step 1 — Install n8n on your main PC

Run these three commands in PowerShell or terminal:

```powershell
# Install Node.js first if not installed — download from nodejs.org
# Then install n8n globally
npm install -g n8n

# Start n8n
n8n start
```

n8n will open at http://localhost:5678 in your browser.
Default login: create an account on first launch, it stays local.

To keep n8n running in the background on Windows:

```powershell
npm install -g pm2
pm2 start n8n
pm2 save
pm2 startup
```

---

## Step 2 — API keys you need before building the workflow

Get these before opening n8n. Claude desktop will prompt you for each one
if you paste this document in and ask it to walk you through setup.

### Groq API key (primary thought layer — free)
1. Go to https://console.groq.com
2. Sign up / log in
3. Click API Keys → Create API Key
4. Copy and save it — you only see it once
- Model to use: llama-3.3-70b-versatile
- Free tier: 6000 requests/day, 30 requests/minute — more than enough

### Gemini API key (fallback — free)
1. Go to https://aistudio.google.com
2. Sign in with Google
3. Click Get API Key → Create API Key
4. Copy and save it
- Model to use: gemini-1.5-flash-latest
- Free tier: 1500 requests/day

### Gmail OAuth (for reading and sending emails)
n8n connects to Gmail via OAuth — no password needed.
You will do this inside n8n when you add the Gmail node:
1. Add Gmail node → Credentials → Create New
2. Click Connect → sign in with Google → allow access
3. n8n stores the token locally — it auto-refreshes

### Discord webhook URL (for pinging yourself)
1. Open Discord → go to the channel you want notifications in
2. Click the gear icon (Edit Channel) → Integrations → Webhooks
3. Click New Webhook → copy the webhook URL
4. Save it — looks like: https://discord.com/api/webhooks/xxxxx/xxxxx

### Your local bridge URL
While testing locally use ngrok to expose your bridge:
```powershell
# Install ngrok from https://ngrok.com (free account)
ngrok http 8000
```
ngrok gives you a public URL like https://abc123.ngrok.io
Use that as your webhook target in n8n while testing.
When you move n8n to a server later, use your local IP instead.

---

## Step 3 — Build the n8n workflow

Open n8n at http://localhost:5678
Click New Workflow → name it "Fiverr Pipeline"

Add these nodes in order:

---

### Node 1 — Gmail Trigger
Type: Gmail Trigger
- Event: Message Received
- Credentials: your Gmail OAuth (set up in Step 2)
- Filters:
  - From: (leave blank to catch all, or set to notification@fiverr.com)
  - Subject contains: "New Order" OR "order confirmation"
- Poll every: 1 minute

What this does: checks your Gmail every minute for new Fiverr order emails
and fires the workflow when one arrives.

---

### Node 2 — Extract email body
Type: Code (JavaScript)
- Connect from: Gmail Trigger

Paste this code:

```javascript
const email = $input.first().json;

// Get the plain text body — Fiverr emails are HTML
const body = email.text || email.snippet || email.subject || "";
const subject = email.subject || "";
const from = email.from || "";
const messageId = email.id || "";

return [{
  json: {
    raw_body: body,
    subject: subject,
    from: from,
    message_id: messageId,
    received_at: new Date().toISOString()
  }
}];
```

---

### Node 3 — Groq: classify and summarise
Type: HTTP Request
- Method: POST
- URL: https://api.groq.com/openai/v1/chat/completions
- Authentication: Header Auth
  - Name: Authorization
  - Value: Bearer YOUR_GROQ_API_KEY
- Body (JSON):

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "You are an assistant that processes Fiverr order notifications. Extract order details and classify the work type. Always respond in valid JSON only."
    },
    {
      "role": "user",
      "content": "Extract the following from this Fiverr order email and return ONLY valid JSON with these fields: project_name (short slug, no spaces), client_name, requirements (full description of what they want built), order_type (one of: landing_page / discord_bot / automation / combo / non_coding), estimated_complexity (small/medium/large), deadline_hours (number). Email: {{ $json.raw_body }}"
    }
  ],
  "temperature": 0.2,
  "max_tokens": 800
}
```

---

### Node 4 — Parse Groq response
Type: Code (JavaScript)
- Connect from: Groq node

```javascript
const response = $input.first().json;
const content = response.choices[0].message.content;

let parsed;
try {
  // Strip markdown code fences if present
  const clean = content.replace(/```json|```/g, '').trim();
  parsed = JSON.parse(clean);
} catch(e) {
  // If parsing fails, flag for fallback
  parsed = { parse_error: true, raw: content };
}

return [{ json: { ...parsed, groq_success: !parsed.parse_error } }];
```

---

### Node 5 — Groq success check (IF node)
Type: IF
- Condition: {{ $json.groq_success }} equals true

Two outputs:
- TRUE → continue to Node 7 (send acknowledgement)
- FALSE → go to Node 6 (Gemini fallback)

---

### Node 6 — Gemini fallback
Type: HTTP Request
- Method: POST
- URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=YOUR_GEMINI_API_KEY
- Body (JSON):

```json
{
  "contents": [{
    "parts": [{
      "text": "Extract the following from this Fiverr order email and return ONLY valid JSON with these fields: project_name (short slug no spaces), client_name, requirements (full description), order_type (one of: landing_page/discord_bot/automation/combo/non_coding), estimated_complexity (small/medium/large), deadline_hours (number). Email: {{ $('Extract email body').item.json.raw_body }}"
    }]
  }],
  "generationConfig": { "temperature": 0.2, "maxOutputTokens": 800 }
}
```

Add another Code node after this to parse Gemini's response:

```javascript
const response = $input.first().json;
const content = response.candidates[0].content.parts[0].text;
const clean = content.replace(/```json|```/g, '').trim();
const parsed = JSON.parse(clean);
return [{ json: { ...parsed, groq_success: false, used_fallback: true } }];
```

---

### Node 7 — Send acknowledgement email
Type: Gmail
- Operation: Send
- Connect from: both TRUE branch of IF node AND Gemini fallback parser
- To: {{ $json.client_email }} (if available) — otherwise skip for now
- Subject: Re: Your order — {{ $json.project_name }}
- Body:

```
Hi {{ $json.client_name }},

Thanks for your order! I've received your brief and I'm reviewing 
your requirements now.

I'll get started shortly and keep you updated on progress. 
Feel free to message me if you have any questions.

Looking forward to working with you!
```

Note: Fiverr handles client messaging through their platform.
This node fires only if the order came with a direct email.
For Fiverr-native messaging, you will handle replies manually
or via the Fiverr API (add later).

---

### Node 8 — Route by order type (IF node)
Type: IF
- Condition: {{ $json.order_type }} does not equal "non_coding"

- TRUE (coding order) → go to Node 9 (send to bridge)
- FALSE (non-coding) → go to Node 11 (Discord ping, no bridge needed)

---

### Node 9 — POST to your local bridge
Type: HTTP Request
- Method: POST
- URL: https://YOUR_NGROK_URL.ngrok.io/new-order
  (replace with your actual ngrok URL while testing)
- Body (JSON):

```json
{
  "project_name": "{{ $json.project_name }}",
  "requirements": "{{ $json.requirements }}",
  "client_name": "{{ $json.client_name }}",
  "order_type": "{{ $json.order_type }}",
  "estimated_complexity": "{{ $json.estimated_complexity }}",
  "deadline_hours": "{{ $json.deadline_hours }}"
}
```

---

### Node 10 — Discord notification (coding order)
Type: HTTP Request
- Method: POST
- URL: YOUR_DISCORD_WEBHOOK_URL
- Body (JSON):

```json
{
  "content": "**New coding order queued**\n**Project:** {{ $json.project_name }}\n**Type:** {{ $json.order_type }}\n**Complexity:** {{ $json.estimated_complexity }}\n**Deadline:** {{ $json.deadline_hours }} hours\n**Requirements:** {{ $json.requirements }}\n\nTask file written to /tasks — open Claude desktop to process."
}
```

---

### Node 11 — Discord notification (non-coding order)
Type: HTTP Request
- Method: POST
- URL: YOUR_DISCORD_WEBHOOK_URL
- Body (JSON):

```json
{
  "content": "**Non-coding order received — handle manually**\n**Client:** {{ $json.client_name }}\n**Details:** {{ $json.requirements }}"
}
```

---

### Node 12 — Schedule review follow-up (3 days)
Type: n8n Wait node
- Wait: 3 days
- Connect from: Node 10 (after coding order queued)

After wait, add another Discord notification:

```json
{
  "content": "**Review follow-up reminder**\nProject: {{ $json.project_name }}\nTime to send the client a review request if not already done."
}
```

(You send the actual Fiverr review request manually — Fiverr does not
allow automated messages through external tools on their platform.)

---

## Step 4 — Test the full pipeline

1. Confirm bridge is running: http://localhost:8000/health
2. Confirm ngrok is running and you have a public URL
3. In n8n, click Execute Workflow to run it manually
4. Send yourself a test email with subject "New Order" and fake order details
5. Watch the workflow execute node by node in n8n's visual editor
6. Check C:\fiverr-pipeline\tasks\ for the new .md file
7. Check Discord for the notification

If a node fails, click it in n8n — it shows you the exact error and the
data that was passed in. 90% of issues are wrong field names in the JSON.

---

## Step 5 — Activate the workflow

Once tested and working:
1. Click the toggle at the top right of the workflow — set to Active
2. n8n will now poll Gmail every minute automatically
3. Every new Fiverr order email triggers the full pipeline

---

## Upgrade path — switching to Claude Haiku later

When you are ready to replace Groq/Gemini with Claude Haiku API:
1. Replace Node 3 (Groq HTTP Request) with an Anthropic API call:
   - URL: https://api.anthropic.com/v1/messages
   - Headers: x-api-key: YOUR_HAIKU_API_KEY, anthropic-version: 2023-06-01
   - Model: claude-haiku-4-5
2. Remove Node 6 (Gemini fallback) — Haiku does not go down
3. Everything else stays identical

Cost at upgrade point: roughly $0.01-0.03 per order.
Upgrade when Fiverr income makes this trivially affordable.

---

## Keys and URLs checklist

Before activating make sure you have all of these configured in n8n:

- [ ] Groq API key — in Node 3 Authorization header
- [ ] Gemini API key — in Node 6 URL query parameter
- [ ] Gmail OAuth — connected in Node 1 and Node 7
- [ ] Discord webhook URL — in Node 10 and Node 11
- [ ] ngrok URL — in Node 9 (update this whenever ngrok restarts)
- [ ] Bridge health confirmed — http://localhost:8000/health returns OK
- [ ] Test order processed end to end before activating
