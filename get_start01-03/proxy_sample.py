import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def demo_call(input, 
              model="gpt-4o-mini",
              token=None
              ):
    # Use provided token or get from environment
    if token is None:
        token = os.getenv("KEYWORDSAI_API_KEY")
        if not token:
            raise ValueError("KEYWORDSAI_API_KEY environment variable is required")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': input}],
    }

    response = requests.post('https://api.keywordsai.co/api/chat/completions', headers=headers, json=data)
    return response

messages = "Say 'Hello World'"
print(demo_call(messages).json())