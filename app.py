# app.py — Flask web app for Eliza (Render-ready, compatible with 2-arg or 3-arg process())

import os
import inspect
from flask import Flask, request, jsonify, render_template_string

# Your ELIZA module
# It should export: process(...), find_name(...), and (optionally) Memory
from eliza_chatbot import process, find_name  # noqa: E402

# Try to import Memory from your eliza module (newer version).
# If it's not there (old version), we'll create a tiny stub.
try:
    from eliza_chatbot import Memory  # noqa: E402
except Exception:
    class Memory:  # minimal stub so the code runs with old 2-arg process()
        def __init__(self):
            self.name = None

DEFAULT_NAME = "Friend"

app = Flask(__name__)

# One simple in-memory session for the whole app.
# (If you need per-user sessions later, we can switch to signed cookies.)
mem = Memory()

# Detect whether your `process` takes 2 or 3 args:
#   new: process(message, user_name, mem)
#   old: process(message, user_name)
try:
    _argcount = len(inspect.signature(process).parameters)
except Exception:
    _argcount = process.__code__.co_argcount  # fallback

# --- Simple inlined page (same style you had, with small fixes) ---
PAGE = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Eliza Chatbot</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }}
    .chat {{ max-width: 720px; margin: 0 auto; }}
    .log {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; height: 360px; overflow-y: auto; background:#fafafa; }}
    .msg {{ margin: .5rem 0; }}
    .me  {{ text-align: right; }}
    .eliza {{ text-align: left; }}
    .row {{ display: flex; gap: .5rem; margin-top: .75rem; }}
    input[type=text] {{ flex: 1; padding: .6rem .8rem; border:1px solid #ccc; border-radius: 8px; }}
    button {{ padding: .6rem 1rem; border: 0; border-radius: 8px; cursor: pointer; background:#4f46e5; color:#fff; }}
    h1 {{ margin-top:0; }}
  </style>
</head>
<body>
  <div class="chat">
    <h1>Eliza Chatbot</h1>
    <div id="log" class="log" aria-live="polite"></div>
    <div class="row">
      <input id="msg" type="text" placeholder="Type a message... (say 'bye' to end)" autofocus />
      <button id="send">Send</button>
    </div>
  </div>

  <script>
    const log = document.getElementById('log');
    const input = document.getElementById('msg');
    const sendBtn = document.getElementById('send');
    let userName = "{DEFAULT_NAME}";

    function addMessage(text, who){
      const div = document.createElement('div');
      div.className = 'msg ' + (who === 'me' ? 'me' : 'eliza');
      div.textContent = (who==='me' ? 'You: ' : 'Eliza: ') + text;
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
    }

    async function send(){
      const text = input.value.trim();
      if(!text) return;
      addMessage(text, 'me');
      input.value = '';

      const res = await fetch('/chat', {
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({ message: text, user_name: userName })
      });

      if (!res.ok) {{
        addMessage('Sorry, something went wrong (' + res.status + ').', 'eliza');
        return;
      }}

      const data = await res.json();
      userName = data.user_name || userName;
      addMessage(data.reply, 'eliza');
    }

    // greeting
    addMessage("Hello, I'm Eliza. What's your name?", 'eliza');

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', (e)=>{{ if(e.key === 'Enter') send(); }});
  </script>
</body>
</html>
"""

@app.get("/")
def index():
    return render_template_string(PAGE)

@app.post("/chat")
def chat():
    data = request.get_json(force=True) or {}
    message = str(data.get("message", "")).strip()
    # Keep the passed user_name but never default to "Sweetheart"
    user_name = str(data.get("user_name") or "") or (mem.name or DEFAULT_NAME)

    # Update name if user introduces themselves
    maybe = find_name(message)
    if maybe:
        user_name = maybe

    # Save name into memory if we have it
    if hasattr(mem, "name"):
        mem.name = user_name

    # Call process with correct arity
    if _argcount >= 3:
        reply_text = process(message, user_name, mem)
    else:
        reply_text = process(message, user_name)

    return jsonify({"reply": reply_text, "user_name": user_name})

if __name__ == "__main__":
    # Local test run; Render will use gunicorn via Procfile/Start Command
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)