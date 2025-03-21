'''
How to use these resources:

1. **Create a BusinessModelCanvas instance**  
   Call `variable = Module.BusinessModelCanvas()`.  
   This initializes an empty Business Model Canvas.

2. **Update the BusinessModelCanvas with text input**  
   Call `variable.update_from_text('text')`, where `'text'` is the input data.  
   The AI will analyze and fill in the relevant fields of the BMC.

   + thread_id should be added to the completion object to keep track of the conversation. NOT DONE YET

3. **Retrieve the updated BusinessModelCanvas**  
   Call `json_output = variable.model_dump_json(indent=2)`.  
   This returns a **JSON-formatted** object where each field is a key-value pair.  
   This can be used in **frontend visualization** or **data storage**.

4. **Create a BmcValidator instance** 
   Call `validator = Module.BmcValidator()`.  
   This initializes the BMC validation module.

5. **Compare the current BMC with ideal BMC examples**  
   Call `validation = validator.current_vs_ideal_score(json_output)`.  
   This returns a JSON object with **True/False values** for each evaluation metric.

6. **Calculate the comparison score**  
   Call `score = validator.calculate_score(validation)`.  
   The score is between **0-6**, converted to **percentage** by multiplying it by **16.67**.
'''


import json
import re
import uuid
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional, List, Dict

client = OpenAI()

class BusinessModelCanvas(BaseModel):
    print("BMC IS RUNNING")
    company_name: Optional[str] = None 
    key_partners: Optional[List[str]] = None
    key_activities: Optional[List[str]] = None
    key_resources: Optional[List[str]] = None
    value_propositions: Optional[Dict[str, str]] = None
    customer_relationships: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    customer_segments: Optional[Dict[str, List[str]]] = None
    cost_structure: Optional[List[str]] = None ###
    revenue_streams: Optional[List[str]] = None
    print("BMC IS RUNNING")

    def update_from_text(self, text: str) -> None:
        print("BMC IS RUNNING")

        try:
            completion = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are an expert in Business Model Canvas (BMC) data extraction. 
                        You will be given unstructured business descriptions and extract relevant information into a structured BMC format.

                        Your goal is to **fill in as many fields as possible** without overwriting existing values.

                        ### **Instructions**
                        1**Analyze the input text carefully.**  
                        - Identify key components such as business goals, customers, revenue sources, partnerships, and technologies.
                        
                        2**Map the extracted information to the correct BMC fields.**  
                        - Example mappings:
                            - **Company Name** → If an organization is mentioned.
                            - **Key Partners** → Any external companies or institutions involved.
                            - **Key Activities** → Core operations mentioned in the text.
                            - **Key Resources** → Technologies, infrastructure, or human resources.
                            - **Value Propositions** → The benefits offered by the product/service.
                            - **Customer Segments** → Who benefits from the product/service?
                            - **Revenue Streams** → Monetization strategies.
                            - **Cost Structure** → Main expenses.

                        3**Preserve existing values**  
                        - Do not overwrite previously filled fields unless explicitly stated.

                        Return the updated Business Model Canvas in **JSON format**.
