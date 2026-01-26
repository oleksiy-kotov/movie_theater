from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Application is starting up...")

    yield

    # Shutdown
    print("Application is shutting down...")
app = FastAPI(
    lifespan=lifespan,
)

app.include_router(users.router, prefix="/accounts", tags=["Accounts"])
