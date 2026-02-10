from fastapi import HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from app.movies import crud
from app.movies.schemas import (
    MovieResponse,
    MovieDetailResponse,
    MovieUpdate,
    MovieCreate,
    StarCreate,
    StarUpdate,
    DirectorCreate,
    DirectorUpdate,
    GenreCreate,
    GenreUpdate
)
from app.movies.models import ReactionType, MovieModel

async def list_genres(db: AsyncSession):
    return await crud.get_genres_with_counts(db)

async def create_new_star(db: AsyncSession, star_data: StarCreate):
    return await crud.create_star(db, star_data)

async def update_star(db: AsyncSession, star_id: int, star_update: StarUpdate):
    update_dict = star_update.model_dump(exclude_unset=True)
    star = await crud.update_star(db, star_id, update_dict)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    return star

async def delete_star(db: AsyncSession, star_id: int):
    if not await crud.delete_star(db, star_id):
        raise HTTPException(status_code=404, detail="Star not found")
    return True


async def create_new_director(db: AsyncSession, director_data: DirectorCreate):
    return await crud.create_director(db, director_data)

async def update_director(db: AsyncSession, director_id: int, director_update: DirectorUpdate):
    update_dict = director_update.model_dump(exclude_unset=True)
    director = await crud.update_director(db, director_id, update_dict)
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")
    return director

async def delete_director(db: AsyncSession, director_id: int):
    if not await crud.delete_director(db, director_id):
        raise HTTPException(status_code=404, detail="Director not found")
    return True


async def create_new_genre(db: AsyncSession, genre_data: GenreCreate):
    return await crud.create_genre(db, genre_data)

async def update_genre(db: AsyncSession, genre_id: int, genre_update: GenreUpdate):
    update_dict = genre_update.model_dump(exclude_unset=True)
    genre = await crud.update_genre(db, genre_id, update_dict)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre

async def delete_genre(db: AsyncSession, genre_id: int):
    if not await crud.delete_genre(db, genre_id):
        raise HTTPException(status_code=404, detail="Genre not found")
    return True

async def get_movie(db: AsyncSession, movie_id: int, user_id: int) -> MovieDetailResponse:
    movie = await crud.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    counts = await crud.get_reaction_counts(db, movie_id)
    my_reaction = await crud.get_reaction(db, movie_id, user_id)
    comments = await crud.get_comments_count(db, movie_id)

    movie.avg_rating = movie.imdb
    movie.likes_count = counts.likes
    movie.dislikes_count = counts.dislikes
    movie.my_reaction = my_reaction.reaction_type if my_reaction else None
    movie.comments_count = comments

    return movie

async def create_new_movie(db: AsyncSession, movie_data: MovieCreate) -> MovieResponse:
    return await crud.create_movie(db, movie_data)


async def update_existing_movie(db: AsyncSession, movie_id: int, movie_update: MovieUpdate):
    update_dict = movie_update.model_dump(exclude_unset=True)

    movie = await crud.update_movie(db, movie_id, update_dict)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

async def get_catalog(
        db: AsyncSession,
        page: int,
        limit: int,
        sort_by: str,
        order: str,
        **params,
):
    search = params.pop("search", None)
    genre_ids = params.pop("genre_ids", None)
    star_ids = params.pop("star_ids", None)
    director_ids = params.pop("director_ids", None)

    filters = []

    if search:
        search_filter = f"%{search}%"
        filters.append(or_(
            MovieModel.name.ilike(search_filter),
            MovieModel.description.ilike(search_filter),
        ))
    if params.get("year_from"):
        filters.append(MovieModel.year >= params["year_from"])
    if params.get("year_to"):
        filters.append(MovieModel.year <= params["year_to"])

    if params.get("imdb_min"):
        filters.append(MovieModel.imdb >= params["imdb_min"])
    if params.get("imdb_max"):
        filters.append(MovieModel.imdb <= params["imdb_max"])

    if params.get("price_min"):
        filters.append(MovieModel.price >= params["price_min"])
    if params.get("price_max"):
        filters.append(MovieModel.price <= params["price_max"])

    if params.get("duration_min"):
        filters.append(MovieModel.duration >= params["duration_min"])
    if params.get("duration_max"):
        filters.append(MovieModel.duration <= params["duration_max"])

    if params.get("gross_min"):
        filters.append(MovieModel.gross >= params["gross_min"])

    if params.get("certification_id"):
        filters.append(MovieModel.certification_id == params["certification_id"])

    if params.get("has_metascore") is True:
        filters.append(MovieModel.meta_score.isnot(None))
    elif params.get("has_metascore") is False:
        filters.append(MovieModel.meta_score.is_(None))

    skip = (page - 1) * limit

    return await crud.get_movies_catalog(
        db,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
        filters=filters,
        genre_ids=genre_ids,
        star_ids=star_ids,
        director_ids=director_ids,
        search_query=search
    )

async def delete_movie(db: AsyncSession, movie_id: int):
    deleted = await crud.delete_movie(db, movie_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фільм не знайдено"
        )
    return True

async def handle_reaction(
        db: AsyncSession,
        movie_id: int,
        reaction_type: ReactionType,
        user_id: int
):
    existing = await crud.get_reaction(db, movie_id, user_id)

    if existing:
        if existing.reaction_type == reaction_type:
            await crud.delete_reaction(db, movie_id, user_id)
            return {"message": "Reaction removed"}

        existing.reaction_type = reaction_type
        await db.commit()
        return {"message": "Reaction updated"}

    await crud.create_reaction(db, movie_id, user_id, reaction_type)
    return {"message": "Reaction added"}

async def remove_reaction(db: AsyncSession, user_id: int, movie_id: int):
    await crud.delete_reaction(db, movie_id, user_id)
    return {"status": "Deleted"}

async def get_movie_stats(db: AsyncSession, movie_id: int, user_id: int):
    count = await crud.get_reaction_counts(db, movie_id)
    my_reaction= await crud.get_reaction(db, movie_id, user_id)

    return {
        "likes": count.likes,
        "dislikes": count.dislikes,
        "my_reaction": my_reaction.reaction_type if my_reaction else None
    }

async def add_comment(
        db: AsyncSession,
        movie_id: int,
        user_id: int,
        text: str
):
    movie = await crud.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    comment = await crud.create_comments(db, movie_id, user_id, text)
    await db.refresh(comment, ["author"])
    return comment