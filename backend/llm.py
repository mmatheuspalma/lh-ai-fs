import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(
    messages: list[dict],
    model: str = "gpt-4o",
    temperature: float = 0,
    response_format: dict | None = None,
) -> str:
    """Call the OpenAI API and return the response content."""
    kwargs: dict = {"model": model, "messages": messages, "temperature": temperature}
    if response_format is not None:
        kwargs["response_format"] = response_format
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content
