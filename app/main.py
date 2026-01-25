from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSession() as session:
        yield session
app = FastAPI(
    lifespan=lifespan,
)

@app.get("/")
async def root():
    return {"message": "Welcome to Online Cinema API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
