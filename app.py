# app.py — Flask web app for Eliza (Render-ready, greets by name on first detection)

import os
import inspect
from flask import Flask, request, jsonify, render_template_string

# Your ELIZA module (this must be in eliza_chatbot.py)
from eliza_chatbot import process, find_name, Memory  # uses your 3-arg process()

DEFAULT_NAME = "Friend"
app = Flask(__name__)
mem = Memory()

# Detect arity just in case (supports older 2-arg process too)
try:
    _argcount = len(inspect.signature(process).parameters)
except Exception:
    _argcount = process.__code__.co_argcount

# NOTE: plain triple-quoted string (NOT an f-string) so JS/CSS braces are safe.
PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Eliza Chatbot</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 2rem; }
    .chat { max-width: 720px; margin: 0 auto; }
    .log { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; height: 360px; overflow-y: auto; background:#fafafa; }
    .msg { margin: .5rem 0; }
    .me  { text-align: right; }
    .eliza { text-align: left; }
    .row { display: flex; gap: .5rem; margin-top: .75rem; }
    input[type=text] { flex: 1; padding: .6rem .8rem; border:1px solid #ccc; border-radius: 8px; }
    button { padding: .6rem 1rem; border: 0; border-radius: 8px; cursor: pointer; background:#4f46e5; color:#fff; }
    h1 { margin-top:0; }
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
    let userName = "Friend";

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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, user_name: userName })
      });

      if (!res.ok) {
        addMessage('Sorry, something went wrong (' + res.status + ').', 'eliza');
        return;
      }

      const data = await res.json();
      userName = data.user_name || userName;
      addMessage(data.reply, 'eliza');
    }

    // greeting
    addMessage("Hello, I'm Eliza. What's your name?", 'eliza');

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', (e)=>{ if(e.key === 'Enter') send(); });
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

    # Current known name (if any)
    current_name = getattr(mem, "name", None)

    # Detect a name from this message
    detected = find_name(message)

    # First-time name detection → greet immediately and store it
    if detected and not current_name:
        mem.name = detected
        return jsonify({
            "reply": f"Nice to meet you, {detected}. How are you feeling today?",
            "user_name": detected
        })

    # Use known or detected or default
    user_name = current_name or detected or DEFAULT_NAME
    mem.name = user_name  # keep memory consistent

    # Call ELIZA (3-arg if available, else 2-arg)
    if _argcount >= 3:
        reply_text = process(message, user_name, mem)
    else:
        reply_text = process(message, user_name)

    return jsonify({"reply": reply_text, "user_name": user_name})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)