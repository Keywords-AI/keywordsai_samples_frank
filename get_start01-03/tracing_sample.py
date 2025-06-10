import os
from openai import OpenAI
from keywordsai_tracing.decorators import workflow, task
from keywordsai_tracing.main import KeywordsAITelemetry
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize telemetry with explicit key and base URL
k_tl = KeywordsAITelemetry()

# Initialize OpenAI client with key from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=openai_api_key)

@task(name="joke_creation")
def create_joke():
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Tell me a joke about opentelemetry"}],
        temperature=0.5,
        max_tokens=100,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )
    return completion.choices[0].message.content.strip()

@task(name="pirate_joke_translation")
def translate_joke_to_pirate(joke: str):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Translate this joke to pirate speak:\n\n{joke}"}
        ],
        temperature=0.5,
    )
    return completion.choices[0].message.content.strip()

@task(name="signature_generation")
def generate_signature(joke: str):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Add a signature to this joke:\n\n{joke}"}
        ],
        temperature=0.5,
    )
    return completion.choices[0].message.content.strip()

@workflow(name="joke_workflow")
def joke_workflow():
    joke = create_joke()
    pirate_joke = translate_joke_to_pirate(joke)
    signed_joke = generate_signature(pirate_joke)
    return signed_joke

if __name__ == "__main__":
    final_result = joke_workflow()
    print("\n=== Final Result ===\n")
    print(final_result)
