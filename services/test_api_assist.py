import json
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
            instructions="You assist the user in refining a business model canvas (BMC). First, ask the user to describe their idea in detail. Then, iteratively guide them through completing the BMC by dynamically adjusting questions based on their inputs. The user should also be able to ask general questions outside the BMC process.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o",
        )
        return assistant.id

    def create_thread(self):
        """Luo uuden keskustelun OpenAI API:ssa ja tallenna thread_id."""
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
        return self.thread_id

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
