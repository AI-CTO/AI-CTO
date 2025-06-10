import openai
import os
import random


class Scheduler:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.previous_states = []
        self.project= []
        self.tool1_start = {
                            "type": "function",
                            "name": "get_weather",
                            "description": "Get current temperature for provided coordinates in celsius.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number"},
                                    "longitude": {"type": "number"}
                                },
                                "required": ["latitude", "longitude"],
                                "additionalProperties": False
                            },
                            "strict": True
                        }
        self.tool2_add_numbers = {
                            "type": "function",
                            "name": "get_weather",
                            "description": "Get current temperature for provided coordinates in celsius.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number"},
                                    "longitude": {"type": "number"}
                                },
                                "required": ["latitude", "longitude"],
                                "additionalProperties": False
                            },
                            "strict": True
                        }
        self.tool3_add_letters = {
                            "type": "function",
                            "name": "get_weather",
                            "description": "Get current temperature for provided coordinates in celsius.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number"},
                                    "longitude": {"type": "number"}
                                },
                                "required": ["latitude", "longitude"],
                                "additionalProperties": False
                            },
                            "strict": True
                        }
        self.tool4_add_other_marks = {
                            "type": "function",
                            "name": "get_weather",
                            "description": "Get current temperature for provided coordinates in celsius.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number"},
                                    "longitude": {"type": "number"}
                                },
                                "required": ["latitude", "longitude"],
                                "additionalProperties": False
                            },
                            "strict": True
                        }
        

    def scheduler(self, project):
        pass
        #input message (mihtä funktiota kutsua)+ project jotta sen seuraavan tilan voi arvioida
        #palauttaa seuraavan tilan "kutsumalla tätä funktiota joka puolestaan kutsuu jälleen sceheduleria"

    def starting_state(self, project):
        state_id = 1
        dize = random.randint(1, 10)
        if dize <= 4:
            self.sheduler(project)
        else:
            resources = ["start"]
            project.append(resources[0])
            self.previous_states.append(state_id)
            self.scheduler(project)

    def add_numbers(self, project):
        state_id = 2
        dize = random.randint(1, 10)
        if dize <= 4:
            self.sheduler(project)
        else:
            resources = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
            r_reseurces = random.shuffle(resources)
            project.append(r_reseurces[0])
            self.previous_states.append(state_id)
            self.scheduler(project)
    
    def add_letters(self, project):
        state_id = 3
        dize = random.randint(1, 10)
        if dize <= 4:
            self.sheduler(project)
        else:
            resources = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
            r_reseurces = random.shuffle(resources)
            project.append(r_reseurces[0])
            self.previous_states.append(state_id)
            self.scheduler(project)

    def add_other_marks(self, project):
        state_id = 4
        dize = random.randint(1, 10)
        if dize <= 4:
            self.sheduler(project)
        else:
            resources = ["@", "#", "$", "%", "&", "*", "!", "?"]
            r_reseurces = random.shuffle(resources)
            project.append(r_reseurces[0])
            self.previous_states.append(state_id)
            self.scheduler(project)