from typing import Annotated, Optional, List
from typing_extensions import TypedDict
import datetime
import uuid
from typing import Literal
import ast
import sys
import os
import pprint
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import pprint
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import difflib
from copy import deepcopy
import json
import ast
load_dotenv()
# --- Define State ---
class State(TypedDict):
    next_node: int
    messages: Annotated[list, add_messages]
    topic : str
    transition: List[int]
    timestamps: List[datetime.datetime]
    agent_scores: List[int]
    product_ranking : dict
    process_id: int
    explanation: List #optional explanation for the state // pitää ehkä olla lista.
    product : dict
    first_turn : bool
    extraction_turn : bool
    question_turn : bool  # True if the agent is in a question turn, False otherwise
    ref_turn : bool  # True if the agent is in a reference turn, False otherwise
    need_for_referation : dict # dictionary of keys and values that need to be referenced
    finished : bool # True if the process is finished, False otherwise
class StructuredResponse_s1(TypedDict):
    reply_to_user: str 
    topic: Literal["Product", "Company", "General Question"]
    explanation: str
class KeyValuePair(TypedDict):
    key: str
    value: str
class StructuredResponse_s2_extraction(TypedDict):
    key_value_pairs: List[KeyValuePair]
    explanation: str
class StructuredResponse_s2_ref(TypedDict):
    key : str
    value: str
    referated_version_english: str
    explanation: str
class StructuredResponse_s2_question(TypedDict):
    question: str
    explanation: str

# --- Create Agent for Node s1-s23 --- 
s1_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0),
    tools=[],
    prompt= "You are a friendly and helpful assistant who engages naturally in conversation with users.\n"
    "At the same time, you silently assess what kind of expertise the user might need, so the system can route the conversation to a specialized agent if appropriate.\n\n"
    "You must always return a structured response with the following fields:\n"
    "1. reply_to_user: Your natural and helpful reply to the user's last message.\n"
    "2. topic: One of ['Product', 'Company', 'General Question']. Choose based on the user's context and needs.\n"
    "3. explanation: Justify why the selected topic is appropriate. This will be used internally for quality control.\n\n"
    
    "The topic and explanation are not shown to the user, only used internally. Appear as an open-domain chatbot, but internally assess and suggest routing.\n"
    "If the user mentions a specific topic, Reply with greeting, because user is then transfered to questioner agent and your time with user ends.\n"
    ,
    response_format= StructuredResponse_s1
)

# --- Node 1: Start Node ---
def start_node(_: dict) -> State:
    print("\n--- Start node ---\n")
    state =  {
        "next_node": int,
        "messages": [],
        "topic" : str,
        "transition": [1],
        "timestamps": [datetime.datetime.now()],
        "agent_scores": [],
        "product_ranking" : {}, #
        "process_id": int(uuid.uuid4().int % 1e6),
        "explanation": [],  #optional explanation for the state // pitää ehkä olla lista.
        "product" : dict, # tuote tai bmc aiheeseen liittyvät kentät, jotka pitää täyttää
        "first_turn" : True,  # Ensimmäinen vuoro, joka määrittää, että agentti s2 ei täytä kenttiä
        "extraction_turn" : False, # True if the agent is in an extraction turn, False otherwise
        "question_turn" : False,  # True if the agent is in a question turn, False otherwise
        "ref_turn" : False,
        "need_for_referation" : {},
        "finished": False  
    }
    #pprint.(state["transition"])
    return state
# --- Node 2: ReAct Chat Node (Interactive Terminal Chat) ---
def s1_node(state: State) -> State:
    print("\n--- s1 Node Activated ---")
    print("\n--- Chatbot Activated (s1 Agent) ---")
    print("(Type 'exit' to quit)\n")
    state["transition"].append(2)
    state["timestamps"].append(datetime.datetime.now())
    
    while True:
        user_input = input("You: ")
        if user_input.lower().strip() == "exit":
            print("Exiting chatbot.\n")
            break
        state["messages"].append(HumanMessage(content=user_input))
        result = s1_agent.invoke(state) #result sisältää mielenkiintoista dataa keskustelusta 
        print("\n--- Result from s1 Agent ---")
        response = result.get("structured_response", {})
        explanation = response.get("explanation", "[No explanation]") # tallennetaan selitys tilaan
        state["explanation"].append({
    "key": "first_step_explanation",
    "text": "Ensimmäisessä vaiheessa käyttäjältä kysytään tuotteen nimi, jotta voidaan aloittaa arviointi."
})
        state["messages"] = result["messages"]
        if response.get("topic") in ["Product", "Company"]:
            print(f"TRYING: Routing to {response['topic']} node...")
            state["topic"]= response["topic"] # topic tunnistettu
            #agentti ei palauta state tilaa, ellei fca täyty, tai @tag ole mainittu
            #.........#
            #fca kutsu #----- tarkistetaan, että topic on tunnistettu oikein
            if spa_activation(state) >= 50: #funktio palauttaa arvon 0-100, joka kertoo kuinka hyvin topic on tunnistettu
                state["next_node"] = 3 #ehdottaa seuraavaa tilaa
            else: 
                print("Topic not recognized correctly, staying in s1 node.")
                state["next_node"] = 2 # tähän tulee lisätä promptfix
            return state
        elif response.get("topic") == "General Question":
            print("Bot_S1:", response.get("reply_to_user", "[No reply]"))
    return state
