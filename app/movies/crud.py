from typing import List

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.movies.models import MovieModel, GenreModel, StarModel, DirectorModel
from app.movies.schemas import MovieCreate, MovieResponse


async def create_movie(db: AsyncSession, movie_data: MovieCreate) -> MovieResponse:
    data = movie_data.model_dump(exclude={"genres_ids", "director_ids", "star_ids"})
    new_movie = MovieModel(**data)

    if movie_data.genre_ids:
        genres = await db.execute(select(GenreModel).where(GenreModel.id.in_(movie_data.genre_ids)))
        new_movie.genres = genres.scalar().all()

    if movie_data.star_ids:
        stars = await db.execute(select(StarModel).where(StarModel.id.in_(movie_data.star_ids)))
        new_movie.stars = stars.scalars().all()

    if movie_data.director_ids:
        directors = await db.execute(select(DirectorModel).where(DirectorModel.id.in_(movie_data.director_ids)))
        new_movie.directors = directors.scalars().all()

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie

async def get_all_movies(db: AsyncSession, skip: int = 0, limit: int = 10) -> List[MovieResponse]:
    result = await db.execute(select(MovieModel).options(
        selectinload(MovieModel.directors),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.stars),
        selectinload(MovieModel.certification)
    )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_movies_catalog(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        sort_by = str,
        order = str,
):
    sort_map = {
        "price": MovieModel.price,
        "year": MovieModel.year,
        "rating": MovieModel.imdb,
        "popularity": MovieModel.views,
        "date": MovieModel.id,
    }
    column = sort_map.get(sort_by, MovieModel.id)
    sort_func = desc(column) if order == "desc" else asc(column)
    stmt = select(MovieModel).order_by(sort_func).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()