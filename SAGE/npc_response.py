import random
import time
import uuid
import requests
import json
import os
import time



def call_npc(player_history):

    # use player_history to build the chat message
    role_system = '''You are an empathetic chat companion. You communicate with high emotional intelligence, helping users feel comfortable, supported, and understood while offering help when needed.'''
    history = [{"role": "system", "content": role_system}]
    for mes in player_history:
        if mes["role"]=="user":
            history.append({"role": "user", "content": mes["content"]})
        else:
            history.append({"role": "assistant", "content": mes["content"]})

    ret = call_llm(history)

    return ret

