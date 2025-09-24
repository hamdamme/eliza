# app.py — Flask web app for Eliza
from flask import Flask, request, jsonify, render_template_string
from eliza_chatbot import process, find_name  # reuse your existing functions

app = Flask(__name__)

PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Eliza Chatbot</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    .chat { max-width: 720px; margin: 0 auto; }
    .log { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; height: 360px; overflow-y: auto; background:#fafafa; }
    .msg { margin: .5rem 0; }
    .me  { text-align: right; }
    .eliza { text-align: left; }
    .row { display: flex; gap: .5rem; margin-top: .75rem; }
    input[type=text] { flex: 1; padding: .6rem .8rem; border:1px solid #ccc; border-radius: 8px; }
    button { padding: .6rem 1rem; border: 0; border-radius: 8px; cursor: pointer; }
  </style>
</head>
<body>
  <div class="chat">
    <h1>Eliza Chatbot </h1>
    <div id="log" class="log"></div>
    <div class="row">
      <input id="msg" type="text" placeholder="Type a message... (say 'bye' to end)" autofocus />
      <button id="send">Send</button>
    </div>
  </div>

  <script>
    const log = document.getElementById('log');
    const input = document.getElementById('msg');
    const sendBtn = document.getElementById('send');
    let userName = "Sweetheart";

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
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: text, user_name: userName })
      });
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
    user_name = str(data.get("user_name") or "Sweetheart")
    # update name if user introduces themselves
    maybe = find_name(message)
    if maybe:
        user_name = maybe
    reply = process(message, user_name)
    return jsonify({"reply": reply, "user_name": user_name})

if __name__ == "__main__":
    # Render will run via a start command later; this is for local testing
    app.run(host="0.0.0.0", port=8000, debug=True)