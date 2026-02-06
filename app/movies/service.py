from fastapi import HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.movies import crud
from app.movies.schemas import MovieCreate
from app.movies.schemas import MovieResponse
from movies.models import ReactionType
from movies.schemas import MovieShortResponse, MovieDetailResponse


async def get_movie(db: AsyncSession, movie_id: int, user_id: int) -> MovieDetailResponse:
    movie = await crud.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    counts = await crud.get_reaction_counts(db, movie_id)
    my_reaction = await crud.get_reaction(db, movie_id, user_id)

    movie.avg_rating = movie.imdb,
    movie.likes_count = counts.likes,
    movie.dislikes_count = counts.dislikes,
    movie.my_reaction = my_reaction.reaction_type if my_reaction else None
    movie.comments_count = 0

    return movie

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

async def handle_reaction(
        db: AsyncSession,
        movie_id: int,
        reaction_type: ReactionType,
        user_id: int
):
    existing = await crud.get_reaction(db, movie_id, user_id)
    if existing:
        if existing.reaction_type == reaction_type:
            return {"message": "Reaction already exists"}
        existing.reaction_type = reaction_type
        await db.commit()
        return {"message": "Reaction updated"}
    await crud.create_reaction(db, movie_id, reaction_type)
    return {"message": "Reaction added"}

async def remove_reaction(db: AsyncSession, user_id: int, movie_id: int, reaction_type: ReactionType):
    await crud.delete_reaction(db, movie_id, reaction_type)
    return {"status": "Deleted"}

async def get_movie_stats(db: AsyncSession, movie_id: int, user_id: int):
    count = await crud.get_reaction_counts(db, movie_id)
    my_reaction= await crud.get_reaction(db, movie_id, user_id)

    return {
        "likes": count.likes,
        "dislikes": count.dislikes,
        "my_reaction": my_reaction.reaction_type if my_reaction else None
    }