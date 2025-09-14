import random
import time
import uuid
import requests
import json
import os
from utils.llm_utils import get_llm


def create_llm(llm_type='openai', model_name='gpt-3.5-turbo', temperature=0.7, **kwargs):
    """
    Create and return a configured LLM instance.
    
    Args:
        llm_type: Type of LLM ('openai', 'azure', 'google', 'anthropic', etc.)
        model_name: Name of the model to use
        temperature: Temperature setting for the model
        **kwargs: Additional configuration parameters
    
    Returns:
        Configured LLM instance
    """
    llm_config = {
        'type': 'azure',
        'name': 'gpt-4.1',
        **kwargs
    }
    
    return get_llm(llm_config)



def call_npc(player_history, llm):
    """
    Generate NPC response using the provided LLM instance.
    
    Args:
        player_history: List of message dictionaries with 'role' and 'content' keys
        llm: Pre-configured LLM instance from get_llm()
    
    Returns:
        str: The generated response content
    """
    # use player_history to build the chat message
    role_system = '''You are an empathetic chat companion. You communicate with high emotional intelligence, helping users feel comfortable, supported, and understood while offering help when needed.'''
    history = [{"role": "system", "content": role_system}]
    for mes in player_history:
        if mes["role"]=="user":
            history.append({"role": "user", "content": mes["content"]})
        else:
            history.append({"role": "assistant", "content": mes["content"]})

    # Call the LLM with the message history
    response = llm.invoke(history)
    
    # Extract the content from the response
    ret = response.content

    return ret

