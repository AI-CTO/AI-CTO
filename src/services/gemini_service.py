from google import genai
import os

def evaluate_with_gemini(thread_id, bmc_canvas, evaluation_results, project_details, conversation_content):
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        # Updated prompt to include conversation content
        prompt = (
            f"Evaluate the project:.\n\n"
            f"Project Details:\n{project_details}\n\n"
            f"BMC Canvas:\n{bmc_canvas}\n\n"
            f"Evaluation Results:\n{evaluation_results}\n\n"
            f"Conversation Content:\n{conversation_content}\n\n"
            "Provide a second opinion based on the above information."
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt]
        )
        print(f"Project details: {project_details}") # debugging
        print(f"BMC canvas: {bmc_canvas}") # debugging
        print(f"Evaluation results: {evaluation_results}") # debugging
        print(f"Conversation content: {conversation_content}") # debugging
        print("Gemini response:", response.text) # debugging

        return {"gemini_response": response.text}
    except Exception as e:
        return {"error": f"Failed to connect to Gemini API: {str(e)}"}
