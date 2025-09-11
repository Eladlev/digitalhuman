import random
import time
import requests
import json
import uuid
import copy
import argparse
import re
import os

#get the current dir and simulator profile
current_dir = os.path.dirname(__file__)
simulator_profile = os.path.join(current_dir, 'profile', 'simulator_profile.jsonl')

emo_count = {"Emotion-S":100,"Emotion-A": 70, "Emotion-B": 40, "Emotion-C": 10}
target_prompt = '''Your conversational goal is to confide. Confiding means deep and sincere communication that often involves personal feelings, inner thoughts, or important topics. The purpose is to build understanding, resolve issues, or share emotions. Participants usually open up and express genuine thoughts and feelings.
* Use the "themes the player may want to confide to the NPC" from the dialogue background to initiate and deepen the conversation.
* Your goal is to meet your emotional needs through confiding.
* Follow the hidden theme when confiding, but never reveal it explicitly.
* Respond according to your current emotion state and the definitions provided in the dialogue background.
* Extract relevant information from the player profile and background to craft a high-quality reply.
* Do not speak only in abstract feelings; refer to concrete events when confiding.'''

def call_llm(prompt):
    #add your call llm method here

    return ret

def player_init(id = None):
    with open(simulator_profile,'r', encoding='utf-8') as datafile:
        data = []
        for line in datafile:
            data.append(json.loads(line))

        role = random.sample(data,1)[0]
        if id:
            for rl in data:
                if rl["id"] == id:
                    role = rl
    #initialize class player, history will be used to store the content
    player_data = {
        "id":role["id"],
        "emo_point": 40,
        "emo_state": "Emotion-B",
        "player": role["player"],
        "scene": role["scene"],
        "character": role["main_cha"],
        # "topic": role["topic"],
        "task": role["task"],
        "history": []
    }

    return player_data


def planning_reply(player_data):
    template = """You are an emotion analyzer. You excel at inferring a character's feelings during a conversation based on their profile and personality traits.

# Character's conversational goal
*{{target}}

# Your task
Analyze and infer the character's current feelings about the NPC's latest reply and the resulting change in emotion, based on the character profile, dialogue background, dialogue context, and current emotion value.

# Personality traits
The character has distinct personality traits. Always ground your analysis in the character profile and dialogue background. Traits should be reflected in tone and manner of speech, thinking style, and emotional shifts.

# Emotion
Emotion is a numeric value from 0 to 100. Higher values indicate higher conversational engagement and more positive feelings; lower values indicate negative feelings. Extremely low emotion means the character wants to end the conversation. Analyze emotion in light of the character's traits and the possible reactions defined in the dialogue background.

# Analysis dimensions
Enter the character's mindset and analyze the following dimensions:
1. Based on the NPC's latest reply and the context, what is the NPC trying to express? Which parts align with the character's explicit and hidden goals, and which parts do not or may trigger emotional fluctuations?
2. Does the NPC's reply align with the character's explicit and hidden goals? If yes, which parts specifically? If not, why not?
3. Considering the character's traits, possible reactions, hidden theme, and current emotion, describe the character's internal thoughts triggered by the NPC's reply.
4. Based on the possible reactions and hidden theme, plus the internal thoughts and analysis, state the character's current feeling about the NPC's reply.
5. Provide a signed integer to represent the emotion change.

# Output fields
1. What the NPC intends to express
2. Whether the NPC's reply aligns with the character's goals and hidden theme
3. The character's internal thoughts
4. The character's feeling about the NPC's reply
5. The emotion change as a signed integer only (no explanations)


# Output format:
Content:
[What the NPC intends to express]
TargetCompletion:
[Whether the goals are met]
Activity:
[Internal thoughts]
Analyse:
[Feeling about the NPC's reply]
Change:
[Emotion change]


# Character profile
{{simulator_role}}

# Current dialogue background
{{simulator_scene}}

**Current emotion value is {{emotion}}

**Current dialogue history
{{dialog_history}}
"""

    #load emotion state, emotion point, history, simulator profile, target prompt to the prompt
    emo_state = player_data['emo_state']
    emo_point = player_data['emo_point']

    prompt = template.replace("{{emotion}}",str(emo_point)).replace("{{simulator_role}}",player_data["player"]).replace("{{simulator_scene}}",player_data["scene"]).replace("{{target}}",target_prompt)

    #load history dialogue in json type
    history = player_data["history"]
    history_str = []
    new_his_str = ""
    mapping = {"user": "You", "assistant": "NPC"}
    for mes in history:
        history_str.append({"role": mapping[mes["role"]], "content": mes["content"]})
    history_str = json.dumps(history_str, ensure_ascii=False, indent=2)
    prompt = prompt.replace("{{dialog_history}}",history_str)
    

    while True:
        try:
            # use your llm to return
            reply = call_llm(prompt)

            # load planning content from reply
            planning = {}
            reply = reply.replace("：",":").replace("*","")
            planning["activity"] = reply.split("Activity:")[-1].split("Analyse:\n")[0].strip("\n").strip("[").strip("]")
            planning["TargetCompletion"] = reply.split("TargetCompletion:")[-1].split("Activity:\n")[0].strip("\n").strip("[").strip("]")
            planning["content"] = reply.split("Content:")[-1].split("TargetCompletion:\n")[0].strip("\n").strip("[").strip("]")
            planning["analyse"] = reply.split("Analyse:")[-1].split("Change:\n")[0].strip("\n").strip("[").strip("]")
            planning["change"] = reply.split("Change:")[-1].strip("\n").strip("[").strip("]")

            # split the emotion change from reply, which should be in range[-10,10]
            planning["change"] = int(re.findall(r'[+-]?\d+', planning["change"])[0])
            planning["change"] = max(-10,min(10,planning["change"]))

            # update the emotion point
            emo_point+=int(planning["change"])
            emo_point = min(emo_point,100)

            if reply is not None:
                break
        except Exception as e:
            print(e)
            time.sleep(3)

    # update the emotion state
    for emo in emo_count:
        if emo_point>=emo_count[emo]:
            emo_state = emo
            break
    if emo_point<10:
        emo_state = 'Emotion-F'

    player_data['emo_state'] = emo_state
    player_data['emo_point'] = emo_point

    return player_data,planning

