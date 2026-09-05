"""Small direct-SDK app used as source for the v0b delivery smoke test.

The smoke harness edits this application but never executes it.
"""
from anthropic import Anthropic


def main() -> None:
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=32,
        messages=[{"role": "user", "content": "Reply with the word ready."}],
    )
    print(response.content[0].text)


if __name__ == "__main__":
    main()
