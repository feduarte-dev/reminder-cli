from openai import OpenAI
import os
from dotenv import load_dotenv


def get_thread(client, thread_id):
    return client.beta.threads.retrieve(thread_id)


def run_thread(client, thread_id, assistant_id):
    return client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="""
        You are an assistant designed to parse reminder messages into a structured JSON format. I will send you messages containing the details of a reminder, and you need to extract the relevant information and return it as a JSON object. 
        Here's the expected JSON structure for your response:
            {
            "message": "Reminder description",
            "frequency": number_of_repetitions,
            "gap": interval_in_hours,
            "duration": "YYYY-MM-DD HH:MM:SS"
            }
        """,
    )


def create_thread(client, id, phone_number, user_name=""):
    return client.beta.threads.create(
        metadata={
            "user_id": id,
            "user_phone_number": phone_number,
            "user_name": user_name,
        }
    )


def create_openai_client(key):
    if not key:
        raise ValueError("A variável de ambiente OPENAI_API_KEY não está definida.")

    return OpenAI(api_key=key)


def create_openai_assistant(client):
    return client.beta.assistants.create(
        instructions="""
        You are an assistant designed to parse reminder messages into a structured JSON format. I will send you messages containing the details of a reminder, and you need to extract the relevant information and return it as a JSON object. 
        Here's the expected JSON structure for your response:
            {
            "message": "Reminder description",
            "frequency": number_of_repetitions,
            "gap": interval_in_hours,
            "duration": "YYYY-MM-DD HH:MM:SS"
            }
        """,
        name="Reminder Assistant",
        tools=[
            #    Por que nao colocar a tool direta aqui?
        ],
        model="gpt-4o-mini",
    )


def get_openai_assistant(client, assistant_id):
    return client.beta.assistants.retrieve(assistant_id)


def tool_builder(client, assistant_id):
    # Define the reminder_builder tool
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

    # Get current tools of the assistant
    assistant = client.beta.assistants.retrieve(assistant_id)
    current_tools = assistant.tools

    # Check if the tool is already in the tools list
    tool_names = [
        tool["function"]["name"] for tool in current_tools if "function" in tool
    ]
    if "reminder_builder" not in tool_names:
        print("Tool 'reminder_builder' not found. Adding tool...")
        updated_tools = current_tools + [reminder_tool]

        # Update the assistant with the new tool
        client.beta.assistants.update(
            assistant_id=assistant_id,
            tools=updated_tools,
        )
        print("Tool 'reminder_builder' added successfully.")
    else:
        print("Tool 'reminder_builder' already exists.")


def send_message_to_assistant(client, assistant_id, reminder_message):
    thread = create_thread(
        client=client, id="1", phone_number="+55945422672", user_name="Teste Teste"
    )
    run = run_thread(client=client, thread_id=thread.id, assistant_id=assistant_id)
    response = client.beta.threads.runs.submit_tool_outputs_and_poll(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=run.required_action.submit_tool_outputs.tool_calls[0],
    )
    return response


def agent():
    load_dotenv()

    ASSISTANT_ID = os.environ.get("ASSISTANT_ID")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    client = create_openai_client(key=OPENAI_API_KEY)

    if not ASSISTANT_ID:
        assistant = create_openai_assistant(client=client)
        ASSISTANT_ID = assistant.id  # Use a propriedade 'id' para obter o ID
        os.environ["ASSISTANT_ID"] = ASSISTANT_ID  # Atualiza a variável de ambiente
    else:
        assistant = get_openai_assistant(client, ASSISTANT_ID)

    # Check and update tools if necessary
    tool_builder(client=client, assistant_id=ASSISTANT_ID)

    reminder_message = "Remind me to take a break every 2 hours for the next 8 hours."
    result = send_message_to_assistant(client, ASSISTANT_ID, reminder_message)
    print("Assistant response:", result)


if __name__ == "__main__":
    agent()
