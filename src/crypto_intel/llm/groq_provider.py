from groq import AsyncGroq


class GroqProvider:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant") -> None:
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, system: str = "") -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""
