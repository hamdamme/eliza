# -*- coding: utf-8 -*-

__author__ = "Hamdam Aynazarov"

import re
import random
import datetime
from typing import Optional, List, Dict
from collections import deque

# =========================
# Config (simple toggles)
# =========================
ENABLE_LOG = False          # write transcript to 'eliza_transcript.txt'
LOG_PATH = "eliza_transcript.txt"
DEFAULT_NAME = "Friend"     # fallback name (no endearments)
RECENT_REPLY_WINDOW = 4     # anti-repetition memory size

# =========================
# Lexicons & helpers
# =========================
NEG_WORDS = {
    "bad", "sad", "angry", "upset", "anxious", "depressed", "terrible", "awful",
    "worse", "worst", "tired", "stressed", "stress", "pain", "hurt", "nothing",
    "no", "nope", "nah", "confused"
}
POS_WORDS = {
    "good", "great", "awesome", "amazing", "fine", "okay", "ok", "happy", "glad",
    "better", "nice", "relieved", "improved"
}
ACK_NEG = {"no", "nope", "nah", "not really", "nothing", "none"}
ACK_AFFIRM = {"yes", "yep", "yeah", "sure", "ok", "okay", "fine", "alright"}
SHORT_Q = {"what", "why", "how", "?"}
JUST_YOU = {"you", "your", "yourself"}
GREETING_WORDS = {"hi", "hello", "hey", "hola", "yo", "good morning", "good afternoon", "good evening"}

CONFUSED_UTTS = {
    "i don't know", "idk", "dont know", "i am not sure", "i'm not sure", "not sure", "dunno"
}

TIME_WORDS = {
    "yesterday", "today", "last night", "tonight", "this morning", "this afternoon", "this evening"
}

COMMON_CORRECTIONS = {  # tiny typo map
    "twon": "town",
    "teh": "the",
    "recieve": "receive",
    "becuase": "because",
}

GENERIC_POOL = [
    "I’m listening. Say more about that.",
    "That matters. What else should I know?",
    "I hear you. What’s the core issue here?",
    "Tell me more about how this affects you.",
    "What would a ‘better’ version of this look like?",
    "What happened next?",
    "Why do you think that is?",
    "How do you deal with that?",
    "What does this mean to you?",
    "Is there more to this?",
]

KINSHIP_WORDS = [
    "mother", "mom", "mama", "father", "dad", "daddy", "brother", "sister",
    "friend", "grandmother", "grandma", "grandfather", "grandpa", "uncle",
    "aunt", "cousin", "nephew", "niece", "husband", "wife", "partner",
    "boyfriend", "girlfriend", "son", "daughter"
]

TOPIC_HINTS = {
    "work": {"job", "work", "boss", "office", "career", "project", "deadline"},
    "health": {"sick", "ill", "health", "doctor", "pain", "hurt", "injury"},
    "study": {"school", "class", "study", "exam", "university", "college", "homework"},
    "relationships": {"friend", "partner", "wife", "husband", "girlfriend", "boyfriend"},
}

# small reflection map
REFLECT_MAP = {
    r"\bi am\b": "you are",
    r"\bi'm\b": "you're",
    r"\bim\b": "you're",
    r"\bmy\b": "your",
    r"\bme\b": "you",
    r"\bi\b": "you",
    r"\byour\b": "my",
    r"\byou\b": "I",
}

_last_responses = deque(maxlen=RECENT_REPLY_WINDOW)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _apply_corrections(text: str) -> str:
    """Very small typo fixer using a safe replacement table."""
    def repl(m):
        w = m.group(0)
        lw = w.lower()
        if lw in COMMON_CORRECTIONS:
            fixed = COMMON_CORRECTIONS[lw]
            # preserve capitalization if word was capitalized
            return fixed.capitalize() if w[0].isupper() else fixed
        return w
    return re.sub(r"[A-Za-z]+", repl, text)


def _anti_repeat_pick(candidates: List[str]) -> str:
    random.shuffle(candidates)
    for c in candidates:
        if c not in _last_responses:
            _last_responses.append(c)
            return c
    choice = random.choice(candidates)
    _last_responses.append(choice)
    return choice


