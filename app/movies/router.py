from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.movies.schemas import MovieCreate, MovieResponse
from app.movies import service
from app.auth.dependencies import get_current_admin, get_current_user
from app.database import get_db
from movies.schemas import MovieShortResponse

movie_router = APIRouter(prefix="/movies", tags=["Movies"])

@movie_router.post(
    "/",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Movie creation",
    description="Create a new movie(only moderator/admin)"
)
async def add_movie(
        movie_data: MovieCreate,
        db: AsyncSession = Depends(get_db),
        admin: Depends = Depends(get_current_admin)
) -> MovieResponse:
    return await service.create_new_movie(db, movie_data)

@movie_router.get("/", response_model=list[MovieResponse], status_code=status.HTTP_200_OK, summary="Get all movies")
async def get_movies(db: AsyncSession = Depends(get_db)):
    return await service.list_all_movies(db)

@movie_router.get(
    "/catalog",
    response_model=list[MovieShortResponse],
    status_code=status.HTTP_200_OK,
    summary="Get movies catalog"
)
async def get_movies_catalog(
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=100),
        sort_by: str = Query("date", enum=["price", "year", "rating", "popularity", "date"]),
        order: str = Query("desc", enum=["asc", "desc"]),
        db: AsyncSession = Depends(get_db),
        user = Depends(get_current_user)
):
    return await service.get_catalog(db, page, limit, sort_by, order)