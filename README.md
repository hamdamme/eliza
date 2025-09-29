# Eliza-like Chatbot

This is a simple **Eliza-like chatbot** written in Python.  
It uses pattern matching to recognize user input about feelings, relationships, and actions, and replies with context-aware responses.

## Features
- Detects user’s name from input.  
- Identifies common feelings (happy, sad, good, bad).  
- Recognizes relationships (mother, father, friend, etc.).  
- Responds to verbs ending in *-ed* (e.g., "started", "ended").  
- Provides varied responses for natural conversation flow.  

## How to Run
1. **Clone the repository**  
   bash
   git clone https://github.com/hamdamme/eliza.git
   cd eliza

2. Run the chatbot
   bash
   python3 eliza_chatbot.py


Example:

Eliza: Hello, I'm Eliza chatbot. I'm here to chat with you. What's your name?
User: My name is Sam
Eliza: Hello Sam, I was waiting for you, let's chat, how are you feeling?
Sam: I feel sad today
Eliza: I'm sorry to hear that you're feeling sad, Sam. Can you tell me more about why? ...