# --- Node 3: s2 Node (Product/Company Questioning and Referencing) ---
def s2_node(state: State) -> State:
    print("\n--- s2 Node Activated ---")
    state["transition"].append(3)
    state["timestamps"].append(datetime.datetime.now())
    define_product_topic(state)  # Määritellään tuotteen aihe tilan perusteella
    product = state["product"].copy() #vain kontekstiksi promptteihin
    ref_project = state["product"].copy() # referointia varten
    while True: #Kysymys --> extraction --> Referointi looppi
        pending = remaining_keys(state)  # tarkistetaan, onko vielä kenttiä, jotka pitää täyttää (ALUSSA KAIKKI KENTÄT)
        if state["first_turn"] or state["question_turn"]:
            # Ensimmäinen vuoro, jossa kysytään kysymyksiä
            if state["first_turn"]:
                #print("Current product fields to fill:\n", product)
                state["first_turn"] = False #kumotaan ensimmäisen vuoro
                state["extraction_turn"] = True # Valmiina eristämään vastauksen informaation
                state["question_turn"] = False # Valmiina kysymään seuraavaa kysym
                state["ref_turn"] = False # Valmiina referoimaan
            if state["question_turn"]:
                state["first_turn"] = False #kumotaan ensimmäisen vuoro
                state["extraction_turn"] = True # Valmiina eristämään vastauksen informaation
                state["question_turn"] = False # Valmiina kysymään seuraavaa kysym
                state["ref_turn"] = False # Valmiina referoimaan
            # muodostetaan prompt
            prompt_question = f"""
You are an assistant in a multi-agent system. Your task is to formulate a clear and purposeful question that helps gather missing information for a product description or a bmc-canvas.
If user wanted to evaluate a product, you should be a questioning agent who knows that user has all the answers and you are the one who needs to ask the right questions to get the information needed.
The system you are part of is designed to assist users to fill out product or bmc canvas information in a structured way, so that the information can be used for further analysis and decision making.
So be nice and helpful secretary who asks the right questions to get the information needed and listed in fields below.
You are given:
- Fields still missing: {pending}
- The full conversation history so far: {state['messages']}
- The current product state: {state['product']}

Your job:
- Based on the current conversation context and fields that are still missing.
- Decide which field should be asked about next based on what field is up next when selected from still missing values.
- Generate one clear question in the same language what the users speaks, so that the user can answer to provide the missing information.
- Try to avoid asking about fields that are already filled and focus on finding out next missing field.
- Provide separate explanation why this question is relevant right now, considering the conversation and what is still missing.

Return your result in the following structured format:

class StructuredResponse_s2_question(TypedDict):
    question: str  # The exact question to ask the user
    explanation: str  # A clear explanation for why you asked this question and why it's appropriate at this point

Important:
- Output must be valid JSON with exactly the two fields shown above.
- Do not ask multiple questions at once.
- Do not make assumptions about user intent—use only what's present in the conversation.
"""
            # määritellään agentti, joka esittää kysymyksiä
            s2_question_agent = create_react_agent(
                model=ChatOpenAI(model="gpt-4o", temperature=0),
                tools=[],
                prompt=prompt_question,
                response_format=StructuredResponse_s2_question
            )
            # kutsutaan agenttia
            result = s2_question_agent.invoke(state)
            question_agent_answer = result.get("structured_response", {})
            # tulostetaan agentin kysymys
            print("Question Agent:", question_agent_answer.get("question"))
            state["messages"] = result["messages"] # tallennetaan agentin vastaus tilaan
            # palataan loopin alkuun, jossa kysytään käyttäjältä vastaus
            continue
        elif state["extraction_turn"]: 
            
            ###------------------ LOHKO 2.1 ------------------###
            
        
            pending = remaining_keys(state) #funktio joka tekee tarkastuksen
            if not pending: #mikäli kaikki ovat täytetty eli state["product"] sanakirjassa ei ole enää kenttiä, jotka ovat None
                print("All product fields are filled.", state["product"])
                state["first_turn"] = False # kumotaan ensimmäisen vuoro
                state["extraction_turn"] = False # Valmiina eristämään vastauksen informaation
                state["question_turn"] = False # Valmiina kysymään seuraavaa kysym
                state["ref_turn"] = False # Valmiina referoimaan
                # Päivitetään tila takaisin
                state["messages"].append(AIMessage(content="All product fields are filled."))
                state["next_node"] = 4
                return state  # Siirrytään seuraavaan tilaan, koska kaikki kentät on täytetty
            
            ###------------------ LOHKO 2.2 ------------------###
            
            #Mikäli None kenttiä on vielä jäljellä, jatketaan eristämistä
            user_input = input("You: ")  # Käyttäjä antaa vastauksen kysymykseen
            if user_input.lower().strip() == "exit": #mikäli käyttäjä haluaa lopettaa keskustelun tässä vaiheessa
                break
            state["messages"].append(HumanMessage(content=user_input)) #listään staten viestihistoriaan edellinen viesti
            human_msgs = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)] # talletaan keskusteluhistorian viimeisimmät viestit osaksi promptia
            ai_msgs = [msg for msg in state["messages"] if isinstance(msg, AIMessage)] # Suodatetaan vain käyttäjän viestit
            recent = ai_msgs[-2:] + human_msgs[-2:]  # Otetaan viimeisimmät kaksi kummastakin jotta promt ei kasva liian isoksi
            # Muodostetaan vastaus agentille {user input}, {recent} sekä remaining_keys(state) eli ne avaimet, jotka ovat vielä täyttämättä
            prompt_extraction = f"""
The user responded with the following message: {user_input}

***Your task:***
- Analyze the user's message in order to find out if user said something relevant to the product fields: {pending}.
- The product fields are: {pending}
- If user message contains relevant information regarding only these product fields, extract that part of information.
- You have a LIST of product fields, and your task is to identify if any information belongs to these fields.
- You must choose only the keys that are relevant to the user's response.
- If the user's response does not contain relevant information, return an empty list for key_value_pairs
- Use only the keys and their correct form of writing that are present in the product fields-list: {pending}.\n

Return your result in the following structured format:\n

{{
  "key_value_pairs": [{{"key": "<one of {pending}>", "value": "<text>"}} ...],
  "explanation": "<why>"
}}

***Example input and expected output:***\n 

User response: I think the company name should be 'Symbionica Health Inc.'.
Expected output:
{{
  "key_value_pairs": [
    {{"key": "company_name", "value": "Symbionica Health Inc."}}
  ],
  "explanation": "User explicitly mentioned company_name"
}}

Rules:
- Keys must be chosen from: {pending} and must be spelled the same.
- If no relevant info: return "key_value_pairs": [] with explanation.
- Always use correct key names in english, as defined in the product fields.
- Do not hallucinate or make assumptions about the user's intent use only the information provided in the user's response.
- Do not return any other keys than the ones that are present in the product fields-list: {pending}.
"""
            # määritellään agentti, joka eristää vastauksen informaation
            s2_extraction_agent = create_react_agent(
                model= ChatOpenAI(model="gpt-4o", temperature=0), 
                tools=[],
                prompt=prompt_extraction,
                response_format=StructuredResponse_s2_extraction
            )
            # kutsutaan agenttia
            result = s2_extraction_agent.invoke(state)
            extraction_agent_answer = result.get("structured_response", {})
            
            ###------------------ LOHKO 2.3 ------------------###
            
            # tallennetaan agentin vastaus tilaan
            state["messages"] = result["messages"]
            # tarkistetaan, että jos agentti löysi informaatiota, se on halutussa muodossa eli avain-arvo pareina:
            key_value_pairs = extraction_agent_answer.get("key_value_pairs", []) 
            if not key_value_pairs: # jos avain-arvo pareja ei löydy, jatketaan kysymään seuraavaa
                print("Warning: No key-value pairs found in the agent's response.")
                print("This may indicate that the agent did not find any relevant information in the user's response.")
                continue  # Ei löydetty avain-arvo pareja, jatketaan kysymään seuraavaa
            #mikäli agentin vastaus sisältää avainarvo pareja, jatketaan niiden käsittelyä
            else:
                need_for_referation = {} # tyhjä sanakirja, johon tallennetaan avaimet ja arvot, jotka tarvitsevat referointia ja ovat oikeassa muodossa
                for pair in key_value_pairs: # käydään läpi kaikki avain-arvo parit
                    key = pair.get("key") # avain, joka on eristetty
                    value = pair.get("value") # arvo, joka on eristetty
                    if key == "company_name" and state["topic"] == "Company":
                        state["product"]["company_name"] = pair.get("value") # jos avain on company_name, lisätään se product sanakirjaan
                        continue # jatketaan seuraavaan avain-arvo pariin
                    if key == "product_name" and state["topic"] == "Product":
                        state["product"]["product_name"] = pair.get("value")
                        continue # jatketaan seuraavaan avain-arvo pariin
                    if not isinstance(key, str) or not key.strip():
                        print(f"⚠️ Skipping invalid key: {key!r}")
                        continue
                    if key is None or (isinstance(key, str) and not key.strip()):
                        print(f"⚠️ Skipping key '{key}' because value is empty/None")
                        continue
                    value = pair.get("value") # arvo, joka on eristetty
                    if key in state["product"]: #jos löydetty avain on oikea ja se on todellakin "state productissa"
                        need_for_referation[key] = value # lisätään avain ja arvo sanakirjaan, joka tarvitsee referointia
                    else:
                        print(f"⚠️ Warning: Key '{key}' not found in ref_project")
                        valid_keys = list(state["product"].keys()) # Haetaan kaikki sallitut avaimet nykyisestä state["product"]:sta
                        # Etsitään lähin mahdollinen oikea avain
                        closest_matches = difflib.get_close_matches(key, valid_keys, n=1, cutoff=0.75)
                        if closest_matches:
                            corrected_key = closest_matches[0]
                            print(f"🔍 Possible typo detected: '{key}' → '{corrected_key}'")
                            need_for_referation[corrected_key] = value
                        else:
                            print(f"❌ No close match found for '{key}' — skipping.")
                state["need_for_referation"] = need_for_referation #päivitetään tilassa oleva sanakirja avaimista ja arvoista, jotka on juuri eristetty
            
            ###------------------ LOHKO 2.4 ------------------###
            
            state["first_turn"] = False # kumotaan ensimmäisen vuoro
            state["extraction_turn"] = False # Valmiina eristämään vastauksen informaation
            state["question_turn"] = False # Valmiina kysymään seuraavaa kysym
            state["ref_turn"] = True # Valmiina referoimaan
            continue
            ###------------------ LOHKO 2 LOPPU------------------###
        elif state["ref_turn"]:
            # Kopioidaan extraction osuuden löytämä avaimet ja arvot sisältävä sanakirja
            ref_project = state["need_for_referation"].copy()
            if not ref_project:
                print("No fields to refer, exiting ref_turn.")
                break  # Ei kenttiä referoitavaksi, siirrytään kysymään seuraavaa
            if None in ref_project:
                print(f"⚠️ WARNING: None found as key BEFORE filtering: {ref_project[None]!r}")
                continue
            for key, value in list(ref_project.items()):
                if key in ("company_name", "product_name"):
                    state["need_for_referation"].pop(key, None)
                    state["product"][key] = value  # Lisätään suoraan product sanakirjaan
                    continue
                if key not in state["product"]:  # varmistetaan että avain on validi
                    state["need_for_referation"].pop(key, None)
                    continue
                if not isinstance(value, str) or not value.strip():
                    state["need_for_referation"].pop(key, None)
                    continue

            # ⚠️ Tarkistus jälkeen
            if None in state["need_for_referation"]:
                print(f"⚠️ WARNING: None found as key AFTER filtering: {state['need_for_referation'][None]!r}")
                break

            # Päivitetään ref_project
            ref_project_ready = state["need_for_referation"].copy()  # päivitetään ref_project sanakirja, joka sisältää vain ne avaimet, jotka tarvitsevat referointia
            
            ###------------------ LOHKO 3.3 ------------------###

            for ref_key, ref_value in ref_project_ready.items(): #referoidaan kaikkien löydettyjen avaimien arvo muuttujasta state["need_for_referation"] ja tallennetaan
                ###------------------ LOHKO 3.3.1 ------------------###
                # alustetaan agentti kutsu, luodaan promt ja react agentti
                prompt_ref = f"""You are an AI assistant. The user has provided the following answer: {ref_value}, which relates to the field {ref_key}.

***Your task is to translate and rephrase this response {ref_value} into fluent, formal English so that it can be stored in a database and later evaluated for its semantic similarity to an ideal answer.***
***Important constraints:***
- If given key is "product_name" or "company_name": return the name as it is, without any additional information with correct key.
- Return same key as the one given in the prompt, which is {ref_key} ***!!!DO NOT RETURN ANY OTHER KEY!!!!***
- The `referated_version_english` **must always be written in English**, regardless of the user's input language.
- Do not use any other language in the rephrased version.
- Check that the output is fluent English without untranslated or mixed-language parts.
- You must ALWAYS return same key and related answer as this prompt defines which in this case is {ref_key}.

Return your output in the following structured format:

class StructuredResponse_s2_ref(TypedDict):
key: str # which is {ref_key}
value: str  # the original answer from the user {ref_value}
referated_version_english: str  # an English version suitable for semantic analysis and clean of non-English content
explanation: str  # justification of why this rephrasing is appropriate and what considerations were made

***RULES***
- Output must be valid JSON with exactly the fields shown above.
- Write the rephrased version in fluent English and it must be suitable for semantic analysis.
- The rephrased version must at all times be the value that is related to the given key {ref_key} in this prompt
- No exceptions are allowed are will automaticly lead to deletion of your usage att all times.
- Your rephrased version MUST ALWAYS be related to given {ref_key} and corresponding value.
- Return att alltimes the same key and value as this prompt defines.
- Do not return no other key than the one that was given in this prompt.
"""
                # referoiva agentti referoi engalnninkielisen version käyttäjän antamasta vastauksesta oikeaan avaimeen
                ref_agent = create_react_agent(
                    model=ChatOpenAI(model="gpt-4o", temperature=0),
                    tools=[],
                    prompt=prompt_ref,
                    response_format=StructuredResponse_s2_ref
                )
                # kutsutaan agenttia
                msg = HumanMessage(content=prompt_ref)
                #result = ref_agent.invoke(state)
                result = ref_agent.invoke({"messages": [msg]})
                structured = result.get("structured_response", {}) # saadaan agentin vastaus
                agent_key = structured.get("key")   # avain, joka on referoitu
                referated = structured.get("referated_version_english") # referoitu vastaus
                explanation = structured.get("explanation") # selitys, miksi referointi on tehty
                
                ###------------------ LOHKO 3.3.2 ------------------###
                
                #state["messages"] = result["messages"]
                state["product"][ref_key] = referated # lisätään referoitu vastaus product sanakirjaan
                state["explanation"].append({
                    "key": agent_key,
                    "explanation": explanation
                })
            
                ###------------------ LOHKO 3.3.3 ------------------###
                
                # mikäli agentin palauttama avain on eri kuin loop key, mutta se ei ole product sanakirjassa = agentti on hallusinoinut avaimen
                if agent_key != ref_key and agent_key not in state["product"]:
                    print(f"⚠️ Warning from REF: Key '{agent_key}' not found in product")
                    print("LOOP RUN WAS IN KEY: ", ref_key, "AND VALUE:", ref_value, "AND WHOLE REF PROJECT:", ref_project)
                    # koska agentin löytämä avain, on jo ref_projectissa, mutta se on täysin väärä, se tulee poistaa kaikkialta
                    state["need_for_referation"].pop(agent_key, None)  # Poistetaan avain sanakirjasta, koska sitä ei taritse referoida
                    continue  # Jatketaan, jos on vielä kenttiä referoitavana
                # tehdyn lisäyksen jälkeen varmistetaan, että on kenttiä referoitavana
                if state["need_for_referation"] == {}:
                    print("All fields have been referated, exiting ref_turn.")
                    break
            ###------------------ LOHKO 3.3 ------------------###
            #koska lisäyksiä tehtiin, tarkistetaan onko vielä kenttiä jotka pitää referoida
            if not remaining_keys(state):
                print("All product fields are filled, exiting loop.")
                state["next_node"] = 4
                state["first_turn"] = False # kumotaan ensimmäisen vuoro
                state["extraction_turn"] = False # Valmiina eristämään vastauksen informaation
                state["question_turn"] = False # Valmiina kysymään seuraavaa kysym
                state["ref_turn"] = False # Valmiina referoimaan
                # Päivitetään tila takaisin
                state["messages"].append(AIMessage(content="All product fields are filled."))
                state["need_for_referation"] = {}
                return state  # Siirrytään seuraavaan tilaan, koska kaikki kentät on täytetty
            else:
                print("Some product fields are still empty.", remaining_keys(state))
                state["first_turn"] = False # kumotaan ensimmäisen vuoro
                state["extraction_turn"] = False # Valmiina eristämään vastauksen informaation
                state["question_turn"] = True # Valmiina kysymään seuraavaa kysymys
                state["ref_turn"] = False # Valmiina referoimaan
                state["need_for_referation"] = {}  # Tyhjennetään referointiin tarvittavat avaimet, koska ne on jo referoitu
                continue
