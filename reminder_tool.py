def get_reminder_tool():
    return {
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
