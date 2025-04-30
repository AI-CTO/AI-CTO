import json
import os
import re

from openai import OpenAI

# from .BMC_recources import BusinessModelCanvas as BMC

script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
assistant_instructions = os.path.join(
    script_dir, "instructions.txt"
)  # Construct full path
with open(assistant_instructions, "r", encoding="utf-8") as file:
    instructions_content = file.read()


class IdeaGenerator:
    def __init__(self, client: OpenAI):
        """
        Luokka uusien ideoiden generointiin ja hallintaan OpenAI Assistants API:n avulla.
        :param client: OpenAI API client
        """
        self.client = client
        self.thread_id = None
        self.bmc = {}  # Luo tyhjän bmc tietueen
        self.assistant_id = self.get_or_create_assistant()

    def get_or_create_assistant(self):
        """Checks if an assistant exists. If not, creates a new one."""
        assistants = self.client.beta.assistants.list().data  # Get all assistants

        if assistants:
            # Use the first available assistant
            existing_assistant = assistants[0]
            print(
                f"Using existing assistant: {existing_assistant.name} (ID: {existing_assistant.id})"
            )
            return existing_assistant.id

        # If no assistant exists, create a new one

        print("No existing assistant found. Creating a new one...")
        assistant = self.client.beta.assistants.create(
            temperature=0.0,
            name="Project Idea Assistant",
            instructions="""
            RULE: RETURN ONLY A JSON OBJECT.
                           You assist the user in refining a business model canvas (BMC).
                           First, ask the user to describe their idea in detail. Then,
                           iteratively guide them through completing the BMC by dynamically adjusting questions based on their inputs.
                           The user should also be able to ask general questions outside the BMC process.
                           If the user wishes to evaluate, use the data that you have to do so.
                           You will have two kinds of outputs for me. Imagine your answer to the user is in the variable "assistant_response"
                           And now you have more instructions:
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
                          **Return ONLY a JSON object structured as follows, without extra text**:
                          RULE: RETURN ONLY A JSON OBJECT. 
                            - The JSON object should contain the following fields:
                           ```json  
                       {
                          "company_name": null,
                           "assistant_response": assistant_response,
                           "key_partners": <extracted info here, null of not provided>,
                           "key_activities": <extracted info here, null of not provided>,
                           "key_resources": <extracted info here, null of not provided>,
                           "value_propositions": <extracted info here, null of not provided>,
                           "customer_relationships": <extracted info here, null of not provided>,
                           "channels": <extracted info here, null of not provided>,
                           "customer_segments": <extracted info here, null of not provided>,
                           "cost_structure": <extracted info here, null of not provided>,
                           "revenue_streams": <extracted info here, null of not provided>
                       }
                           ```
""",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o",
        )
        return assistant.id

    def create_thread(self):
        """Luo uuden keskustelun OpenAI API:ssa ja tallenna thread_id."""
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
        return self.thread_id

    def extract_json_from_response(self, response):
        """
        Extracts and parses JSON data from the assistant's response string.

        :param response: The string response from the assistant containing JSON data.
        :return: A parsed dictionary containing the extracted JSON data.
        """
        try:
            print(
                "Attempting to extract JSON from:", response[:100] + "..."
            )  # Print first 100 chars

            match = re.search(r"```json\s*([\s\S]+?)\s*```", response)
            if match:
                json_data = match.group(1).strip()
                parsed_data = json.loads(json_data)
                return parsed_data
            else:
                # If no JSON block found, try to extract any valid JSON from the response
                # Look for anything that might be JSON (between curly braces)
                json_match = re.search(r"\{[\s\S]*?\}", response)
                if json_match:
                    try:
                        possible_json = json_match.group(0)
                        parsed_data = json.loads(possible_json)
                        return parsed_data
                    except json.JSONDecodeError:
                        pass

                # If all else fails, return the response as an assistant_response
                print("No valid JSON block found, returning response as text")
                return {"assistant_response": response}

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            return {"assistant_response": response, "error": "Invalid JSON format"}

    def evaluate(self):
        """Asks the AI to evaluate the project based on user discussions and updates the evaluation table."""
        if not self.thread_id:
            print("No active thread found. Start a conversation first.")
            return

        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)

        conversation_history = []
        for msg in messages.data:
            if (
                isinstance(msg.content, list)
                and len(msg.content) > 0
                and "text" in msg.content[0]
            ):
                content_text = msg.content[0]["text"]
            else:
                content_text = str(msg.content)

            conversation_history.append({"role": msg.role, "content": content_text})

        eval_prompt = """
        Based on the discussion so far, evaluate the business idea using the following metrics:
        - **Customer Novelty (x_value)**: How new and unique is this idea to potential customers? (1-100 scale)
        - **Business Novelty (y_value)**: How innovative is this from a business perspective? (1-100 scale)
        - **Business Impact (impact)**: Rate the overall business potential on a scale of 1-10.
        - **Project Name**: Provide a short, clear name for the idea.

        Return your response as a JSON object like this:
        ```json
        {
            "x_value": 75,
            "y_value": 85,
            "impact": 8,
            "name": "AI-Powered Smart Assistant"
        }
        ```
        """

        conversation_history.append({"role": "user", "content": eval_prompt})

        response = self.client.chat.completions.create(
            model="gpt-4o", messages=conversation_history
        )

        print("Full API response: ", response)

        try:
            ai_response_text = response.choices[0].message.content.strip()

            match = re.search(r"```json\s*([\s\S]+?)\s*```", ai_response_text)
            if match:
                ai_response_text = match.group(1)

            evaluation_result = json.loads(ai_response_text)

            if not all(
                key in evaluation_result
                for key in ["x_value", "y_value", "impact", "name"]
            ):
                print("Error: Missing expected keys in AI response.")
                return {"error": "Invalid response format"}

            self.bmc[self.thread_id] = evaluation_result

            print(f"\nEvaluation Completed for {evaluation_result['name']}")
            print(f"Customer Novelty: {evaluation_result['x_value']}")
            print(f"Business Novelty: {evaluation_result['y_value']}")
            print(f"Business Impact: {evaluation_result['impact']}")

            return evaluation_result

        except json.JSONDecodeError as e:
            print(f"Error: Could not parse AI response. {str(e)}")
            return {"error": "Invalid response format"}

    def resume_conversation(self):
        """Resumes the conversation based on the thread_id."""
        if not self.thread_id:
            print("No active thread found. Start a conversation first.")
            return {"error": "No active thread to resume."}

        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)

        conversation_history = []
        for msg in messages.data:
            if (
                isinstance(msg.content, list)
                and len(msg.content) > 0
                and "text" in msg.content[0]
            ):
                content_text = msg.content[0]["text"]
            else:
                content_text = str(msg.content)
            conversation_history.append({"role": msg.role, "content": content_text})

        conversation_history.append(
            {"role": "user", "content": "Resume the project discussion."}
        )

        response = self.client.chat.completions.create(
            model="gpt-4o", messages=conversation_history
        )

        ai_response_text = response.choices[0].message.content.strip()
        print("Resumed conversation response: ", ai_response_text)

        return {"success": True, "message": ai_response_text}
