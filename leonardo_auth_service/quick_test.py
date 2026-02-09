import asyncio

import httpx
from loguru import logger

API_URL = "http://localhost:8000/auth/login"

async def quick_test() -> None:
    """Simple test with dummy credentials to see browser behavior."""
    logger.info("🧪 Running quick stealth test...")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(API_URL, json={
                "strategy": "email",
                "email": "test@example.com",
                "password": "dummy123"
            })

            logger.info(f"Status code: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Response: {response.text}")
            else:
                logger.success("✅ Request completed!")

        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
