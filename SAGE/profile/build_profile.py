import random
import time
import requests
import json
import uuid
import argparse
from utils.llm_utils import get_llm

character = {
"Negative":["angry","irritable","vulgar","arrogant","conceited","vain","selfish","mean","lazy","suspicious"],
"Passive":["introverted","straightforward","resentful","manic","anxious","cautious","insecure","patient","suspicious","timid","optimistic","humble","tolerant","steady","quick-witted"],
"Avoidant":["introverted","cautious","insecure","manic","timid","avoidant","sensitive","suspicious","aloof","taciturn","humble","tolerant","steady"]
}

hidden_task = {
"Rational":[
    "You want the other person to analyze the issues in a dialectical way",
    "You want advice that can truly help you solve your current dilemma",
    "You want to analyze the reasons behind other people's actions in the event",
    "You want the other person to guide you to reflect on the event for personal growth"
],
"Emotional":[
    "You want sincere praise for your specific actions in the event",
    "You want the other person to attentively listen to your emotional venting",
    "You want deep empathy for your feelings, not superficial comfort",
    "You believe you bear no responsibility in the event and want the other person to agree"
]
}

def call_llm(prompt):
    """
    Call LLM with the given prompt and return the response.
    
    Args:
        prompt: String prompt to send to the LLM
    
    Returns:
        str: The LLM response content
    """
    # Configure the LLM (you can modify these settings as needed)
    llm_config = {
        'type': 'openai',  # or 'azure', 'google', 'anthropic', etc.
        'name': 'gpt-3.5-turbo',  # model name
        'temperature': 0.7
    }
    
    # Get the LLM instance
    llm = get_llm(llm_config)
    
    # Call the LLM with the prompt
    response = llm.invoke(prompt)
    
    # Extract the content from the response
    return response.content

def role_generate(talking_set):

    #prompt template
    template = '''You are a professional screenwriter. You excel at extracting a character profile from given information and enriching it with sufficient detail.

# Your task
Given three things the character said to a friend and the character's personality traits, imagine and describe the character profile, including:
* Name, age, gender
* Occupation, habits and behavioral traits
* Personal hobbies
* Speaking style

# Analysis
1. Based on the personality and the three utterances, infer the basic information — name, age, gender.
2. Considering the personality, infer plausible occupations and derive habits and behavioral traits. Ensure diversity and make sure traits reflect the personality.
3. Infer and summarize the character's hobbies; provide 3 detailed descriptions.
4. Define the character's likely speaking style according to the traits.
5. Define how proactively the character tends to speak and guide conversations.

* Note: The generated profile should reflect both positive and negative sides of the personality.

## Example
# Three utterances when chatting with a friend:
What kind of exercise do you usually do to stay in shape?
Got it. Do you go to the gym? Do you know which machines train leg muscles?
Haha, it's fine, no worries.

# Personality traits
The character is proactive, with extroversion, casualness, and impatience.

# Character profile
* Name: Li Jiajun
* Age: 28
* Gender: Male
* Occupation: Vocal coach

* Hobbies:
1. He loves fitness and sports. He keeps healthy through running, swimming, and gym workouts.
2. He enjoys reading, but his impatience makes it hard to stick with classics; he prefers trending web novels.
3. He also enjoys music, especially jazz and rock, and often goes to live houses to watch shows and make friends.

* Habits and behavioral traits:
He is very disciplined and schedules exercise daily regardless of workload.
He studies how to use various gym machines and often asks others how to better train specific muscle groups.
Due to his work, he takes special care of his throat and vocal cords. He strictly controls his diet, also because of his love for fitness.
Sometimes he stays up too late reading books he likes, which he regrets but cannot always control.

* Speaking style:
He is proactive and extroverted, likes to control the topic.
He is casual and shrugs off sarcasm with a laugh.
His impatience affects his speaking style; when focused on problem-solving, he gets angry at anything that blocks progress.

* Speaking manner:
He asks questions to guide the topic.
He will proactively voice his thoughts when the topic is uninteresting.

# Three utterances:
{ques3} 

# Personality traits
{character}

# Do not generate game or IT-related occupations

# Character profile
'''

    #prepare parameters for the prompt

    #randomly choose 3 talks
    ques_ = random.sample(talking_set,3)
    question = [] 
    ques3 = ""
    for i in ques_:
        ques3+=i+"\n"
        question.append(i)

    #randomly generate 1 main characteristic and 3 sub characteristics
    main_cha = random.choice(list(character.keys()))
    cha_group = random.sample(character[main_cha],3)
    character_str = "The character has a {} personality with traits: {}, {}, {}.".format(main_cha,cha_group[0],cha_group[1],cha_group[2])

    print("Three utterances:\n"+ques3)
    print("Character traits:"+character_str)

    #use your llm to generate player with prompt
    ask_prompt = template.replace('{ques3}', ques3).replace('{character}', character_str)
    player = call_llm(ask_prompt)

    
    print("Character profile:\n")
    print(player)

    return player, question, main_cha,cha_group,character_str

