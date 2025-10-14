# -*- coding: utf-8 -*-

__author__ = "Hamdam Aynazarov"

import re
import random
from typing import Optional, List
from collections import deque

# --- small anti-repetition buffer for general replies (after name is known) ---
RECENT_REPLY_WINDOW = 4
_last_responses = deque(maxlen=RECENT_REPLY_WINDOW)

# Basic keywords
NEG_WORDS = {"bad", "sad", "upset", "depressed", "angry", "lonely", "tired", "hurt"}
POS_WORDS = {"good", "great", "fine", "happy", "better", "okay"}
CONFUSED_UTTS = {"i don't know", "idk", "not sure"}
ACK_NEG = {"no", "nope", "nothing"}

# Greetings & words we should NOT treat as names
GREETING_WORDS = {
    "hi", "hello", "hey", "hola", "yo", "greetings",
    "good morning", "good afternoon", "good evening"
}
NOT_NAME_WORDS = (
    ACK_NEG | CONFUSED_UTTS | NEG_WORDS | POS_WORDS | set(GREETING_WORDS) |
    {"what", "why", "how", "who", "when", "where", "thanks", "thank", "please",
     "ok", "okay", "bye", "exit", "quit"}
)

# Family/relations
KINSHIP_WORDS = [
    "mother", "mom", "father", "dad", "brother", "sister",
    "wife", "husband", "son", "daughter", "friend"
]


# ----------------- Helpers -----------------

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _anti_repeat_pick(options: List[str]) -> str:
    random.shuffle(options)
    for o in options:
        if o not in _last_responses:
            _last_responses.append(o)
            return o
    c = random.choice(options)
    _last_responses.append(c)
    return c


def _is_valid_name(token: str) -> bool:
    t = token.strip().strip(",.:;!?'\"").strip()
    if not t:
        return False
    tl = t.lower()
    if tl in NOT_NAME_WORDS:
        return False
    # allow letters, hyphen, apostrophe in names like "Jean-Paul", "O'Neil"
    if not re.fullmatch(r"[A-Za-z][A-Za-z\-']{0,30}", t):
        return False
    # accept if starts with a letter (no need to force uppercase—users may type lowercase)
    return t[0].isalpha()


# ----------------- Extractors -----------------

def find_name(response: str) -> str:
    """Extract a likely name; ignore greetings like 'Hi'."""
    r = response.strip()

    # Patterned introductions
    m = re.search(
        r"(?:my\s+name\s+is|i\s*am|i[' ]?m|call\s+me|name\s*:\s*)([A-Za-z][A-Za-z\-']{1,30})",
        r,
        re.I,
    )
    if m:
        cand = m.group(1).strip()
        if _is_valid_name(cand):
            return cand[0].upper() + cand[1:]
        return ""

    # Single-token fallback (only if not a greeting/stop word)
    toks = re.findall(r"[A-Za-z][A-Za-z\-']{1,30}", r)
    if len(toks) == 1:
        tok = toks[0]
        if _is_valid_name(tok) and tok.lower() not in GREETING_WORDS:
            return tok[0].upper() + tok[1:]

    return ""


def find_relationship(response: str) -> Optional[str]:
    for relation in KINSHIP_WORDS:
        if re.search(rf"\b{relation}\b", response, re.I):
            return relation
    return None


def find_feeling(response: str) -> Optional[str]:
    for w in NEG_WORDS:
        if re.search(rf"\b{w}\b", response, re.I):
            return "negative"
    for w in POS_WORDS:
        if re.search(rf"\b{w}\b", response, re.I):
            return "positive"
    return None


def is_greeting(text: str) -> bool:
    t = _normalize(text)
    return any(t == g or t.startswith(g) for g in GREETING_WORDS)


# ----------------- Memory -----------------

class Memory:
    def __init__(self):
        self.name: Optional[str] = None


# ----------------- Main logic -----------------