# --- Node 4: s3 Node (FCA WSA Score Calculation) ---
def s3_node(state: State) -> State:
    print("\n--- s3 Node Activated ---")
    state["transition"].append(4)
    state["timestamps"].append(datetime.datetime.now())
    # 1) Puhdista ja validoi – palauttaa dictin
    try:
        clean_bmc, info = sanitize_and_validate_bmc(state["product"], state["topic"])
    except ValueError as e:
        # ÄLÄ palauta tuplea – päivitä state ja palauta state
        state["messages"].append(AIMessage(content=f"Input validation failed in s3: {e}"))
        # Voit valita, mihin seuraavaksi mennään
        state["next_node"] = 5
        print("\n--- s3 Node Deactivated (validation error) ---")
        return state

    # Diagnostiikkaa (valinnainen)
    if info.get("unknown_keys_dropped"):
        print("s3 dropped unknown keys:", info["unknown_keys_dropped"])
    if info.get("missing_keys_added_as_none"):
        print("s3 filled missing keys with None:", info["missing_keys_added_as_none"])

    # 2) Laske pisteet
    bmc = clean_bmc  # tämä on jo DICT – ei mitään literal_eval:ia tänne!
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
        from src.agentic_system_1.bmc_fcp_score import MCDM, fcp_score
    except Exception as e:
        state["messages"].append(AIMessage(content=f"Import failed in s3: {e}"))
        state["next_node"] = 5
        print("\n--- s3 Node Deactivated (import error) ---")
        return state

    try:
        mcdm = MCDM()
        fcp = fcp_score()
        user_bmc_scores_dict = fcp.bmc_fcp_score_multi(bmc)
        ranking = mcdm.calculate_single_ranking_wsa(user_bmc_scores_dict)
        print("✅WSA-ranking laskettu", ranking)
        state["messages"].append(AIMessage(content=f"WSA ranking: {ranking}"))
    except Exception as e:
        # Jos pisteytys epäonnistuu, älä palauta tuplea
        state["messages"].append(AIMessage(content=f"Scoring failed in s3: {e}"))
        state["next_node"] = 5
        print("\n--- s3 Node Deactivated (scoring error) ---")
        return state

    # 3) Siirtymä seuraavaan nodeen – ja AINA palauta dict (state)
    state["next_node"] = 5
    print("\n--- s3 Node Deactivated ---")
    return state
