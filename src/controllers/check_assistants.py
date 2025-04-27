"""
Module for managing OpenAI assistants.
Connects to OpenAI using API key loaded from environment variables.
"""
import os

import dotenv
import openai

dotenv.load_dotenv()

api = os.getenv("OPENAI_API_KEY")


client = openai.OpenAI(api_key=api)


def delete_all_assistants():
    """Deletes all assistants from OpenAI API."""

    has_more = True
    while has_more:
        assistants = client.beta.assistants.list()

        if not assistants.data:
            print("No assistants found.")
            break

        print(f"Found {len(assistants.data)} assistants. Deleting them now...")

        for assistant in assistants.data:
            assistant_id = assistant.id
            client.beta.assistants.delete(assistant_id)
            print(f"Deleted Assistant ID: {assistant_id}, Name: {assistant.name}")

        has_more = len(assistants.data) > 0  # Keep deleting if more exist

    print("✅ All assistants deleted successfully!")


def list_assistants():
    """Lists all assistants from OpenAI API."""
    assistants = client.beta.assistants.list()

    print(f"Total Assistants: {len(assistants.data)}")
    for assistant in assistants.data:
        print(
            f"ID: {assistant.id}, Name: {assistant.name}, Created: {assistant.created_at}"
        )


if __name__ == "__main__":
    list_assistants()  # Show existing assistants
    delete_all_assistants()  # Delete them
    print("\nVerifying deletion...")
    list_assistants()  # Check again