def _ask_for_name_again(user_text: str) -> str:
    """Polite loop: acknowledge, then ask for name again, explain why."""
    # If user greeted, acknowledge the greeting simply
    if is_greeting(user_text):
        return (
            "Hello. I want to use your name so my sentences are clear and polite. "
            "Please tell me your name. You can say: “My name is Sam.”"
        )
    # If they mentioned 'name' but not given
    if "name" in _normalize(user_text):
        return (
            "I understand. Please tell me your exact name so I can address you well. "
            "For example: “My name is Sam.” What is your name?"
        )
    # Any other text before giving a name
    return (
        "Thank you. I would like to address you by your name to make my words clear. "
        "Please tell me your name. You can say: “My name is Sam.”"
    )


def process(response: str, user_name: str, mem: Memory) -> str:
    text = _normalize(response)

    # Exit handling
    if text in {"bye", "exit", "quit"}:
        if mem.name:
            return f"Goodbye, {mem.name}. I wish you well."
        return "Goodbye. I wish you well."

    # === Name handling loop: keep asking until a name is given ===
    if mem.name is None:
        nm = find_name(response)
        if nm:
            mem.name = nm
            return (
                f"Nice to meet you, {nm}. "
                f"How are you feeling today? "
                f"You can share a little or a lot. "
                f"I will read carefully."
            )
        # politely ask again and explain why name helps
        return _ask_for_name_again(response)

    # From here, name is known
    name = mem.name

    # Family handling
    relation = find_relationship(response)
    if relation:
        return (
            f"Your {relation} seems important to you, {name}. "
            f"I understand that family can affect us strongly. "
            f"Would you like to share what is happening with your {relation}? "
            f"I will listen with care."
        )

    # Feelings
    feeling = find_feeling(response)
    if feeling == "negative":
        return (
            f"I see you are not feeling well, {name}. "
            f"It is alright to have hard moments. "
            f"If you wish, you can say what led to this feeling. "
            f"I am here to listen."
        )
    elif feeling == "positive":
        return (
            f"I am glad to hear that, {name}. "
            f"It is good to notice positive moments. "
            f"What do you think helped you feel this way? "
            f"You may share more if you want."
        )

    # Confusion
    if text in CONFUSED_UTTS:
        return (
            f"It is okay not to know, {name}. "
            f"Some ideas are hard to explain. "
            f"You can take your time and speak in small steps. "
            f"I am listening."
        )

    # Negative acknowledgment
    if text in ACK_NEG:
        return (
            f"Alright, {name}. "
            f"You do not need to push yourself. "
            f"If you want to continue later, I will be here. "
            f"I respect your pace."
        )

    # Simple "what"
    if text == "what":
        return (
            f"Do you wish to ask something in particular, {name}? "
            f"I will try to answer in simple and clear words. "
            f"Please continue when you are ready. "
            f"I am here."
        )

    # Default calm responses (3–4 simple sentences)
    responses = [
        (
            f"I understand, {name}. "
            f"You may share more if you wish. "
            f"Short or long is fine. "
            f"I will read with care."
        ),
        (
            f"Thank you for telling me this, {name}. "
            f"It is not always easy to talk. "
            f"If there is more you want to add, please do. "
            f"I am here to listen."
        ),
        (
            f"I hear you, {name}. "
            f"We can go step by step. "
            f"Say whatever feels safe to say. "
            f"I am patient."
        ),
    ]
    return _anti_repeat_pick(responses)


# ----------------- CLI Mode (Optional) -----------------

def main():
    print("Eliza: Hello. I am Eliza. What is your name?")
    mem = Memory()
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEliza: Goodbye. I wish you well.")
            break

        if not user_input:
            print("Eliza: Please take your time. When you are ready, tell me your name.")
            continue

        resp = process(user_input, mem.name if mem.name else "", mem)
        print(f"Eliza: {resp}")
        if _normalize(user_input) in {"bye", "exit", "quit"}:
            break


if __name__ == "__main__":
    main()