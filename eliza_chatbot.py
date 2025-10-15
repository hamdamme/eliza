# -*- coding: utf-8 -*-

__author__ = "Hamdam Aynazarov"

import re
import random
from typing import Optional, List
from collections import deque

NEG_WORDS = {
    "bad", "sad", "upset", "depressed", "angry", "lonely", "tired", "hurt",
    "miserable", "terrible", "awful"
}
POS_WORDS = {"good", "great", "fine", "happy", "better", "okay", "ok", "glad"}

GREETINGS = {
    "hi", "hello", "hey", "hola", "yo",
    "good morning", "good afternoon", "good evening"
}
STOP_WORDS = {
    "what", "why", "how", "who", "when", "where", "thanks", "thank", "please",
    "ok", "okay", "bye", "exit", "quit", "nothing", "no", "nope", "idk",
    "i don't know", "not sure"
}

KINSHIP = [
    "mother", "mom", "father", "dad", "brother", "sister",
    "wife", "husband", "son", "daughter", "friend", "grandmother",
    "grandfather", "aunt", "uncle", "cousin"
]

RECENT_REPLY_WINDOW = 4
_last_replies = deque(maxlen=RECENT_REPLY_WINDOW)


# ----------------------------- helpers --------------------------------

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _anti_repeat(options: List[str]) -> str:
    random.shuffle(options)
    for o in options:
        if o not in _last_replies:
            _last_replies.append(o)
            return o
    choice = random.choice(options)
    _last_replies.append(choice)
    return choice


def _is_greeting(text: str) -> bool:
    t = _normalize(text)
    return any(t == g or t.startswith(g) for g in GREETINGS)


def _is_name_like(token: str) -> bool:
    # allow letters, hyphen, apostrophe
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z\-']{0,30}", token))


# ---------------------------- extractors -------------------------------

def find_name(text: str) -> str:
    """Return first name if clearly given; else ''."""
    # explicit patterns
    m = re.search(
        r"(?:my\s+name\s+is|i\s*am|i[' ]?m|call\s+me|name\s*:\s*)([A-Za-z][A-Za-z\-']{1,30})",
        text,
        flags=re.I,
    )
    if m:
        cand = m.group(1).strip()
        return cand[0].upper() + cand[1:] if _is_name_like(cand) else ""

    # single-token fallback (but not greetings or stop words)
    toks = re.findall(r"[A-Za-z][A-Za-z\-']{1,30}", text)
    if len(toks) == 1:
        tok = toks[0]
        low = tok.lower()
        if _is_name_like(tok) and low not in GREETINGS and low not in STOP_WORDS:
            return tok[0].upper() + tok[1:]
    return ""


def find_feeling(text: str) -> Optional[str]:
    for w in NEG_WORDS:
        if re.search(rf"\b{w}\b", text, re.I):
            return "neg"
    for w in POS_WORDS:
        if re.search(rf"\b{w}\b", text, re.I):
            return "pos"
    return None


def find_relation(text: str) -> Optional[str]:
    for r in KINSHIP:
        if re.search(rf"\b{r}\b", text, re.I):
            return r
    return None


def find_ed_verbs(text: str) -> List[str]:
    # simple verbs ending with -ed
    return re.findall(r"\b([a-z]{3,}ed)\b", text, flags=re.I)


# ------------------------------- memory --------------------------------

class Memory:
    def __init__(self):
        self.name: Optional[str] = None
        self.last_relation: Optional[str] = None


# ---------------------------- name prompts -----------------------------

def ask_name_prompt(user_text: str) -> str:
    t = _normalize(user_text)

    if _is_greeting(user_text):
        return (
            "Hello. I want to use your real name so my sentences are clear and polite. "
            "Please tell me your name. You can say: “My name is Sam.”"
        )

    if "name" in t:
        return (
            "I want to address you correctly. Please tell me your exact name. "
            "You can say: “My name is Sam.” What is your name?"
        )

    return (
        "Thank you. I would like to address you by your real name, so my words are clear. "
        "Please tell me your name. You can say: “My name is Sam.”"
    )