def scene_generate(player,topic_set,character_str):
    template = '''You are a professional screenwriter. You are good at expanding a dialogue script based on a character profile and inter-personal conversation.

# Your task
You will receive a character profile and a confiding theme. Write a background story for a dialogue where the "player confides to the NPC", with {topic} as the background topic and "{task}" as the hidden theme.
Your script should include:
1. Based on the player profile and confiding theme, and grounded in the hidden theme, define what the player might want to confide to the NPC related to the theme.
2. Based on the player profile and theme, expand the detailed background events of the confiding content. The background should include:
    - The cause of the event

    - The unfolding of the event, including:
    * A timeline
    * Sub-events at each time point, and the player's specific thoughts and feelings in each

    - The main conflicts in the event, including:
    * Conflict events
    * Involved roles
    * Underlying reasons for conflicts (in-depth analysis)

    - The difficulties the player encounters, including:
    * Previously attempted but unsuccessful solutions
    * The problems the player currently faces
    
    - The current status of the event  
3. The player's possible reactions in different states. Based on the character's goals and hidden theme, and the profile and traits, define possible reactions during the dialogue, including:
    - Reactions under different emotion levels (emotion represents conversational engagement). Include:
    * When emotion is high: dialogue style, e.g., calm, relaxed
    * When emotion is low: dialogue style, e.g., agitated, irritable, despairing
    * When emotion is medium: dialogue style, e.g., impatient, disappointed
4. Given the hidden theme, how would the character react to different NPC replies? Include:
    - What kinds of NPC replies align with the hidden theme and raise emotion?
    - What kinds of NPC replies deviate from the hidden theme and lower emotion?

Notes:
1. You must write the specific background events the player wants to confide about. Do not write the actual confiding content or specific dialogues.

2. Each sub-event should have sufficient detail.
* Incorrect example:
    "The player worked hard on a market analysis report but did not get the manager's approval."
    - Too brief; lacks detail and information.
* Correct example:
    "For a week, the player stayed up until 3 a.m. to revise the report, but every submission was rejected for reasons like 'format not meeting requirements' or 'no pain points identified' without concrete guidance or revision directions. The player feels lost, not knowing how to meet the manager's standards."
    - Detailed and informative.
    
3. The player's specific thoughts and feelings should also be detailed.
* Incorrect example:
    "The player feels tired and confused about maintaining the relationship and doesn't know whether to continue."
* Correct example:
    "The player feels uncertain about the current relationship with his girlfriend, specifically: 1) unsure whether the relationship has broken down and unable to find a suitable opportunity to ask; 2) often reminisces about past happy moments, and the current painful situation makes him hesitate to continue."

4. The player's goal should prioritize fulfilling the hidden theme rather than seeking concrete advice.

5. Write the background according to the confiding theme only. Do not mix in other themes (e.g., if the theme is interpersonal relationships, do not also include health or work-pressure topics).

6. Do not write the story continuation or specific dialogue.

7. The setting is that confiding should improve emotions, not endless complaining.

8. Define in detail the character's reactions to various NPC replies according to the hidden theme.

# Player profile
{player}

# Personality
{character}

# Confiding theme
{topic}

# Hidden theme
{task}

# Script for "player confides to NPC": 
'''

    # prepare scene generation prompt

    #randomly choose 1 topic
    topic = random.sample(topic_set,1)[0]

    #randomly generate 1 hidden task
    if random.random()<=0.5:
        task = random.sample(hidden_task["Rational"],1)[0]
    else:
        task = random.sample(hidden_task["Emotional"],1)[0]

    #use your llm to generate player with prompt    
    ask_prompt = template.replace("{player}", player).replace("{topic}",topic).replace("{task}",task).replace("{character}",character_str)
    scene = call_llm(ask_prompt)+"\n####Hidden theme:\n***"+task
    print("Current dialogue background:\n")
    print("Background topic:"+topic)
    print("Hidden theme:"+task)
    print(scene)

    return scene,topic,task


#add your store address here
store_file = ""
collect_times = 100

data = []

#prepare your seed talking set in the seed talking file, e.g., "Went to the park today, so happy!"
#prepare your seed topic set in the seed topic file, e.g., "What to do if grades are always poor at school?"
talking_set = ["Went to the park today, so happy!"]
topic_set = ["What to do if grades are always poor at school?"]

with open(seed_talking_file,'r', encoding='utf-8') as datafile:
    for line in datafile:
        talking_set.append(line.strip("\n"))

with open(seed_topic_file,'r', encoding='utf-8') as datafile:
    for line in datafile:
        topic_set.append(line.strip("\n"))

# start to generate profile, including role and scene
for times in range(collect_times):
    player, ques3, main_cha,cha_group,character_str = role_generate(talking_set)
    scene, topic, task = scene_generate(player,topic_set,character_str)

    session = {"id":"","player":"","scene":"","3-question":[],"main_cha":"","cha_group":[],"topic":"","task":""}
    session["player"] = player
    session["scene"] = scene
    session["3-question"] = ques3
    session["main_cha"] = main_cha
    session["cha_group"] = cha_group
    session["topic"] = topic
    session["task"] = task
    session["id"] = str(uuid.uuid4())

    with open(store_file,'a',encoding='utf-8') as file:
        file.write(json.dumps(session, ensure_ascii=False) + "\n")