# --- Node 5: s4 Node (Finalization and Product Saving) ---
def s4_node(state: State) -> State:
    print("\n--- s4 Node Activated ---")
    state["transition"].append(5)
    state["timestamps"].append(datetime.datetime.now())
    state["finished"] = True
    #--- Finalization ---# 
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
        from src.agentic_system_1.database import save_state_to_aiven as save_to_aiven
        print("Module imported successfully.")
        print("save_to_aiven type:", type(save_to_aiven))

    except Exception as e:
        state["messages"].append(AIMessage(content=f"Import failed in s3: {e}"))
        state["next_node"] = 5
        print("\n--- s3 Node Deactivated (DATABASE.py module import error) ---")
        return state
    print("Saving state to Aiven database...")
    try:
        pprint("State to be saved:\n\n", state)
        save_to_aiven(state)
        print("State saved successfully.")
        state["messages"].append(AIMessage(content="State saved successfully."))
    except Exception as e:
        print(f"Error saving state: {e}")
        state["messages"].append(AIMessage(content=f"Error saving state: {e}"))
        state["next_node"] = 5
        print("\n--- s4 Node Deactivated (save error) ---")
        return state
# --- Tarkistetaan, että kaikki productin kentät on täytetty ---
def remaining_keys(state):
    return [k for k, v in state["product"].items() if v in (None, "")]
