import json
from openai import AsyncOpenAI
from pydantic import BaseModel
from app.config import settings


class OpenAIService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def structured(self, *, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        response = await self.client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            text_format=schema,
        )
        if response.output_parsed is None:
            raise RuntimeError("Model returned no structured output")
        return response.output_parsed

    async def text(self, *, system: str, user: str) -> str:
        response = await self.client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.output_text
