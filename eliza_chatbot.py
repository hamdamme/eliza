# -*- coding: utf-8 -*-
"""Eliza-like Chatbot in Python (CLI version)"""

__author__ = "Hamdam Aynazarov"

import re
import random
from typing import Optional, List


def find_name(response: str) -> str:
    """Extract a name if the user introduces themselves."""
    match = re.search(r"(?:i[' ]?m|i am|my name is)\s+([a-z]+(?:\s+[a-z]+)*)", response, re.I)
    if match:
        return match.group(1).strip().split()[0].capitalize()
    return ""


def find_feeling(response: str) -> Optional[str]:
    """Detect common feelings from user response."""
    feelings = {
        "sad": ["sad", "saddened", "depressed", "unhappy", "miserable"],
        "happy": ["happy", "joyful", "joy", "glad", "pleased", "satisfied"],
        "good": ["good", "fine", "well", "okay", "alright", "decent", "nice", "pleasing"],
        "bad": ["bad", "poor", "unpleasant", "undesirable", "awful", "terrible"],
    }
    for key, words in feelings.items():
        for word in words:
            if re.search(rf"\b{word}\b", response, re.I):
                return key
    return None


def find_relationship(response: str) -> Optional[str]:
    """Detect family or relationship words."""
    relationships = [
        "mother", "mom", "mama", "father", "dad", "daddy", "brother", "sister",
        "friend", "grandmother", "grandma", "grandfather", "grandpa", "uncle",
        "aunt", "cousin", "nephew", "niece", "husband", "wife", "partner",
        "boyfriend", "girlfriend", "son", "daughter", "sweetheart"
    ]
    for relation in relationships:
        if re.search(rf"\b{relation}\b", response, re.I):
            return relation
    return None


def pick_standard_answer() -> str:
    """Pick a generic but natural-sounding response."""
    responses = [
        "Tell me more about that.", "Can you elaborate on that?", "Anything else you'd like to share?",
        "How does that make you feel?", "That's interesting. Please continue.", "What happened next?",
        "Why do you think that is?", "How do you deal with that?", "What does this mean to you?",
        "Can you explain why that is important?", "What led you to that conclusion?", "Is there more to this?",
        "How did that make you feel?", "What else can you tell me about this?", "That sounds significant. Why?",
        "What's your take on that?", "Does this relate to anything else?", "What's your next step?"
    ]
    return random.choice(responses)


def find_verb_ending_in_ed(response: str) -> List[str]:
    """Extract verbs ending in 'ed' (ignores short words like 'red')."""
    return re.findall(r"\b([a-z]{3,}ed)\b", response, re.I)


def process(response: str, user_name: str) -> str:
    """Generate a chatbot response based on user input."""
    response_clean = response.strip().lower()

    if response_clean in {"bye", "exit", "quit"}:
        return "Bye, it was great to chat with you!"

    relationship = find_relationship(response)
    feeling = find_feeling(response)
    verbs = find_verb_ending_in_ed(response)

    if relationship:
        if feeling in ["sad", "bad"]:
            return f"I'm sorry to hear that your {relationship} is feeling {feeling}. Can you tell me more about why?"
        elif feeling in ["happy", "good"]:
            return f"It's great to hear that your {relationship} is feeling {feeling}. What made them feel this way?"
        else:
            return f"How is your {relationship} doing?"

    if feeling:
        if feeling in {"sad", "bad"}:
            return f"I'm sorry to hear that you're feeling {feeling}, {user_name}. Can you tell me more about why?"
        else:
            return f"It's great to hear that you're feeling {feeling}, {user_name}! What made you feel this way?"

    if verbs:
        action = " and ".join(verbs)
        if "ended" in verbs:
            return "Why did it end?"
        elif "started" in verbs:
            return "When did it start?"
        return f"That's interesting. Can you elaborate on '{action}'?"

    return pick_standard_answer()


def main():
    """Main function to start the chatbot in CLI."""
    print("Eliza: Hello, I'm Eliza chatbot. I'm here to chat with you. What's your name?")
    name_input = input("User: ").strip()
    user_name = find_name(name_input) or "Sweetheart"

    print(f"Eliza: Hello {user_name}, I was waiting for you. Let's chat. How are you feeling?")

    while True:
        try:
            user_input = input(f"{user_name}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEliza: Goodbye, take care!")
            break

        response = process(user_input, user_name)
        print(f"Eliza: {response}")
        if user_input.strip().lower() in {"bye", "exit", "quit"}:
            break


if __name__ == "__main__":
    main()