"""
                    },
                    {"role": "user", "content": text}
                ],
                response_format=BusinessModelCanvas
            )

            new_data = completion.choices[0].message.parsed


            for field, value in new_data.dict().items():
                if value is not None:
                    setattr(self, field, value)
        
        except Exception as e:
            print(f"⚠️ OpenAI API -virhe: {e}")

class BmcValidator(BaseModel):
    print("BMC IS RUNNING")
    accuracy_of_information: bool
    completeness_and_depth: bool
    consistency_in_language: bool
    uniformity_in_detail: bool
    numerical_data_realism: bool
    clarity_and_readability: bool

    def calculate_score(self, validation: 'BmcValidator') -> int:
        """
        Laskee numeerisen pisteytyksen sen perusteella, kuinka moni arvo on False.

        Parameters:
            bmc_validator (BmcValidator): BmcValidator-objekti, joka sisältää arvioinnin tulokset.

        Returns:
            int: Numeerinen pisteytys (0-6), jossa 0 tarkoittaa, että kaikki arvot ovat True ja 6 tarkoittaa, että kaikki arvot ovat False.
        """
        score = 100
        for field, value in validation.model_dump().items():
            if not value:
                score -= round(16.67, 1)
        return score

    def load_ideal_bmc():
        """
        Loads the ideal Business Model Canvas (BMC) from a JSON file.
        this can be used to compare the current BMC with the ideal BMC and other stuff
        It can be accessed trough the self.ideal_bmc_list attribute.
        """
        with open("src/services/business_model_canvas.json") as f:
            ideal_bmc_list = json.load(f)
        return ideal_bmc_list

    def current_vs_ideal_score(self, bmc:json) -> None:
        """
        Päivittää nykyisen BMC-olion uusilla tiedoilla ilman, että aiemmat tiedot ylikirjoitetaan.

        Parameters:
            text (str): Uusi analysoitava syöte.
        """
        try:
            current_bmc = bmc
            ideal_bmc_list = BmcValidator.load_ideal_bmc()
            bmc_comparison = {
                "current_bmc": bmc,
                "ideal_bmc_list": ideal_bmc_list
            }
            bmc_comparison = json.dumps(bmc_comparison, sort_keys=True)
            completion = client.beta.chat.completions.parse(
                model="gpt-4o",
                temperature=0.0,
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are an AI that evaluates Business Model Canvas (BMC) structures.
                        Your task is to compare a provided BMC to multiple high-quality examples 
                        and return a structured evaluation.

                        ### **Evaluation Criteria**
                        **Accuracy of the Information**
                        - Does all provided information logically fit within its respective BMC category?
                        - Are there any misplaced, irrelevant, or nonsensical entries?

                        **Completeness and Depth of Responses**
                        - Are all sections of the BMC filled with the same level of thoroughness as high-quality, real-world examples?
                        - Are some sections overly brief or missing essential details?
                        - **If any section is empty or contains only meaningless characters, set `completeness_and_depth = False`.**

                        **Consistency in Language Use**
                        - Is the entire BMC written in the same language, without mixing different languages?

                        **Uniformity in Detail Level**
                        - Are some parts more vaguely described than others?
                        - Is there inconsistency in how much detail is provided across different sections?

                        **Numerical Data Realism**
                        - If numerical data is included (e.g., market size, revenue streams, costs), do the numbers seem realistic and justifiable based on the business context?
                        - Are there any obvious errors, such as unrealistic growth rates or market sizes?

                        **Clarity and Readability**
                        - Are all sections of the BMC clearly written, avoiding ambiguous or confusing statements?
                        - Would an external reader understand the business model easily?

                        ---

                        ### **Instructions**
                        - **Return `True` if a category is correct or nearly correct.**
                        - **Return `False` if a category fails significantly compared to ideal BMC examples.**
                        - Use the provided JSON object, which contains:
                        - `"current_bmc"` → The user's BMC to evaluate.
                        - `"ideal_bmc_list"` → A list of perfect BMC examples.
                        - Compare each section carefully.
                        - **Return only a JSON object** following the schema below.
                        """
                    },
                    {"role": "user", "content": f"Evaluate this BMC comparison: {json.dumps(bmc_comparison)}"}
                ],
                response_format=BmcValidator
            )
            response = completion.choices[0].message.parsed
            return response

        except Exception as e:
            print(f"⚠️ OpenAI API -virhe: {e}")
        
    

#test the code if you like it :)
if __name__ == "__main__":

    input_bmc = {
    "company_name": "",
    "key_partners": ["Energy utility companies", "Smart home device manufacturers"
        
    ],
    "key_activities": [
    ],
    "key_resources": [
    ],
    "value_propositions": {
        "Businesses": "Optimized energy usage and reduced costs through AI-driven recommendations.",
        "Households": "Personalized energy efficiency suggestions to lower energy bills.",
        "Grid Operators": "Automated balancing of energy supply and demand using AI-powered Virtual Power Plants (VPPs).",
        "Renewable Energy Users": "Maximized revenue from surplus energy through AI-driven aggregation and redistribution."
    },
    "customer_relationships": [
        "Automated AI-driven insights and alerts",
        "Subscription-based energy optimization services",
        "Customer support via AI chatbots and human experts",
        "B2B partnerships with businesses for large-scale energy management"
    ],
    "channels": [
    ],
    "customer_segments": {
        "Residential consumers": [
        ],
        "Business consumers": [
        "Factories and industrial facilities",
        "Large commercial buildings",
        "Retail chains with high energy demand"
        ],
        "Grid operators": [
        "Electricity transmission and distribution companies",
        "Energy market regulators"
        ]
    },
    "cost_structure": [
        "AI model development and maintenance",
        "Cloud computing and data storage costs",
        "Smart grid infrastructure integration",
        "Regulatory compliance and energy market fees",
        "Customer acquisition and support"
    ],
    "revenue_streams": [
        "Subscription fees for AI-powered energy optimization services",
        "Revenue from Virtual Power Plant energy aggregation and redistribution",
        "Partnerships with utility companies and smart home manufacturers",
        "Data monetization from energy consumption analytics",
        "Premium enterprise-level energy management solutions"
    ]
    }

    bmc = BusinessModelCanvas()
    while True:
        text = input("Enter the text: ")
        if text == "exit":
            break
        bmc.update_from_text(text)
        print(bmc.model_dump_json(indent=2))


    #val = BmcValidator(
    #accuracy_of_information=False,
    #completeness_and_depth=False,
    #consistency_in_language=False,
    #uniformity_in_detail=False,
    #numerical_data_realism=False,
    #clarity_and_readability=False
    #)

    #validation = val.current_vs_ideal_score(input_bmc)
    #print(validation)
    #print(val.calculate_score(validation))