def _sentiment_hint(text: str) -> int:
    toks = re.findall(r"[a-z']+", text.lower())
    return sum(1 for t in toks if t in POS_WORDS) - sum(1 for t in toks if t in NEG_WORDS)


def _reflect(text: str) -> str:
    out = " " + text.strip() + " "
    for pat, rep in REFLECT_MAP.items():
        out = re.sub(pat, rep, out, flags=re.I)
    return out.strip()


def _log(line: str):
    if not ENABLE_LOG:
        return
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")
    except Exception:
        pass


# =========================
# Extractors
# =========================
def find_name(response: str) -> str:
    m = re.search(r"(?:i[' ]?m|i am|my name is)\s+([a-z]+(?:\s+[a-z]+)*)", response, re.I)
    if m:
        return m.group(1).strip().split()[0].capitalize()
    toks = re.findall(r"[A-Za-z][A-Za-z\-']{1,30}", response.strip())
    if len(toks) == 1:
        token = toks[0].lower()
        if token not in SHORT_Q and token not in ACK_NEG and token not in JUST_YOU and token not in GREETING_WORDS:
            return toks[0].capitalize()
    return ""


def find_feeling(response: str) -> Optional[str]:
    feelings = {
        "sad": ["sad", "saddened", "depressed", "unhappy", "miserable", "upset"],
        "happy": ["happy", "joyful", "joy", "glad", "pleased", "satisfied"],
        "good": ["good", "fine", "well", "okay", "ok", "alright", "decent", "nice", "better"],
        "bad": ["bad", "poor", "unpleasant", "undesirable", "awful", "terrible", "worse", "worst"],
    }
    for key, words in feelings.items():
        for word in words:
            if re.search(rf"\b{word}\b", response, re.I):
                return key
    return None


def find_relationship(response: str) -> Optional[str]:
    for relation in KINSHIP_WORDS:
        if re.search(rf"\b{relation}\b", response, re.I):
            return relation
    return None


def find_verb_ending_in_ed(response: str) -> List[str]:
    return re.findall(r"\b([a-z]{3,}ed)\b", response, re.I)


def detect_greeting(response: str) -> bool:
    r = _normalize(response)
    return any(r.startswith(g) or r == g for g in GREETING_WORDS)


# =========================
# Memory (simple, in-run)
# =========================
class Memory:
    def __init__(self):
        self.facts: List[str] = []
        self.name: Optional[str] = None
        self.kinship: set = set()
        self.concerns: set = set()  # work / health / study / relationships
        self.mood: Optional[str] = None  # 'pos' | 'neg' | None
        self.term_counts: Dict[str, int] = {}  # count mentions, e.g. "brother" -> 2
        self.last_relation: Optional[str] = None

    def bump(self, term: str):
        term = term.lower()
        self.term_counts[term] = self.term_counts.get(term, 0) + 1

    def remember_fact(self, fact: str):
        fact = fact.strip()
        if fact and fact not in self.facts:
            self.facts.append(fact)

    def summarize(self) -> str:
        if not self.facts:
            return "I haven't stored any facts yet."
        return " ; ".join(self.facts[:8])


def extract_topics(mem: Memory, text: str):
    for k in KINSHIP_WORDS:
        if re.search(rf"\b{k}\b", text, re.I):
            mem.kinship.add(k)
            mem.last_relation = k
            mem.bump(k)
    t = text.lower()
    for tag, vocab in TOPIC_HINTS.items():
        if any(w in t for w in vocab):
            mem.concerns.add(tag)


# =========================
# Intents (simple)
# =========================
def route_intent(user_raw: str, mem: Memory):
    s = user_raw.strip()
    n = _normalize(user_raw)

    # Direct questions about identity
    if re.search(r"\bwho\s+are\s+you\b", n):
        return True, "I’m Eliza—a simple conversation program here to listen and ask helpful questions. How can I help?"

    if n in {"help", "?", "commands"}:
        return True, (
            "Commands: help, time, joke, recall, remember <fact>, reset, quit/exit\n"
            "Otherwise, just talk to me."
        )
    if n in {"quit", "exit", "bye", "goodbye"}:
        return True, "Thanks for talking. Take care."
    if n == "reset":
        mem.__init__()
        return True, "Reset complete. Tell me your name?"
    if n == "time" or n == "what time is it?":
        now = datetime.datetime.now().strftime("%A, %b %d %Y, %I:%M %p")
        return True, f"It’s {now}."
    if n == "joke":
        return True, random.choice([
            "Why did the developer go broke? They used up all their cache.",
            "I told my computer I needed a break; it said: ‘No problem—I’ll go to sleep.’",
        ])
    m = re.match(r"^(remember|save)\s+(.+)$", s, flags=re.I)
    if m:
        fact = m.group(2).strip()
        mem.remember_fact(fact)
        return True, f"Got it. I’ll remember: {fact}"
    if n in {"recall", "memory", "what do you remember"}:
        return True, mem.summarize()

    return False, None


