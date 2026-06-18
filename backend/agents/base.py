from __future__ import annotations

from pydantic import BaseModel, ValidationError

from llm import call_llm


class AgentError(Exception):
    """Raised when an agent cannot produce schema-valid output after retries."""


def call_structured(
    messages: list[dict],
    schema: type[BaseModel],
    model: str = "gpt-4o",
    max_retries: int = 2,
):
    """Call the LLM in JSON mode and parse into `schema`, repairing on failure.

    On a parse/validation error we feed the bad output back and ask for a
    corrected, schema-only response. Raises AgentError if all attempts fail.
    """
    convo = list(messages)
    last_err: Exception | None = None

    for _ in range(max_retries + 1):
        raw = call_llm(convo, model=model, response_format={"type": "json_object"})
        try:
            return schema.model_validate_json(raw)
        except (ValidationError, ValueError) as err:
            last_err = err
            convo = convo + [
                {"role": "assistant", "content": raw or ""},
                {
                    "role": "user",
                    "content": (
                        "Your previous response was not valid JSON for the required "
                        f"schema. Error: {err}. Respond again with ONLY a single JSON "
                        "object matching the schema. No prose, no markdown fences."
                    ),
                },
            ]

    raise AgentError(f"schema validation failed after retries: {last_err}")
