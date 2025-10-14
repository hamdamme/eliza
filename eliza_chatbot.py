# -*- coding: utf-8 -*-

__author__ = "Hamdam Aynazarov"

import re
import random
from typing import Optional, List
from collections import deque

RECENT_REPLY_WINDOW = 4
_last_responses = deque(maxlen=RECENT_REPLY_WINDOW)

# Keywords
NEG_WORDS = {"bad", "sad", "upset", "depressed", "angry", "lonely", "tired", "hurt"}
POS_WORDS = {"good", "great", "fine", "happy", "better", "okay"}
CONFUSED_UTTS = {"i don't know", "idk", "not sure"}
ACK_NEG = {"no", "nope", "nothing"}

# Greetings & words we should NOT treat as names
GREETING_WORDS = {"hi", "hello", "hey", "hola", "yo", "greetings"}
NOT_NAME_WORDS = ACK_NEG | CONFUSED_UTTS | NEG_WORDS | POS_WORDS | GREETING_WORDS | {
    "what", "why", "how", "who", "when", "where", "thanks", "thank", "please", "ok", "okay",
    "bye", "exit", "quit"
}

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
    # prefer it to look like a name (capitalized or all upper)
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
    return t in GREETING_WORDS


# ----------------- Memory -----------------

class Memory:
    def __init__(self):
        self.name = None


# ----------------- Main logic -----------------

def process(response: str, user_name: str, mem: Memory) -> str:
    text = _normalize(response)

    # Exit handling
    if text in {"bye", "exit", "quit"}:
        if mem.name:
            return f"Goodbye, {mem.name}. I hope you find peace."
        return "Goodbye. I wish you well."

    # Name handling
    if not mem.name:
        # If user just greets, do not treat it as a name
        if is_greeting(response):
            return (
                "I am Eliza. I would like to address you properly. "
                "What is your name?"
            )
        nm = find_name(response)
        if nm:
            mem.name = nm
            return (
                f"Nice to meet you, {nm}. I hope you are doing alright. "
                f"How are you feeling today?"
            )
        # If user mentions 'name' but we couldn't detect it, guide them simply
        if "name" in text:
            return (
                "I want to use your correct name. "
                "Please tell me like this: 'My name is Sam.' "
                "What is your name?"
            )
        return (
            "I am Eliza. I would like to address you properly. "
            "What is your name?"
        )

    # From here, name is known
    name = mem.name

    # Family handling
    relation = find_relationship(response)
    if relation:
        return (
            f"Your {relation} seems important to you, {name}. "
            f"I understand that family matters can affect us deeply. "
            f"Would you like to tell me more about your {relation}? "
            f"I am here to listen."
        )

    # Feelings
    feeling = find_feeling(response)
    if feeling == "negative":
        return (
            f"I see you are not feeling well, {name}. "
            f"It is alright to have difficult moments. "
            f"If you wish, you can share what made you feel this way. "
            f"I am here to listen calmly."
        )
    elif feeling == "positive":
        return (
            f"I am glad to hear this, {name}. "
            f"It is good to notice positive moments. "
            f"What do you think helped you feel this way? "
            f"Would you like to talk about it?"
        )

    # Confusion
    if text in CONFUSED_UTTS:
        return (
            f"It is okay not to know, {name}. "
            f"Some thoughts are not easy to explain. "
            f"Take your time. "
            f"I will listen whenever you are ready."
        )

    # Negative acknowledgment
    if text in ACK_NEG:
        return (
            f"Alright, {name}. "
            f"You do not need to force yourself to speak. "
            f"If you wish to continue later, I will still be here. "
            f"I respect your pace."
        )

    # Simple "what"
    if text == "what":
        return (
            f"Do you wish to ask something in particular, {name}? "
            f"I am here to respond with care. "
            f"Please feel free to continue. "
            f"I am listening."
        )

    # Default calm responses (3–4 simple sentences)
    responses = [
        (
            f"I understand, {name}. "
            f"Sometimes it helps to express things slowly. "
            f"If you want, you may continue at your own pace. "
            f"I am here with patience."
        ),
        (
            f"I hear you, {name}. "
            f"Life can feel heavy at times. "
            f"You may share as much as you feel comfortable. "
            f"I am here to listen."
        ),
        (
            f"Thank you for sharing this, {name}. "
            f"It may not always be easy to speak. "
            f"If there is more you wish to say, I am here. "
            f"Take your time."
        )
    ]
    return _anti_repeat_pick(responses)


# ----------------- CLI Mode (Optional) -----------------

def main():
    print("Eliza: Hello, I am Eliza. What is your name?")
    mem = Memory()
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEliza: Goodbye. I wish you well.")
            break

        if not user_input:
            print("Eliza: Take your time.")
            continue

        resp = process(user_input, mem.name if mem.name else "", mem)
        print(f"Eliza: {resp}")
        if _normalize(user_input) in {"bye", "exit", "quit"}:
            break


if __name__ == "__main__":
    main()