import ollama
from config import settings


class LLMAssistant:
    def __init__(self):
        self.model_name = settings.LLM_MODEL

    async def get_response(self, prompt: str) -> str:
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.5,
                    "num_ctx": 4096,
                    "top_k": 40,
                    "top_p": 0.9,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Ошибка: {str(e)}"


# async def send_chat_request(message, model="gpt-4.1-nano"):
#     url = "https://api.hydraai.ru/v1/chat/completions"
#     headers = {"Authorization": f"Bearer {settings.API_KEY_MODEL}"}
#     payload = {
#         "messages": [{"content": message, "role": "user"}],
#         "model": model,
#         "temperature": 0.1,
#         "top_p": 1.0,
#         "repetition_penalty": 1.1,
#         "presence_penalty": 0.0,
#         "frequency_penalty": 0.0,
#         "max_tokens": 4096
#     }

#     async with httpx.AsyncClient() as client:
#         response = await client.post(url, headers=headers, json=payload, timeout=18000)
#         response.raise_for_status()
#         return str(response.json()["choices"][0]["message"]["content"])