# ----------------------------- main logic ------------------------------

def process(user_text: str, _user_name: str, mem: Memory) -> str:
    text = _normalize(user_text)

    # Exits
    if text in {"bye", "exit", "quit"}:
        return f"Goodbye, {mem.name}. I wish you well." if mem.name else "Goodbye. I wish you well."

    # 1) Ask for name until we have it
    if not mem.name:
        nm = find_name(user_text)
        if nm:
            mem.name = nm
            return (
                f"Nice to meet you, {nm}. "
                f"How are you feeling today? "
                f"You may share a little or a lot. "
                f"I will read with care."
            )
        return ask_name_prompt(user_text)

    # From here we have a name
    name = mem.name

    # 2) Family / relation focus
    rel = find_relation(user_text)
    if rel:
        mem.last_relation = rel
        return (
            f"Your {rel} seems important to you, {name}. "
            f"I understand that family can affect us strongly. "
            f"Would you like to share what is happening with your {rel}? "
            f"I will listen with care."
        )

    # Detect “in town” and tie to last relation if we have one
    if re.search(r"\bin\s+town\b", user_text, re.I):
        if mem.last_relation:
            return (
                f"Is your {mem.last_relation} in town, {name}? "
                f"What brings them here? "
                f"How do you feel about it? "
                f"You can share more if you wish."
            )
        else:
            return (
                f"Who is in town, {name}? "
                f"What brings them here? "
                f"How do you feel about it? "
                f"You can share more if you wish."
            )

    # 3) Feelings
    feeling = find_feeling(user_text)
    if feeling == "neg":
        return (
            f"I see you are not feeling well, {name}. "
            f"It is alright to have hard moments. "
            f"If you wish, you can say what led to this feeling. "
            f"I am here to listen."
        )
    if feeling == "pos":
        return (
            f"I am glad to hear that, {name}. "
            f"It is good to notice positive moments. "
            f"What do you think helped you feel this way? "
            f"You may share more if you want."
        )

    # 4) -ed verbs
    ed_verbs = [v.lower() for v in find_ed_verbs(user_text)]
    if ed_verbs:
        if "started" in ed_verbs:
            return (
                f"When did it start, {name}? "
                f"What was happening around that time? "
                f"How did it affect you? "
                f"You can tell me more if you wish."
            )
        if "ended" in ed_verbs:
            return (
                f"Do you know what led it to end, {name}? "
                f"How do you feel about it now? "
                f"What changed after it ended? "
                f"I am here to read more if you want to share."
            )
        joined = ", ".join(sorted(set(ed_verbs))[:3])
        return (
            f"You mentioned “{joined}”, {name}. "
            f"Would you like to explain what happened? "
            f"What was most important to you? "
            f"I will read carefully."
        )

    # 5) Short “what”
    if text == "what":
        return (
            f"Do you want to ask something specific, {name}? "
            f"I will try to answer in simple and clear words. "
            f"Please continue when you are ready. "
            f"I am here."
        )

    # 6) Acknowledgements and unclear cases
    if text in {"nothing", "no", "nope"}:
        return (
            f"Alright, {name}. "
            f"You do not need to push yourself. "
            f"If you wish to continue later, I will be here. "
            f"I respect your pace."
        )
    if text in {"i don't know", "idk", "not sure"}:
        return (
            f"It is okay not to know, {name}. "
            f"Some ideas are hard to explain. "
            f"You can take your time and speak in small steps. "
            f"I am listening."
        )

    # 7) Default — clear, simple, not short
    options = [
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
    return _anti_repeat(options)


def main():
    print("Eliza: Hello. I am Eliza. What is your name?")
    mem = Memory()
    while True:
        try:
            user = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEliza: Goodbye. I wish you well.")
            break

        if not user:
            print("Eliza: Please take your time. When you are ready, tell me your name.")
            continue

        reply = process(user, mem.name or "", mem)
        print(f"Eliza: {reply}")

        if _normalize(user) in {"bye", "exit", "quit"}:
            break


if __name__ == "__main__":
    main()