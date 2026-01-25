from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
app = FastAPI(
    lifespan=lifespan,
)

@app.get("/")
async def root():
    return {"message": "Welcome to Online Cinema API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