# =========================
# Response engine
# =========================
def generate_candidates(user_raw: str, mem: Memory) -> List[str]:
    # Apply tiny typo corrections so routing works better
    user_raw_fixed = _apply_corrections(user_raw)
    user = _normalize(user_raw_fixed)
    cands: List[str] = []

    # Hard-priority clarifiers for short utterances
    if user in {"what", "?"}:
        return [f"When you say “{user_raw.strip()}”, what do you mean?"]

    if user in CONFUSED_UTTS:
        return [
            "That’s okay not to know. What small piece feels clearest right now?",
            "We can find it together. What’s one detail you’re sure about?",
        ]

    # Greeting
    if detect_greeting(user_raw_fixed):
        name = mem.name or ""
        return [
            f"Hello{name and f' {name}'}! How are you feeling today?",
            f"Hi{name and f' {name}'}—what’s on your mind?",
            f"Hey{name and f' {name}'}! What would you like to talk about?",
        ]

    # Negative acknowledgements & “nothing”
    if user in ACK_NEG or user == "nothing":
        cands += [
            "That’s okay. What makes you say that?",
            "Thanks for being direct. What’s behind that?",
            "Understood. What feels most difficult about it?",
            "Even ‘nothing’ can carry weight. What does that ‘nothing’ mean for you?",
        ]

    # Affirm
    if user in ACK_AFFIRM:
        cands += [
            "Got it. Tell me a bit more.",
            "Okay. What part stands out most?",
            "Alright. What’s the key detail here?",
        ]

    # Time words (“yesterday”, etc.)
    if any(t in user for t in TIME_WORDS):
        cands += [
            "What happened then?",
            "What changed since then?",
            "How did that time affect you?",
        ]

    # “you” focus
    if user in JUST_YOU or (user.startswith("you") and len(user.split()) <= 3):
        cands += [
            "Let’s center on you for a moment—what do *you* want here?",
            "What would be most helpful for you right now?",
            "What do you need, in this moment?",
        ]

    # Relationship prompts
    relation = find_relationship(user_raw_fixed)
    feeling = find_feeling(user_raw_fixed)
    verbs = find_verb_ending_in_ed(user_raw_fixed)

    if relation:
        mem.kinship.add(relation)
        mem.last_relation = relation
        mem.bump(relation)

        # If the message is just the relation word, respond directly
        if len(user.split()) == 1:
            cands += [f"How is your {relation} doing?"]
        if mem.term_counts.get(relation, 0) >= 2:
            cands += [f"You’ve mentioned your {relation} a few times. What’s happening with them?"]

        if feeling in ["sad", "bad"]:
            cands += [f"I'm sorry to hear your {relation} is feeling {feeling}. What happened?"]
        elif feeling in ["happy", "good"]:
            cands += [f"Glad to hear your {relation} is {feeling}. What led to that?"]
        else:
            cands += [f"How is your {relation} doing these days?"]

    # Feelings
    if feeling:
        if feeling in {"sad", "bad"}:
            cands += [
                "I’m sorry it’s rough. What’s the hardest part right now?",
                "That sounds heavy. When did you first notice it?",
                "Thanks for sharing that. What small step could ease it?",
            ]
        else:
            cands += [
                "That’s nice to hear. What helped make it better?",
                "Great—what went well specifically?",
                "What would help you keep that momentum?",
            ]

    # Verb-based probes
    if verbs:
        action = " and ".join(verbs)
        if "ended" in verbs:
            cands += ["Why did it end?"]
        elif "started" in verbs:
            cands += ["When did it start?"]
        else:
            cands += [f"That's interesting. Can you elaborate on “{action}”?"]

    # Sentiment nudge
    s = _sentiment_hint(user_raw_fixed)
    if s < 0:
        mem.mood = "neg"
        cands += [
            "I’m sorry it’s rough. What’s the hardest part right now?",
            "That sounds heavy. What small step could ease it?",
        ]
    elif s > 0:
        mem.mood = "pos"
        cands += [
            "That’s nice to hear. What helped make it better?",
            "Awesome—what went well specifically?",
        ]

    # Topic extraction + light “fact” capture
    extract_topics(mem, user_raw_fixed)
    m_fact = re.search(r"\b(i am|i'm|i feel|i have|i want|my)\b(.+)", user_raw_fixed, re.I)
    if m_fact:
        fact = user_raw_fixed.strip()
        if len(fact.split()) >= 3:
            mem.remember_fact(fact)

    # “in town” follow-up leveraging last relation if we have it
    if re.search(r"\bin\s+town\b", user_raw_fixed, re.I):
        if mem.last_relation:
            cands += [f"Is your {mem.last_relation} in town? What brings them here?"]
        else:
            cands += ["Who is in town, and what brings them here?"]

    # Reflective fallback + generic
    short = " ".join(user_raw_fixed.split()[:14])
    if short:
        cands += [f"When you say “{_reflect(short)}”, what do you hope will change?"]
    cands += GENERIC_POOL

    return cands