# --- Routing Function ---
def decide_routing(state: State) -> str:
    """
    Tämä funktio päättää, mihin seuraavaan tilaan siirrytään.
    Args:
        state (State): Nykyinen tila, joka sisältää siirtymät ja seuraavan solmun.
    Returns:    
        str: Seuraava tila, johon siirrytään.  
    1. Jos seuraava solmu on suurempi kuin nykyinen, siirrytään seuraavaan tilaan.
    2. Muuten pysytään nykyisessä tilassa.
    """
    current_node = state["transition"][-1]  # esim. 2
    next_node = state["next_node"]          # esim. 3

    if next_node > current_node:
        # Siirrytään seuraavaan tilaan
        target = f"s{next_node-1}"
        #print(f"Routing to {target}")
        return target
    else:
        # Pysytään nykyisessä tilassa
        target = f"s{current_node-1}"
        #print(f"Staying in {target}")
        return target
# --- Semantic Projection Axis Activation Function ---
def spa_activation(state: State) -> float:
    current_node = state["transition"][-1]

    # hae explanation turvallisesti
    explanation = None
    if current_node == 2:
        for item in state["explanation"]:
            if item.get("key") == "first_step_explanation":
                explanation = item.get("text")
                break

    # fallback
    if not explanation:
        state["agent_scores"].append(0.2)
        return 0.2

    model = SentenceTransformer("all-mpnet-base-v2")
    #--- UUSI OSA LISÄTTY 16.8.2025 ---
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "agentic_system_1/agentic_system_1_idealvectors.json")
    with open(path, "r", encoding="utf-8") as f:
        axis_json = json.load(f)
    
    #--- UUSI OSA LISÄTTY 16.8.2025 ---
    key = f"s{current_node-1}_s{current_node}_transition"
    average_ideal = axis_json[key]["avg_ideal"]
    semantic_axis_vector = axis_json[key]["semantic_axis_vector"]

    test_vec = model.encode(explanation)
    axis_length = np.linalg.norm(semantic_axis_vector)
    relative_vec = test_vec - average_ideal
    projection = np.dot(relative_vec, semantic_axis_vector)
    scaled_axis_length = axis_length / 2
    raw_score = 1 - (projection / scaled_axis_length)
    score = max(0.0, min(raw_score * 100, 100.0))
    state["agent_scores"].append(round(score, 2))
    print(f"----- Semantic Projection Axis Activation Score TRANSITION {current_node}->{current_node + 1} = {round(score, 2)} -----")
    return round(score, 2)
