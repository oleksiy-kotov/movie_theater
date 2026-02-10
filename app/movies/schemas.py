from pydantic import BaseModel, ConfigDict, Field, model_validator

from uuid import UUID
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from app.movies.models import ReactionType


class GenreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class GenreResponse(GenreBase):
    id: int
    movies_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class StarBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class StarCreate(StarBase):
    pass


class StarUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class StarResponse(StarBase):
    id: int
    movies_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class DirectorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class DirectorCreate(DirectorBase):
    pass


class DirectorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class DirectorResponse(DirectorBase):
    id: int
    movies_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class CertificationBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    year: int = Field(..., ge=1888, le=2100)
    duration: int = Field(..., gt=0, description="Тривалість у хвилинах")
    imdb: float = Field(0.0, ge=0, le=10.0)
    description: str
    price: Decimal = Field(..., max_digits=10, decimal_places=2)
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    votes: int = 0

class MovieCreate(MovieBase):
    certification_id: Optional[int] = None
    genre_ids: List[int]
    star_ids: List[int]
    director_ids: List[int]


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    year: Optional[int] = Field(None, ge=1888, le=2100)
    duration: Optional[int] = Field(None, gt=0)
    imdb: Optional[float] = Field(None, ge=0, le=10.0)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    votes: Optional[int] = None

    certification_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None

    model_config = {"from_attributes": True}

class MovieResponse(MovieBase):
    id: int
    uuid: UUID
    certification: CertificationBase
    genres: List[GenreBase]
    stars: List[StarBase]
    directors: List[DirectorBase]

    model_config = ConfigDict(from_attributes=True)

class MovieShortResponse(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    price: Decimal

    model_config = ConfigDict(from_attributes=True)

class MovieDetailResponse(MovieResponse):
    avg_rating: float = 0.0
    likes_count: int = 0
    dislikes_count: int = 0
    comments_count: int = 0

    my_reaction: Optional[ReactionType] = None

    model_config = ConfigDict(from_attributes=True)


class ReactionCreate(BaseModel):
    reaction_type: ReactionType


class ReactionResponse(BaseModel):
    likes: int
    dislikes: int
    my_reaction: Optional[ReactionType] = None

class CommentCreate(BaseModel):
    text: str

class CommentResponse(BaseModel):
    id: int
    text: str
    created_at: datetime
    user_id: int
    user_name: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def map_user_name(cls, data):
        if hasattr(data, "user") and data.user:
            data.user_name = data.user.username
        return data