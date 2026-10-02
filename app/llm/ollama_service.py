import json
from typing import Any

from pydantic import BaseModel


class OllamaLLM:
    """Small adapter around Ollama. The LLM proposes; validators decide."""

    def __init__(self, model: str = "qwen2.5:7b", host: str | None = None):
        try:
            import ollama
        except ImportError as exc:
            raise RuntimeError("Install the Ollama Python package with: pip install ollama") from exc
        self._ollama = ollama.Client(host=host) if host else ollama
        self.model = model

    def json(self, system: str, prompt: str, schema: type[BaseModel] | None = None) -> dict[str, Any]:
        response = self._ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            format="json",
            options={"temperature": 0},
        )
        content = response["message"]["content"]
        data = json.loads(content)
        if schema is not None:
            return schema.model_validate(data).model_dump()
        return data