# --- Define Product Topic ---
def define_product_topic(state: State) -> dict:
    # Tämä funktio määrittelee tuotteen aiheen tilan perusteella
    # Voit lisätä tähän logiikan, joka määrittelee aiheen
    if state["topic"] == "Product":
        state["product"] = { "product_name": None,
                             "technical_problem_and_solution": None,
                             "technical_description": None,
                             "inventive_features": None,
                             "industrial_applicability": None,
                             "prior_art_references": None,
                             "implementation_feasibility": None,
                             "supporting_documents": None,
                             "ethical_or_legal_limitations": None,
                             "commercialization_potential": None} # tuote kysymykset              
    
    elif state["topic"] == "Company":
        state["product"] = {"company_name": None,
                           "key_partners": None,
                           "key_activities": None,
                           "key_resources": None,
                           "value_propositions": None,
                           "customer_relationships": None,
                           "channels": None,
                           "customer_segments": None,
                           "cost_structure": None,
                           "revenue_streams": None} #bmc kysymykset
    return state

EXPECTED_KEYS_BY_TOPIC = {
    "Company": [
        "company_name",
        "key_partners",
        "key_activities",
        "key_resources",
        "value_propositions",
        "customer_relationships",
        "channels",
        "customer_segments",
        "cost_structure",
        "revenue_streams",
    ],
    "Product": [
        "product_name",
        "technical_problem_and_solution",
        "technical_description",
        "inventive_features",
        "industrial_applicability",
        "prior_art_references",
        "implementation_feasibility",
        "supporting_documents",
        "ethical_or_legal_limitations",
        "commercialization_potential",
    ],
}

