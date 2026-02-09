import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

# Fix for Windows: Use SelectorEventLoop instead of ProactorEventLoop
# to support subprocess operations required by Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.auth.email_login import EmailLoginStrategy
from src.config.settings import settings
from src.core.browser import browser_factory
from src.core.profile_manager import profile_manager

# Setup file logging
logger.add("server.log", rotation="10 MB", level="DEBUG", backtrace=True, diagnose=True)


# --- Pydantic Models ---
class LoginRequest(BaseModel):
    strategy: str = "email"  # email, google, microsoft
    email: str | None = None
    password: str | None = None
    use_existing_profile: bool = False  # If True, tries to load existing profile first


class LoginResponse(BaseModel):
    status: str
    cookies: dict[str, Any]
    email: str


# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("📡 Service Starting...")
    await browser_factory.start()
    yield
    # Shutdown
    logger.info("🔌 Service Shutting Down...")
    await browser_factory.stop()


# --- App Definition ---
app = FastAPI(title="Leonardo.ai Auth Service", version="1.0.0", lifespan=lifespan)


# --- Endpoints ---
@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "leonardo-auth"}


@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Orchestrates the login process using the requested strategy.
    """
    logger.info(f"🔑 Login request received for strategy: {request.strategy}")

    # Strategy Factory (Simple version)
    if request.strategy == "email":
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="Email and password required for email strategy")
        provider = EmailLoginStrategy()
    else:
        raise HTTPException(status_code=400, detail=f"Strategy '{request.strategy}' not implemented yet.")

    # Profile name based on email (sanitized)
    # We asserted request.email is truthy above
    assert request.email is not None
    profile_name = request.email.replace("@", "_at_").replace(".", "_")

    # Try to load existing profile if requested
    storage_state = None
    if request.use_existing_profile:
        storage_state = profile_manager.load_profile(profile_name)
        if storage_state:
            logger.info(f"♻️ Reusing existing profile for {request.email}")

    # Create Context (with or without saved profile)
    context = await browser_factory.create_context()
    if storage_state:
        # Close the fresh context and create one with saved state
        await context.close()
        # casting storage_state to generic dict/any for playwright compatibility if needed,
        # though playwright expects specific structure.
        # Mypy might complain if storage_state is Optional[Dict], checking validity.
        if not browser_factory.browser:
            await browser_factory.start()
        # We know browser is set now
        assert browser_factory.browser is not None
        context = await browser_factory.browser.new_context(storage_state=storage_state)

    page = await context.new_page()

    try:
        credentials = {"email": request.email, "password": request.password}
        session_data = await provider.login(page, credentials)

        # Save profile for future reuse
        storage = await context.storage_state()
        profile_manager.save_profile(profile_name, storage)

        # Validate session data
        cookies = session_data.get("cookies", {})
        email_resp = session_data.get("email")

        if not email_resp or not isinstance(email_resp, str):
            email_resp = request.email

        return LoginResponse(status="success", cookies={"raw": cookies}, email=email_resp)

    except Exception as e:
        logger.exception("❌ Login process failed")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup context (closes page)
        await context.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
