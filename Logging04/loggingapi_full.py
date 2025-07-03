import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

url = "https://api.keywordsai.co/api/request-logs/create/"
payload = {
    # --- Layer 1: Required fields ---
    "model": "claude-3-5-sonnet-20240620", # model name 
    "prompt_messages": [    # prompt messages
        {
          "role": "user",
          "content": "Hi"
        },
    ],
    "completion_message": { # completion message
        "role": "assistant",
        "content": "Hi, how can I assist you today?" 
    },
    # --- Layer 2: Telemetry ---
    "prompt_tokens": 5, # prompt tokens
    "completion_tokens": 5, # completion tokens
    "cost": 0.000005, # cost
    "latency": 0.2, # latency
    "ttft": 2, # wall-clock time from request to last token
    "generation_time": 0.2, # time to generate the response
    # --- Layer 3: Metadata ---
    "metadata": {
        "language": "en",
    },
    "customer_params": { # customer params
        "customer_identifier": "1234567890",
        "name": "John Doe",
        "email": "john.doe@example.com",
    },
    "group_identifier": "group-001", # group identifier
    "thread_identifier": "thread-001", # thread identifier
    "custom_identifier": "custom-001" # custom identifier
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
