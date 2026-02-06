from sqlalchemy import select, desc, asc, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.movies.models import MovieModel, GenreModel, StarModel, DirectorModel, MovieReactionModel, ReactionType
from app.movies.schemas import MovieCreate


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(selectinload(MovieModel.directors),
                 selectinload(MovieModel.genres),
                 selectinload(MovieModel.stars),
                 selectinload(MovieModel.certification)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_movie(db: AsyncSession, movie_data: MovieCreate):
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

async def get_all_movies(db: AsyncSession, skip: int = 0, limit: int = 10):
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

async def get_reaction(db: AsyncSession, movie_id: int, user_id: int):
    stmt = (
        select(MovieReactionModel).where(
            MovieReactionModel.movie_id == movie_id,
            MovieReactionModel.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_reaction(db: AsyncSession, movie_id: int, user_id: int, reaction_type: ReactionType):
    new_reaction = MovieReactionModel(
        user_id=user_id,
        movie_id=movie_id,
        reaction_type=reaction_type
    )
    db.add(new_reaction)
    await db.commit()
    return new_reaction

async def delete_reaction(db: AsyncSession, movie_id: int, user_id: int):
    stmt = delete(MovieReactionModel).where(
        MovieReactionModel.movie_id == movie_id,
        MovieReactionModel.user_id == user_id
    )
    await db.execute(stmt)
    await db.commit()

async def get_reaction_counts(db: AsyncSession, movie_id: int):
    stmt = (
        func.count().filter(MovieReactionModel.reaction_type == ReactionType.LIKE).lable("likes"),
        func.count().filter(MovieReactionModel.reaction_type == ReactionType.DISLIKE).label("dislikes")
    ).where(MovieReactionModel.movie_id == movie_id)
    result = await db.execute(stmt)
    return result.one()