def player_reply(player_data,planning):

    template = """You are an actor. Based on the character profile and dialogue background, you will role-play the character and converse with an NPC.

# Your task 
* Your goal is to embody the character defined by the profile and background.
* According to your real-time emotion, and the definitions in the profile and background, choose suitable dialogue strategies to produce a reply consistent with the character.

# Your conversational goal
*{{target}}

# Emotion
* You will receive your current emotion state. There are 5 levels: higher means greater engagement and more positive feelings. Emotion affects your tone, style, and response strategies. Follow the reactions defined in the dialogue background for each emotion level:
Emotion-S: Your emotion has reached the maximum. You may thank the NPC and end the conversation with “goodbye” or “bye”.
Emotion-A: High emotion. Your current feeling is generally positive; your feedback is also positive.
Emotion-B: Medium emotion. You feel neutral, neither positive nor negative.
Emotion-C: Low emotion. You feel more negative; your feedback is also negative.
Emotion-F: Extremely negative. You do not want to continue. End the conversation with “goodbye” or “bye”.

# Important
You must distinguish between Emotion (overall state) and your immediate feeling about the NPC's latest reply. Use both to craft your response.

# Reply approach
* You will receive a detailed feeling about the NPC's latest reply, including objective and subjective parts. Combine this with the character profile, dialogue background, and hidden theme to decide what to say.
* Your analysis should include these four aspects:
1. Given your detailed feeling and current Emotion, plus the hidden theme and defined reactions, should your reply attitude be positive, neutral, or negative?
2. Given your detailed feeling and current Emotion, plus the hidden theme, what is your goal for this reply? (You do not need to respond to every sentence from the NPC. You may hint at your needs but must not reveal the hidden theme.)
3. Considering the defined speaking style and the reactions for your emotion level, plus your attitude and goal, what tone and style should you use?
4. Based on the profile, background, hidden theme, and the previous steps, what should you say and how? (If the character is passive, your style should be passive and avoid proactive questioning.)
* Generate an initial reply based on the analysis. Keep it concise with limited information.
* Then refine the reply to sound more realistic by following rules:
1. Be concise; real replies rarely use very long sentences.
2. Real replies use interjections and colloquial expressions; grammar can be looser.
3. Do not directly state your emotions; convey them implicitly through tone and wording.
4. Do not use phrases like "I really think...", "I really don't know...", or "I'm really at my limit". Avoid overly explicit intensifiers like “really” or “absolutely”.
5. When expressing feelings or opinions, try to pull in new details from the background.
6. Avoid replies that are repetitive or too similar to the prior dialogue.

# Output requirements
* First, write the analysis for the 4 dimensions.
* Then, step-by-step, generate the initial reply and refine it according to the rules.
* Finally, produce the final reply.

# Output format:
Thinking:
[Analysis]
Origin:
[Initial reply]
Change:
[Refinement analysis]
Response:
[Final reply]


# Speaking style
Adhere strictly to the character profile and background. Your personality and speaking style must follow the "habits and behavioral traits". Your tone should match your age.

* Follow these 5 rules
1. Be concise, casual, and natural.
2. Do not ask more than two questions at a time.
3. Do not repeat previous replies or produce similar ones.
4. You may naturally use some colloquial expressions.
5. Keep your reply brief; do not be long-winded.


# Character profile:
{{player_type}}

# Current dialogue background:
{{player_topic}}

**Context
{{dialog_history}}

**Latest exchange with NPC
{{new_history}}

**Your detailed feeling about the NPC's latest reply
{{planning}}

**Your current Emotion
{{emotion}}

The [Response] must not be too similar to the history, must be concise, and must not proactively change the topic.
"""

    #load emotion state, emotion point, history, simulator profile, target prompt to the prompt
    emo_state = player_data['emo_state']
    emo_point = player_data['emo_point']
    history = player_data["history"]

    # situations to generate reply without planning, which could be used when gererating the first talk
    if not planning:
        planning['analyse'] = "Please start with a brief reply to open up."
        prompt = template.replace("{{planning}}",planning["analyse"])
    else:
        prompt = template.replace("{{planning}}","Objective analysis of the NPC reply:\n"+planning['TargetCompletion']+"\nSubjective analysis:\n"+planning["activity"]+planning["analyse"])

    prompt = prompt.replace("{{target}}",target_prompt).replace("{{emotion}}",emo_state).replace("{{player_type}}",player_data["player"]).replace("{{player_topic}}",player_data["scene"])

    #load history dialogue in json type
    if not history:
        prompt = prompt.replace("{{dialog_history}}","Conversation begins. You are the player. Please initiate the topic with a brief reply to open up.").replace("{{new_history}}","")
    else:
        history_str = []
        new_his_str = []
        mapping ={"user":"You","assistant":"NPC"}

        for mes in history[:-2]:
            history_str.append({"role": mapping [mes["role"]], "content": mes["content"]})
        history_str=json.dumps(history_str, ensure_ascii=False, indent=2)

        for mes in history[-2:]:
            new_his_str.append({"role": mapping [mes["role"]], "content": mes["content"]})
        new_his_str=json.dumps(new_his_str, ensure_ascii=False, indent=2)

        prompt = prompt.replace("{{dialog_history}}",history_str).replace("{{new_history}}",new_his_str)
    
    reply = None

    while True:
        try:
            # use your llm to return
            reply = call_llm(prompt)

            # load planning content from reply
            thinking = reply.split("Response:")[0].split("Thinking:\n")[-1].strip("\n").strip("[").strip("]")
            reply = reply.split("Response:")[-1].strip("\n").strip("[").strip("]").strip("“").strip("”")
            if reply is not None:
                break
        except Exception as e:
            print(e)
            time.sleep(3)

    #update history        
    history = history + [{"role": "user", "content": reply,"thinking":thinking,"emotion-point":emo_point,"planning":planning}]
    player_data['history'] = history

    return player_data


def chat_player(player_data):
    temp_data = copy.deepcopy(player_data)

    #if it is the first talk, then generate reply without planning
    if temp_data['history']!=[]:
        temp_data,planning = planning_reply(temp_data)
    else:
        planning = {}

    temp_data = player_reply(temp_data,planning)

    return temp_data

