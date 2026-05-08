import asyncio
import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api import auth_routes, contact_routes, health, user_routes
from src.conf.config import origins, settings
from src.conf.constants import API_PREFIX
from src.utils.rate_limiter import limiter
from src.utils.token_cleanup import token_cleanup_loop

app = FastAPI(title="Contacts API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.state.token_cleanup_task = None


@app.on_event("startup")
async def startup_cleanup_worker() -> None:
    app.state.token_cleanup_task = asyncio.create_task(token_cleanup_loop())


@app.on_event("shutdown")
async def shutdown_cleanup_worker() -> None:
    cleanup_task = app.state.token_cleanup_task
    if cleanup_task:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(contact_routes.router, prefix=API_PREFIX)
app.include_router(auth_routes.router, prefix=API_PREFIX)
app.include_router(user_routes.router, prefix=API_PREFIX)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=int(settings.APP_PORT),
        reload=True,
    )

