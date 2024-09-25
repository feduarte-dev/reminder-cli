from openai import OpenAI
from openai_prompt import get_instructions


def create_openai_client(key):
    if not key:
        raise ValueError("A variável de ambiente OPENAI_API_KEY não está definida.")

    return OpenAI(api_key=key)


def get_openai_assistant(client, assistant_id):
    return client.beta.assistants.retrieve(assistant_id)


def create_openai_assistant(client):
    # Definindo a ferramenta reminder_builder diretamente ao criar o assistente
    reminder_tool = {
        "type": "function",
        "function": {
            "name": "reminder_builder",
            "description": "Parse reminder messages into a JSON",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Reminder description",
                    },
                    "frequency": {
                        "type": "integer",
                        "description": "Number of times the reminder needs to be repeated.",
                    },
                    "gap": {
                        "type": "string",
                        "description": "Interval in hours between reminders.",
                    },
                    "duration": {
                        "type": "string",
                        "description": "The time until which the reminder remains active (YYYY-MM-DD HH:MM:SS).",
                    },
                },
                "required": ["message", "frequency", "gap"],
            },
        },
    }

    # Criando o assistente com a ferramenta definida
    return client.beta.assistants.create(
        instructions=get_instructions(),
        name="Reminder Assistant",
        tools=[reminder_tool],
        model="gpt-4o-mini",
    )


def create_thread(client, id, phone_number, user_name=""):
    return client.beta.threads.create(
        metadata={
            "user_id": id,
            "user_phone_number": phone_number,
            "user_name": user_name,
        }
    )


def run_thread(client, thread_id, assistant_id):
    return client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=get_instructions(),
    )
