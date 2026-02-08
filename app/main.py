from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.auth.router import auth_router
from app.movies.router import movie_router
from app.cart.router import cart_router

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

app.include_router(auth_router)
app.include_router(movie_router)
app.include_router(cart_router)
