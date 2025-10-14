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
KINSHIP_WORDS = [
    "mother", "mom", "father", "dad", "brother", "sister",
    "wife", "husband", "son", "daughter", "friend"
]


# Helpers
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


# Extractors
def find_name(response: str) -> str:
    m = re.search(r"(?:i[' ]?m|i am|my name is)\s+([a-z]+)", response, re.I)
    if m:
        return m.group(1).capitalize()
    toks = re.findall(r"[A-Za-z][A-Za-z\-']{1,30}", response.strip())
    if len(toks) == 1 and toks[0].istitle():
        return toks[0]
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


# Memory
class Memory:
    def __init__(self):
        self.name = None


# Main logic
def process(response: str, user_name: str, mem: Memory) -> str:
    text = _normalize(response)

    # Exit handling
    if text in {"bye", "exit", "quit"}:
        if mem.name:
            return f"Goodbye, {mem.name}. I hope you find peace."
        return "Goodbye. I wish you well."

    # Name handling
    if not mem.name:
        nm = find_name(response)
        if nm:
            mem.name = nm
            return (
                f"Nice to meet you, {nm}. I hope you are doing alright. "
                f"How are you feeling today?"
            )
        return (
            "I am Eliza. I would like to address you properly. "
            "What is your name?"
        )

    # Name is known
    name = mem.name

    # Family handling
    relation = find_relationship(response)
    if relation:
        return (
            f"Your {relation} seems important to you, {name}. "
            f"I understand that family matters can affect us deeply. "
            f"Would you like to tell me more about your {relation}?"
        )

    # Feelings
    feeling = find_feeling(response)
    if feeling == "negative":
        return (
            f"I see you are feeling this way, {name}. "
            f"It is alright to have difficult moments. "
            f"If you wish, you can share what made you feel like this. "
            f"I am here to listen calmly."
        )
    elif feeling == "positive":
        return (
            f"I am glad to hear you feel that way, {name}. "
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

    # Default calm responses
    responses = [
        (
            f"I understand, {name}. "
            f"Sometimes it helps to express things slowly. "
            f"If you want, you may continue at your own pace. "
            f"I am here with patience."
        ),
        (
            f"I hear you, {name}. "
            f"Life can be complex at times. "
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


# CLI Mode (Optional)
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