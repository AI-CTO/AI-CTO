import json
import re
import uuid

from openai import OpenAI


class IdeaGenerator:
    def __init__(self, client: OpenAI):
        """
        Luokka uusien ideoiden generointiin ja hallintaan OpenAI Assistants API:n avulla.

        :param client: OpenAI API client
        """
        self.client = client
        self.thread_id = None
        self.bmc = {}
        self.assistant_id = self.create_assistant()

    def create_assistant(self):
        """Luo uuden Assistantin OpenAI API:iin."""
        assistant = self.client.beta.assistants.create(
            name="Project Idea Assistant",
            instructions="""You assist the user in refining a business model canvas (BMC).
                            First, ask the user to describe their idea in detail. Then,
                            iteratively guide them through completing the BMC by dynamically adjusting questions based on their inputs. 
                            The user should also be able to ask general questions outside the BMC process.
                            If the user wishes to evaluate, use the data that you have to do so.""",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o",
        )
        return assistant.id

    def create_thread(self):
        """Luo uuden keskustelun OpenAI API:ssa ja tallenna thread_id."""
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
        return self.thread_id

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
            if isinstance(msg.content, list) and len(msg.content) > 0 and "text" in msg.content[0]:
                content_text = msg.content[0]["text"]
            else:
                content_text = str(msg.content)
            conversation_history.append({"role": msg.role, "content": content_text})

        conversation_history.append({"role": "user", "content": "Resume the project discussion."})

        response = self.client.chat.completions.create(
            model="gpt-4o", messages=conversation_history
        )

        ai_response_text = response.choices[0].message.content.strip()
        print("Resumed conversation response: ", ai_response_text)

        return {"success": True, "message": ai_response_text}



    def start_chat(self):
        """Käynnistää interaktiivisen OpenAI-pohjaisen chatin käyttäjän kanssa, jossa täytetään BMC."""
        print("Let's begin filling in the BMC Canvas. Describe your idea in detail.")
        user_message = input("User: ")
        conversation = [
            {
                "role": "system",
                "content": """
                    We are working on a Business Model Canvas (BMC). 
                    Guide the user by asking relevant questions to complete the BMC. 
                    Let the user also ask unrelated questions.
                """,
            },
            {"role": "user", "content": user_message},
        ]

        while True:
            response = self.client.chat.completions.create(
                model="gpt-4o", messages=conversation, max_tokens=500
            )
            assistant_reply = response.choices[0].message.content.strip()
            print(f"\nAssistant: {assistant_reply}")

            user_input = input("User: ")
            if user_input.lower() in ["lopeta", "valmis", "done", "finished"]:
                print("\nBMC creation ends.")
                break

            conversation.append({"role": "assistant", "content": assistant_reply})
            conversation.append({"role": "user", "content": user_input})


if __name__ == "__main__":
    client = OpenAI()
    generator = IdeaGenerator(client)

    start = input("Do you want assistance in a new idea? (Yes/No)")
    if start.lower() == "no":
        print("Shutting down...")
    else:
        generator.create_thread()
        generator.start_chat()
        print("\nFinalised Business Model Canvas saved.")
