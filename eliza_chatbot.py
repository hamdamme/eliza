# -*- coding: utf-8 -*-

__author__ = "Hamdam Aynazarov"

import re
import random
from typing import Optional, List
from collections import deque

DEFAULT_NAME = "Friend"
RECENT_REPLY_WINDOW = 4

# Basic emotion words
NEG_WORDS = {"bad", "sad", "upset", "depressed", "angry", "hurt"}
POS_WORDS = {"good", "great", "fine", "okay", "happy", "better"}

# Common short responses
ACK_NEG = {"no", "nope", "nothing"}
CONFUSED_UTTS = {"i don't know", "idk", "not sure"}

# Family/relations
KINSHIP_WORDS = [
    "mother", "mom", "father", "dad", "brother", "sister",
    "wife", "husband", "son", "daughter", "friend"
]

_last_responses = deque(maxlen=RECENT_REPLY_WINDOW)


# ========== Small Helpers ==========

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _anti_repeat_pick(options: List[str]) -> str:
    """Avoid repeating same line too often."""
    random.shuffle(options)
    for o in options:
        if o not in _last_responses:
            _last_responses.append(o)
            return o
    c = random.choice(options)
    _last_responses.append(c)
    return c


# ========== Extractors ==========

def find_name(response: str) -> str:
    m = re.search(r"(?:i[' ]?m|i am|my name is)\s+([a-z]+)", response, re.I)
    if m:
        return m.group(1).capitalize()
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


# ========== Memory Class ==========

class Memory:
    def __init__(self):
        self.name = None


# ========== Main Response Logic ==========

def process(response: str, user_name: str, mem: Memory) -> str:
    text = _normalize(response)

    # Exit conditions
    if text in {"bye", "exit", "quit"}:
        return f"Goodbye, {mem.name}. Take care." if mem.name else "Goodbye."

    # Ask for name at the start if not set
    if not mem.name:
        nm = find_name(response)
        if nm:
            mem.name = nm
            return f"Nice to meet you, {nm}. How are you feeling today?"
        else:
            return "I’m Eliza. What is your name?"

    # From here, name is known
    name = mem.name

    # Simple family recognition
    relation = find_relationship(response)
    if relation:
        return f"Your {relation} seems important, {name}. How is your {relation}?"

    # Feelings
    feeling = find_feeling(response)
    if feeling == "negative":
        return f"I see you are not feeling well, {name}. Would you like to explain?"
    elif feeling == "positive":
        return f"I'm glad to hear that, {name}. What made you feel that way?"

    # Confusion responses
    if text in CONFUSED_UTTS:
        return f"It’s alright, {name}. You can take your time."

    # Acknowledgements
    if text in ACK_NEG:
        return f"Alright, {name}. I am here if you wish to continue."

    # Short "what"
    if text == "what":
        return f"Do you want to ask me something, {name}?"

    # Default calm responses
    simple_responses = [
        f"I see, {name}. Can you tell me more?",
        f"Alright, {name}. Go on.",
        f"Okay, {name}. What else?",
    ]
    return _anti_repeat_pick(simple_responses)


# ========== CLI Mode ==========

def main():
    print("Eliza: Hello, I’m Eliza. What’s your name?")
    mem = Memory()
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEliza: Goodbye.")
            break

        if not user_input:
            print("Eliza: Take your time.")
            continue

        resp = process(user_input, mem.name if mem.name else DEFAULT_NAME, mem)
        print(f"Eliza: {resp}")
        if _normalize(user_input) in {"bye", "exit", "quit"}:
            break


if __name__ == "__main__":
    main()