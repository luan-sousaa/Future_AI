import asyncio
from src.services.agent_tool import gerar_pagamento

async def main():
    result = await gerar_pagamento(
        100,
        "TESTUSERxxxxx@testuser.com",
        "Joao",
        "Silva"
    )
    print(result)

asyncio.run(main())