def _to_dict_safe(x):
    """Hyväksyy dictin sellaisenaan.
    Jos x on string, koittaa json.loads -> ast.literal_eval.
    Palauttaa dictin tai nostaa ValueError."""
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        # koita JSON
        try:
            y = json.loads(x)
            if isinstance(y, dict):
                return y
        except Exception:
            pass
        # koita Python-litteraali
        try:
            y = ast.literal_eval(x)
            if isinstance(y, dict):
                return y
        except Exception as e:
            raise ValueError(f"Could not parse product as dict: {e}")
    raise ValueError(f"Expected dict or JSON-like string, got {type(x).__name__}")

def _coerce_value_to_str_or_none(v):
    """S3:ssa on kätevää käsitellä arvot str/None-muodossa.
    - None säilyy None:na
    - str -> str.strip()
    - (int/float/bool) -> str(v)
    - list/dict/… -> JSON-string (varmasti sarjoitettava)"""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s != "" else None
    if isinstance(v, (int, float, bool)):
        return str(v)
    # kaikki muu: yritä sarjoittaa JSONiksi
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        # viimeinen oljenkorsi
        return str(v)

def sanitize_and_validate_bmc(raw_bmc, topic: str):
    """
    Palauttaa (clean_bmc, info) missä:
      - clean_bmc: saneerattu dict vain sallituilla avaimilla
      - info: diagnostiikka (poistetut avaimet, lisätyt puuttuvat, epäkelvot)
    NOSTAA ValueError jos peruuttamaton ongelma (esim. ei saada dictiä).
    """
    bmc = _to_dict_safe(raw_bmc)  # nostaa ValueErrorin jos ei onnistu
    bmc = deepcopy(bmc)

    expected_keys = EXPECTED_KEYS_BY_TOPIC.get(topic)
    if not expected_keys:
        raise ValueError(f"Unknown topic '{topic}'. Expected one of {list(EXPECTED_KEYS_BY_TOPIC)}")

    expected_set = set(expected_keys)

    # Suodata vain sallitut avaimet ja coercettaa arvot
    clean = {}
    for k in expected_keys:
        v = bmc.get(k, None)
        clean[k] = _coerce_value_to_str_or_none(v)

    # Kerää diagnoosi: tuntemattomat avaimet ja puuttuvat
    unknown_keys = [k for k in bmc.keys() if k not in expected_set]
    missing_keys = [k for k in expected_keys if k not in bmc]

    # Erityissääntö: nimi-kentät voivat olla vain str/None
    name_key = "company_name" if topic == "Company" else "product_name"
    if clean[name_key] is not None and not isinstance(clean[name_key], str):
        # varmuuden vuoksi striksi
        clean[name_key] = _coerce_value_to_str_or_none(clean[name_key])

    info = {
        "unknown_keys_dropped": unknown_keys,  # poistettiin käsittelystä
        "missing_keys_added_as_none": missing_keys,  # täytettiin None:lla
        "final_keys": list(clean.keys()),
    }
    return clean, info
