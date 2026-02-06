from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.movies import crud
from app.movies.schemas import MovieCreate
from app.movies.schemas import MovieResponse
from movies.schemas import MovieShortResponse


async def create_new_movie(db: AsyncSession, movie_data: MovieCreate) -> MovieResponse:
    return await crud.create_movie(db, movie_data)

async def list_all_movies(db: AsyncSession, page: int =1)-> List[MovieResponse]:
    limit = 20,
    skip: (page - 1) * limit
    return await crud.get_all_movies(db, skip=skip, limit=limit)

async def get_catalog(
        db: AsyncSession,
        page: int,
        limit: int,
        sort_by: str,
        order: str,
) -> list[MovieShortResponse]:
    skip = (page - 1) * limit
    return await crud.get_movies_catalog(db, skip=skip, limit=limit, sort_by=sort_by, order=order)