# -*- coding: utf-8 -*-
"""Eliza-like Chatbot in Python"""
__author__ = "Hamdam Aynazarov"

import re
import random

def find_name(response):
    match = re.match(r'(i\'m|i am|my name is)? ?([a-z]+)', response, re.I)
    name = ""
    if match:
        name = match.group(2)
    return name.capitalize()

def find_feeling(response):
    feelings = {
        'sad': ["sad", "saddened", "depressed", "unhappy", "miserable"],
        'happy': ["happy", "joyful", "joy", "glad", "pleased", "satisfied"],
        'good': ["good", "fine", "well", "okay", "alright", "decent", "nice", "pleasing"],
        'bad': ["bad", "poor", "unpleasant", "undesirable", "awful", "terrible"]
    }
    for key, words in feelings.items():
        for word in words:
            if re.search(r"\b" + word + r"\b", response, re.I):
                return key
    return None

def find_relationship(response):
    relationships = [
        "mother", "mom", "mama", "father", "dad", "daddy", "brother", "sister", 
        "friend", "grandmother", "grandma", "grandfather", "grandpa", "uncle", 
        "aunt", "cousin", "nephew", "niece", "husband", "wife", "partner", 
        "boyfriend", "girlfriend", "son", "daughter", "sweetheart"]
    
    for relation in relationships:
        if re.search(r"\b" + relation + r"\b", response, re.I):
            return relation
    return None

def pick_standard_answer():
    responses = [
        "Tell me more about that.", "Can you elaborate on that?", "Anything else you'd like to share?",
        "How does that make you feel?", "That's interesting. Please continue.", "What happened next?",
        "Why do you think that is?", "How do you deal with that?", "What does this mean to you?",
        "Can you explain why that is important?", "What led you to that conclusion?", "Is there more to this?",
        "How did that make you feel?", "What else can you tell me about this?", "That sounds significant. Why?",
        "What's your take on that?", "Does this relate to anything else?", "What's your next step?"
    ]
    index = random.randint(0, len(responses)-1)
    return responses[index]

def find_verb_ending_in_ed(response):
    verbs = re.findall(r"\b(\w+?)ed\b", response, re.I)
    return verbs

def process(response, user_name):
    relationship = find_relationship(response)
    feeling = find_feeling(response)
    verbs = find_verb_ending_in_ed(response)

    if response.strip() == "bye":
        return f"Bye, it was great to chat with you!"

    relationships_regex = r"\b(" + "|".join([
        "mother", "mom", "mama", "father", "dad", "daddy", "brother", "sister", 
        "friend", "grandmother", "grandma", "grandfather", "grandpa", "uncle", 
        "aunt", "cousin", "nephew", "niece", "husband", "wife", "partner", 
        "boyfriend", "girlfriend", "son", "daughter", "sweetheart"]) + r")\b"

    if re.search(relationships_regex, response, re.I) or "is" in response or "are" in response:
        if relationship:
            if feeling in ["sad", "bad"]:
                return f"I'm sorry to hear that your {relationship.capitalize()} is feeling {feeling}. Can you tell me more about why?"
            elif feeling in ["happy", "good"]:
                return f"It's great to hear that your {relationship.capitalize()} is feeling {feeling}. What made your {relationship.capitalize()} feel this way?"
            else:
                return f"How is your {relationship.capitalize()} doing?"
        else:    
            return "Can you tell me more about that?"

    if feeling:
        if feeling in ['sad', 'bad']:
            return f"I'm sorry to hear that you're feeling {feeling}, {user_name}. Can you tell me more about why?"
        else:
            return f"It's great to hear that you're feeling {feeling}, {user_name}! What made you feel this way?"

    if verbs:
        action = " and ".join(verbs)
        if "end" in verbs:
            return "Why did it end?"
        elif "start" in verbs:
            return "When did it start?"
        else:
            return f"That's interesting. Can you elaborate on '{action}'?"

    return pick_standard_answer()

# Chatbot initial greetings 
print("Eliza: Hello, I'm Eliza chatbot. I'm here to chat with you. What's your name?")
name_input = input("User: ").strip()
user_name = find_name(name_input)
if len(user_name) == 0:
    user_name = "Sweetheart"

print(f"Eliza: Hello {user_name}, I was waiting for you, let's chat, how are you feeling?")

while True:
    user_input = input(f"{user_name}: ")
    response = process(user_input, user_name)
    print(f"Eliza: {response}")
    if user_input.strip() == "bye":
        break
