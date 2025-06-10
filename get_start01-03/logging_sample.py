import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

url = "https://api.keywordsai.co/api/request-logs/create/"
payload = {
    "model": "claude-3-5-sonnet-20240620",
    "prompt_messages": [
        {"role": "user", "content": "Hi"}
    ],
    "completion_message": {
        "role": "assistant",
        "content": "Hi, how can I assist you today?"
    },
    "cost": 0.00042,
    "generation_time": 5.7,
    "ttft": 3.1,
    "customer_params": {
        "customer_identifier": "customer_123",
        "name": "Frank Chen",
        "email": "frank@keywordsai.co"
    }
}

# Get API key from environment variable
api_key = os.getenv("KEYWORDSAI_API_KEY")
if not api_key:
    raise ValueError("KEYWORDSAI_API_KEY environment variable is required")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json=payload)

# Print result
print("Status Code:", response.status_code)
try:
    print("Response:", response.json())
except Exception as e:
    print("Raw Response Text:", response.text)
