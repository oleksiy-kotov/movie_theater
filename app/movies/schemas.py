from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from decimal import Decimal
from typing import List, Optional


class GenreBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class StarBase(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class DirectorBase(BaseModel):
    id: int
    name: str
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
    certification_id: int
    genre_ids: List[int]
    star_ids: List[int]
    director_ids: List[int]

class MovieResponse(MovieBase):
    id: int
    uuid: UUID
    certification: CertificationBase
    genres: List[GenreBase]
    stars: List[StarBase]
    directors: List[DirectorBase]

    model_config = ConfigDict(from_attributes=True)