def select_response(candidates: List[str]) -> str:
    # prefer more informative items a bit (longer strings), avoid repeats
    scored = []
    for c in candidates:
        s = min(len(c) // 40, 2)  # tiny length bonus
        if c in _last_responses:
            s -= 3                 # repetition penalty
        # prioritize directed questions over generic fillers slightly
        if "?" in c:
            s += 1
        scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [c for _, c in scored[:6]] or candidates
    return _anti_repeat_pick(top)


# =========================
# Public API
# =========================
def process(response: str, user_name: str, mem: Memory) -> str:
    """Generate a chatbot response based on user input."""
    # Apply corrections early so detectors work better
    response = _apply_corrections(response)
    rnorm = _normalize(response)

    # route intents first
    routed, msg = route_intent(response, mem)
    if routed:
        return msg

    # High-priority short clarifier (avoid generic picking this away)
    if rnorm in {"what", "?"}:
        return f"When you say “{response.strip()}”, what do you mean?"

    # name detection (first turns)
    if not mem.name:
        nm = find_name(response)
        if nm:
            mem.name = nm
            return random.choice([
                f"Nice to meet you, {nm}. How are you feeling today?",
                f"Welcome, {nm}! What’s on your mind?",
                f"Great to meet you, {nm}. What would you like to talk about first?",
            ])
        # If the user writes only 1–3 vague words (and not a greeting), ask name
        if len(response.split()) <= 3 and not detect_greeting(response):
            return random.choice([
                "I’m Eliza. What’s your name?",
                "Hi, I’m Eliza—may I know your name?",
            ])

    # main candidate generation
    candidates = generate_candidates(response, mem)
    return select_response(candidates)


# =========================
# CLI
# =========================
def main():
    print("Eliza: Hello, I’m Eliza. I’m here to chat with you. What’s your name?")
    mem = Memory()

    try:
        name_input = input("User: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nEliza: Goodbye, take care!")
        return

    nm = find_name(name_input)
    mem.name = nm if nm else DEFAULT_NAME
    print(f"Eliza: Hello {mem.name}, nice to meet you. How are you feeling?")

    while True:
        try:
            user_input = input(f"{mem.name}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEliza: Goodbye, take care!")
            break

        if not user_input:
            print("Eliza: Take your time. What feels important to start with?")
            continue

        resp = process(user_input, mem.name, mem)
        print(f"Eliza: {resp}")

        # Hard exit words are also handled in route_intent, but keep this safety:
        n = _normalize(user_input)
        if n in {"quit", "exit", "bye", "goodbye"}:
            break

        # simple log
        if ENABLE_LOG:
            _log(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {mem.name}: {user_input}")
            _log(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] Eliza: {resp}")

    print("Eliza: Session ended.")


# Entrypoint
if __name__ == "__main__":
    main()