import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv(override=True)

print("MODEL:", os.getenv("LITELLM_MODEL"))
print("BASE:", os.getenv("LITELLM_API_BASE"))

response = completion(
    model=os.getenv("LITELLM_MODEL"),
    api_base=os.getenv("LITELLM_API_BASE"),
    api_key=os.getenv("LITELLM_API_KEY"),
    messages=[
        {"role": "user", "content": "Olá! Responda em uma frase curta."}
    ],
)

print(response.choices[0].message.content)
