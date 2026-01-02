import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define available tools/functions
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
    }
]

def call_llm(prompt: str) -> str:
    """Simple summarization (keep for backward compatibility)"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You summarize emails into 2–3 natural sentences."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


def intelligent_command_handler(user_message: str, function_map: dict) -> dict:
    """
    Intelligent command handler using function calling
    
    Args:
        user_message: The user's input
        function_map: Dictionary mapping function names to actual Python functions
        
    Returns:
        dict with response data
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
- "summarize my inbox" → Use get_unread_emails_summary"""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # First API call - let Groq decide what to do
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=500,
        temperature=0.7
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # If no function call needed (e.g., just saying hello), return conversational response
    if not tool_calls:
        return {
            "type": "conversation",
            "message": response_message.content
        }
    
    # Execute the function calls
    messages.append(response_message)
    
    function_results = []
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        
        # Call the actual Python function
        if function_name in function_map:
            function_response = function_map[function_name]()
            function_results.append({
                "name": function_name,
                "result": function_response
            })
            
            # Add function response to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response)
            })
    
    # Second API call - let Groq format the response naturally
    final_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    
    final_content = final_response.choices[0].message.content
    
    # Determine response type based on which function was called
    if function_results:
        function_name = function_results[0]["name"]
        function_data = function_results[0]["result"]
        
        if function_name == "get_last_email_summary":
            return {
                "type": "single_email",
                "message": final_content,
                "data": function_data
            }
        elif function_name == "get_unread_emails_summary":
            return {
                "type": "multiple_emails",
                "message": final_content,
                "data": function_data
            }
    
    return {
        "type": "conversation",
        "message": final_content
    }