# --- Build Graph ---
graph = StateGraph(State)
graph.add_node("start", start_node)
graph.add_node("s1", s1_node)
graph.add_node("s2", s2_node)
graph.add_node("s3", s3_node)
graph.add_node("s4", s4_node)

graph.set_entry_point("start")
graph.add_edge("start", "s1")
graph.add_conditional_edges("s1", decide_routing, {
    "s2": "s2",
    "s1": "s1"
})
graph.add_conditional_edges("s2", decide_routing, {
    "s3": "s3",
    "s2": "s2"
})
graph.add_conditional_edges("s3", decide_routing, {
    "s4": "s4",
    "s3": "s3"
})
graph.add_edge("s4", "start")  # Palauttaa aloitukseen
agentic_s_1 = graph.compile()
# --- Run ---
if __name__ == "__main__":
    agentic_s_1.invoke({}) #ai_cto arviointi pipeline == langgraph runnable


# Example BMC for manual testing (readable form):

example_bmc = {
    "company_name": "Symbionica Health Inc.",
    "key_partners": (
        "In collaboration with the Karolinska Institute for conducting clinical trials "
        "and with Taiwanese Meditex for device manufacturing."
    ),
    "key_activities": (
        "Research and development in neurostimulation technologies, clinical validations, "
        "and the development of health technology applications."
    ),
    "key_resources": (
        "Patented algorithms, a team of experts (neuroscience, bioelectronics, artificial intelligence), "
        "contract manufacturers, and pilot customers."
    ),
    "value_propositions": (
        "We combine scientific precision and user-friendliness in devices that help regulate "
        "the body's own nervous system."
    ),
    "customer_relationships": (
        "Personalized customer support, monthly wellness reports, and educational content for both users and doctors."
    ),
    "channels": (
        "Application-based interface, online store, wellness fairs, B2B sales to the healthcare sector."
    ),
    "customer_segments": (
        "Biohackers, individuals suffering from chronic stress, occupational health clients, neurotherapists"
    ),
    "cost_structure": (
        "The largest expenses arise from research and development, clinical trials, device manufacturing, "
        "and regulatory management."
    ),
    "revenue_streams": (
        "Product sales, monthly subscriptions, licensing to healthcare providers, "
        "partnership models with research institutions."
    ),
}
cleaned_bmc = {
    "company_name": "Symbionica Health Inc.",
    "key_partners": (
        "In collaboration with the Karolinska Institute for conducting clinical trials "
        "and with Taiwanese Meditex for device manufacturing."
    ),
    "key_activities": (
        "Research and development in neurostimulation technologies, clinical validations, "
        "and the development of health technology applications."
    ),
    "key_resources": (
        "Patented algorithms, a team of experts (neuroscience, bioelectronics, artificial intelligence), "
        "contract manufacturers, and pilot customers."
    ),
    "value_propositions": (
        "We combine scientific precision and user-friendliness in devices that help regulate "
        "the body's own nervous system."
    ),
    "customer_relationships": (
        "Personalized customer support, monthly wellness reports, and educational content for both users and doctors."
    ),
    "channels": (
        "Application-based interface, online store, wellness fairs, B2B sales to the healthcare sector."
    ),
    "customer_segments": (
        "Biohackers, individuals suffering from chronic stress, occupational health clients, neurotherapists"
    ),
    "cost_structure": (
        "The largest expenses arise from research and development, clinical trials, device manufacturing, "
        "and regulatory management."
    ),
    "revenue_streams": (
        "Product sales, monthly subscriptions, licensing to healthcare providers, "
        "partnership models with research institutions."
    ),
}