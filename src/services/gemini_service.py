from google import genai
import os

prompt_file_path = os.path.join(os.path.dirname(__file__), "../prompt.txt")
with open(prompt_file_path, "r") as file:
    instruction_prompt = file.read().strip()

def evaluate_with_gemini(evaluation_results, conversation_content):
    print("Beginning Gemini evaluation...") # debugging
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        # Updated prompt to include conversation content
        prompt = (
            f"{instruction_prompt} Evaluate the following project:.\n\n"
            f"Conversation Content:\n{conversation_content}\n\n"
            f"Evaluation Results given by OpenAI:\n{evaluation_results}\n\n"
            "Provide a second opinion based on the above information."
        )

        print(prompt) # debugging

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt]
        )

        print(f"Evaluation results: {evaluation_results}") # debugging
        print(f"Conversation content: {conversation_content}") # debugging
        print("Gemini response:", response.text) # debugging

        return {"gemini_response": response.text}
    except Exception as e:
        return {"error": f"Failed to connect to Gemini API: {str(e)}"}
