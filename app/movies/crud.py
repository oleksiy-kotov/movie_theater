from fastapi import HTTPException
from sqlalchemy import select, desc, asc, delete, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.movies.models import (
    MovieModel,
    GenreModel,
    StarModel,
    DirectorModel,
    MovieReactionModel,
    ReactionType,
    CommentModel
)
from app.movies.schemas import MovieCreate, GenreCreate, StarCreate, DirectorCreate
from app.cart.models import CartItemModel


async def get_genres_with_counts(db: AsyncSession):
    stmt = (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(MovieModel.id).label("movies_count")
        )
        .outerjoin(GenreModel.movies)
        .group_by(GenreModel.id)
        .order_by(GenreModel.name)
    )
    result = await db.execute(stmt)
    return result.all()

async def create_genre(db: AsyncSession, genre_data: GenreCreate):
    new_genre = GenreModel(**genre_data.model_dump())
    db.add(new_genre)
    await db.commit()
    await db.refresh(new_genre)
    return new_genre

async def update_genre(db: AsyncSession, genre_id: int, update_data: dict):
    result = await db.execute(select(GenreModel).where(GenreModel.id == genre_id))
    genre = result.scalar_one_or_none()
    if genre:
        for key, value in update_data.items():
            setattr(genre, key, value)
        await db.commit()
        await db.refresh(genre)
    return genre

async def delete_genre(db: AsyncSession, genre_id: int):
    stmt = delete(GenreModel).where(GenreModel.id == genre_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def create_star(db: AsyncSession, star_data: StarCreate):
    new_star = StarModel(**star_data.model_dump())
    db.add(new_star)
    await db.commit()
    await db.refresh(new_star)
    return new_star

async def update_star(db: AsyncSession, star_id: int, update_data: dict):
    result = await db.execute(select(StarModel).where(StarModel.id == star_id))
    star = result.scalar_one_or_none()
    if star:
        for key, value in update_data.items():
            setattr(star, key, value)
        await db.commit()
        await db.refresh(star)
    return star

async def delete_star(db: AsyncSession, star_id: int):
    stmt = delete(StarModel).where(StarModel.id == star_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def create_director(db: AsyncSession, director_data: DirectorCreate):
    new_director = DirectorModel(**director_data.model_dump())
    db.add(new_director)
    await db.commit()
    await db.refresh(new_director)
    return new_director

async def update_director(db: AsyncSession, director_id: int, update_data: dict):
    result = await db.execute(select(DirectorModel).where(DirectorModel.id == director_id))
    director = result.scalar_one_or_none()
    if director:
        for key, value in update_data.items():
            setattr(director, key, value)
        await db.commit()
        await db.refresh(director)
    return director

async def delete_director(db: AsyncSession, director_id: int):
    stmt = delete(DirectorModel).where(DirectorModel.id == director_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

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
    data = movie_data.model_dump(exclude={"genre_ids", "director_ids", "star_ids"})
    new_movie = MovieModel(**data)

    if movie_data.genre_ids:
        genres = await db.execute(select(GenreModel).where(GenreModel.id.in_(movie_data.genre_ids)))
        new_movie.genres = genres.scalars().all()

    if movie_data.star_ids:
        stars = await db.execute(select(StarModel).where(StarModel.id.in_(movie_data.star_ids)))
        new_movie.stars = stars.scalars().all()

    if movie_data.director_ids:
        directors = await db.execute(select(DirectorModel).where(DirectorModel.id.in_(movie_data.director_ids)))
        new_movie.directors = directors.scalars().all()

    db.add(new_movie)
    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.certification)
        )
        .where(MovieModel.id == new_movie.id)
    )
    return result.scalar_one()


async def update_movie(db: AsyncSession, movie_id: int, update_data: dict):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        return None

    m2m_map = {
        "genre_ids": (GenreModel, "genres"),
        "star_ids": (StarModel, "stars"),
        "director_ids": (DirectorModel, "directors"),
    }

    for key, value in update_data.items():
        if key in m2m_map:
            model, relation_name = m2m_map[key]
            if value is not None:
                stmt = select(model).where(model.id.in_(value))
                result = await db.execute(stmt)
                new_items = result.scalars().all()
                setattr(movie, relation_name, new_items)
        else:
            setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)
    return movie

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
        sort_by: str = "date",
        order:str = "desc",
        filters: list = None,
        genre_ids: list[int] = None,
        star_ids: list[int] = None,
        director_ids: list[int] = None,
        search_query: str = None
):
    stmt = select(MovieModel)

    if search_query:
        stmt = stmt.outerjoin(MovieModel.stars).outerjoin(MovieModel.directors)

        search_pattern = f"%{search_query}%"
        stmt = stmt.where(or_(
            MovieModel.name.ilike(search_pattern),
            MovieModel.description.ilike(search_pattern),
            StarModel.name.ilike(search_pattern),
            DirectorModel.name.ilike(search_pattern)
        ))

    if genre_ids:
        stmt = stmt.join(MovieModel.genres).where(GenreModel.id.in_(genre_ids))

    if star_ids:
        stmt = stmt.join(MovieModel.stars).where(StarModel.id.in_(star_ids))

    if director_ids:
        stmt = stmt.join(MovieModel.directors).where(DirectorModel.id.in_(director_ids))

    if filters:
        stmt = stmt.where(*filters)

    if genre_ids or star_ids or director_ids:
        stmt = stmt.distinct()

    sort_map = {
        "price": MovieModel.price,
        "year": MovieModel.year,
        "rating": MovieModel.imdb,
        "popularity": MovieModel.views,
        "date": MovieModel.id,
    }
    column = sort_map.get(sort_by, MovieModel.id)
    sort_func = desc(column) if order == "desc" else asc(column)

    stmt = stmt.order_by(sort_func).offset(skip).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_movie(db: AsyncSession, movie_id: int) -> bool:
    in_carts_query = await db.execute(
        select(CartItemModel).where(CartItemModel.movie_id == movie_id).limit(1)
    )
    if in_carts_query.scalar():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete movie"
        )

    stmt = delete(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0

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
    stmt = select(
        func.count().filter(MovieReactionModel.reaction_type == ReactionType.LIKE).label("likes"),
        func.count().filter(MovieReactionModel.reaction_type == ReactionType.DISLIKE).label("dislikes")
    ).where(MovieReactionModel.movie_id == movie_id)
    result = await db.execute(stmt)
    return result.one()

async def create_comments(db: AsyncSession, movie_id: int, user_id: int, text: str):
    new_comment = CommentModel(user_id=user_id, movie_id=movie_id, text=text)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment

async def get_comments_count(db: AsyncSession, movie_id: int) -> int:
    stmt = select(func.count(CommentModel.id)).where(CommentModel.movie_id == movie_id)

    result = await db.execute(stmt)
    return result.scalar() or 0
