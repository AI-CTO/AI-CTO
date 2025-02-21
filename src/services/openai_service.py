import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
with open("prompt.txt", "r") as file:
    instruction_prompt = file.read().strip()


def get_openai_completion(description):
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": instruction_prompt},
            {"role": "user", "content": description},
        ],
        model="gpt-3.5-turbo",
    )
    try:
        response_json = json.loads(response.choices[0].message.content)
        required_fields = [
            "project_name",
            "business_novelty",
            "rationale_behind_business_novelty",
            "customer_novelty",
            "rationale_behind_customer_novelty",
            "impact",
            "rationale_behind_impact",
            "type",
        ]
        if all(field in response_json for field in required_fields):
            return response_json
        else:
            raise ValueError("Response JSON does not contain all required fields.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid response format: {e}")
        return None