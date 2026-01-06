import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ===================== TOOLS =====================
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_unread_emails_summary",
            "description": "Get summaries of all unread emails in the inbox",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_last_email_summary",
            "description": "Get summary of the most recent/last unread email",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_unread_email_categories",
            "description": "Get categories for all unread emails",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_emails_from_sender",
            "description": "Check how many unread emails are from a specific sender (e.g., GitHub, Google, LinkedIn)",
            "parameters": {
                "type": "object",
                "properties": {
                    "sender_query": {
                        "type": "string",
                        "description": "Sender name or keyword to search for"
                    }
                },
                "required": ["sender_query"]
            }
        }
    }
]

# ===================== BASIC LLM =====================
def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are an expert email summarizer. Summarize emails concisely in 2-3 sentences, mentioning key points from both the email body and any attachments."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.content.strip()

# ===================== INTELLIGENT HANDLER =====================
def intelligent_command_handler(user_message: str, function_map: dict, history: list = None) -> dict:
    """
    Intelligent command handler using function calling

    ALWAYS returns:
    {
        "reply": str,
        "data": dict | None
    }
    """

    messages = [
        {
            "role": "system",
            "content": """You are InboxAI, a friendly and helpful email assistant. 

When users greet you (hello, hi, hey, etc.), respond warmly and naturally.
When users ask about their emails, use the appropriate function to help them.
Keep responses conversational and natural - don't be robotic.

Examples:
- "hello" → Greet them back warmly
- "what's my last email?" → Use get_last_email_summary
- "show unread emails" → Use get_unread_emails_summary
- If the user asks about categories, labels, types, or classification of emails,
use get_unread_email_categories.
- If the user asks whether they have emails from a specific sender
(e.g., "GitHub", "Google", "LinkedIn", "from X"),
use check_emails_from_sender with the sender name as parameter.
- "summarize my inbox" → Use get_unread_emails_summary"""
        }
    ]

    # Add conversation history if available
    if history:
        messages.extend(history)

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    # -------- First call: decide intent --------
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.7,
        max_tokens=500
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 🟢 NO TOOL CALL → GREETING / CHAT
    if not tool_calls:
        return {
            "reply": response_message.content or "I'm here to help with your emails!",
            "data": None
        }

    # -------- Execute tool (ONLY FIRST TOOL CALL) --------
    tool_call = tool_calls[0]
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments or "{}")

    if function_name not in function_map:
        return {
            "reply": "Sorry, I can't handle that request yet.",
            "data": None
        }

    try:
        if function_args:
            function_result = function_map[function_name](**function_args)
        else:
            function_result = function_map[function_name]()
    except Exception as e:
        return {
            "reply": "Something went wrong while fetching your emails.",
            "data": {"error": str(e)}
        }

    # -------- FORCE STANDARD RESPONSE FORMAT --------
    if isinstance(function_result, dict):
        return {
            "reply": function_result.get("reply", ""),
            "data": function_result.get("data")
        }

    # Fallback safety net
    return {
        "reply": str(function_result),
        "data": None
    }
