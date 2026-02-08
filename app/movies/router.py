from fastapi import APIRouter, Depends, status, Query, HTTPException
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.movies.schemas import (
    MovieCreate,
    MovieResponse,
    MovieShortResponse,
    MovieDetailResponse,
    ReactionCreate,
    ReactionResponse,
    CommentCreate,
    CommentResponse,
    GenreBase,
    MovieUpdate,
    GenreUpdate,
    GenreResponse,
    GenreCreate,
    StarResponse,
    StarCreate,
    StarUpdate,
    DirectorUpdate,
    DirectorCreate,
    DirectorResponse,
)
from app.movies import service
from app.auth.dependencies import get_current_admin, get_current_user
from app.database import get_db
from app.movies import crud

movie_router = APIRouter(prefix="/movies", tags=["Movies"])

@movie_router.get(
    "/genres",
    response_model=list[GenreBase],
    summary="Get all genres with movie counts"
)
async def get_genres(db: AsyncSession = Depends(get_db)):
    return await service.list_genres(db)

@movie_router.post(
    "/genres",
    response_model=GenreResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin | Genres"])
async def add_genre(
        data: GenreCreate,
        db: AsyncSession = Depends(get_db),
        admin = Depends(get_current_admin)):
    return await crud.create_genre(db, data)

@movie_router.patch(
    "/genres/{genre_id}",
    response_model=GenreResponse,
    tags=["Admin | Genres"])
async def edit_genre(
        genre_id: int,
        data: GenreUpdate,
        db: AsyncSession = Depends(get_db),
        admin = Depends(get_current_admin)):
    update_dict = data.model_dump(exclude_unset=True)
    genre = await crud.update_genre(db, genre_id, update_dict)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre

@movie_router.delete(
    "/genres/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin | Genres"])
async def remove_genre(
        genre_id: int,
        db: AsyncSession = Depends(get_db),
        admin = Depends(get_current_admin)):
    if not await crud.delete_genre(db, genre_id):
        raise HTTPException(status_code=404, detail="Genre not found")


@movie_router.post(
    "/stars",
    response_model=StarResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin | Stars"])
async def add_star(
        data: StarCreate,
        db: AsyncSession = Depends(get_db),
        admin = Depends(get_current_admin)):
    return await crud.create_star(db, data)

@movie_router.patch(
    "/stars/{star_id}",
    response_model=StarResponse,
    tags=["Admin | Stars"])
async def edit_star(
        star_id: int,
        data: StarUpdate,
        db: AsyncSession = Depends(get_db),
        admin = Depends(get_current_admin)):
    update_dict = data.model_dump(exclude_unset=True)
    star = await crud.update_star(db, star_id, update_dict)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    return star

@movie_router.delete(
    "/stars/{star_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete star (Admin only)",
    tags=["Admin | Stars"]
)
async def remove_star(
    star_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    if not await crud.delete_star(db, star_id):
        raise HTTPException(status_code=404, detail="Star not found")
    return None

@movie_router.post(
    "/directors",
    response_model=DirectorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin | Directors"])
async def add_director(
        data: DirectorCreate,
        db: AsyncSession = Depends(get_db),
        admin = Depends(get_current_admin)):
    return await crud.create_director(db, data)

@movie_router.patch(
    "/directors/{director_id}",
    response_model=DirectorResponse,
    tags=["Admin | Directors"])
async def edit_director(
        director_id: int,
        data: DirectorUpdate,
        db: AsyncSession = Depends(get_db),
        admin = Depends(get_current_admin)):
    update_dict = data.model_dump(exclude_unset=True)
    director = await crud.update_director(db, director_id, update_dict)
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")
    return director

@movie_router.delete(
    "/directors/{director_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete director (Admin only)",
    tags=["Admin | Directors"]
)
async def remove_director(
    director_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    if not await crud.delete_director(db, director_id):
        raise HTTPException(status_code=404, detail="Director not found")
    return None

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

        search: str = Query(None, description="Search by title, description, actors, or directors"),

        genre_ids: list[int] = Query(None, description="Filter by genre IDs"),
        star_ids: list[int] = Query(None, description="Filter by actor IDs"),
        director_ids: list[int] = Query(None, description="Filter by director IDs"),

        year_from: int = Query(None, ge=1888),
        year_to: int = Query(None),
        imdb_min: float = Query(None, ge=0, le=10),
        imdb_max: float = Query(None, ge=0, le=10),
        price_min: Decimal = Query(None, ge=0),
        price_max: Decimal = Query(None, ge=0),
        duration_min: int = Query(None, ge=0, description="Duration in minutes"),
        duration_max: int = Query(None, ge=0),

        certification_id: int = Query(None),
        has_metascore: bool = Query(None, description="True: has score, False: no score"),

        db: AsyncSession = Depends(get_db),
        user = Depends(get_current_user)
):
    return await service.get_catalog(
        db=db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
        search=search,
        genre_ids=genre_ids,
        star_ids=star_ids,
        director_ids=director_ids,
        year_from=year_from,
        year_to=year_to,
        imdb_min=imdb_min,
        imdb_max=imdb_max,
        price_min=price_min,
        price_max=price_max,
        duration_min=duration_min,
        duration_max=duration_max,
        certification_id=certification_id,
        has_metascore=has_metascore
    )

@movie_router.get(
    "/{movie_id}",
    response_model=MovieDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Movie detail view",
)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    return await service.get_movie(db, movie_id, user.id)
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
        admin = Depends(get_current_admin)
) -> MovieResponse:
    return await service.create_new_movie(db, movie_data)

@movie_router.patch(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Update movie (Admin only)"
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    return await service.update_existing_movie(db, movie_id, movie_data)

@movie_router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete this film (Admin only)"
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    await service.delete_movie(db, movie_id)
    return None # FastAPI автоматично поверне 204

@movie_router.post("/{movie_id}/reaction")
async def add_reaction(
        movie_id: int,
        reaction_data: ReactionCreate,
        db: AsyncSession = Depends(get_db),
        user = Depends(get_current_user)
):
    return await service.handle_reaction(
        db, movie_id, reaction_data.reaction_type, user.id
    )

@movie_router.get(
    "/{movie_id}/reactions",
    response_model=ReactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all reactions"
)
async def get_reactions(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
        user = Depends(get_current_user)
):
    return await service.get_movie_stats(db, movie_id, user.id)

@movie_router.post(
    "/{movie_id}/comments",
    response_model=CommentResponse,
)
async def post_comment(
        movie_id: int,
        comment_data: CommentCreate,
        db: AsyncSession = Depends(get_db),
        user = Depends(get_current_user)
) -> CommentResponse:
    comment = await service.add_comment(db, movie_id, user.id, comment_data.text)
    return comment