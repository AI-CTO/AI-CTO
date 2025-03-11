import os
import json
import fitz
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
prompt_file_path = os.path.join(os.path.dirname(__file__), "../prompt.txt")
with open(prompt_file_path, "r") as file:
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
    
def extract_text_from_pdf(pdf_file):
    try:
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        extracted_text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            extracted_text += text + "\n"

        if not extracted_text.strip():
            return None

        return extracted_text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
