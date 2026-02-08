import uuid
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Table,
    Float,
    Date,
    Time,
    Numeric,
    UUID,
    DateTime,
    func,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.database import Base


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("star_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True)
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True)
)



class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship("MovieModel", back_populates="certification")

class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship("MovieModel", secondary=movie_stars, back_populates="stars")

class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship("MovieModel", secondary=movie_genres, back_populates="genres")

class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    movies: Mapped[List["MovieModel"]] = relationship("MovieModel", secondary=movie_directors, back_populates="directors")

class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer)
    duration: Mapped[int] = mapped_column(Integer)
    imdb: Mapped[float] = mapped_column(Float, default=0.0)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    views: Mapped[int] = mapped_column(Integer, default=0)

    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"))
    certification: Mapped["CertificationModel"] = relationship("CertificationModel", back_populates="movies")


    genres: Mapped[List["GenreModel"]] = relationship("GenreModel", secondary=movie_genres, back_populates="movies")
    stars: Mapped[List["StarModel"]] = relationship("StarModel", secondary=movie_stars, back_populates="movies")
    directors: Mapped[List["DirectorModel"]] = relationship("DirectorModel", secondary=movie_directors, back_populates="movies")


class ReactionType(enum.Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"

class MovieReactionModel(Base):
    __tablename__ = "movie_reactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    reaction_type: Mapped[ReactionType] = mapped_column(Enum(ReactionType))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="unique_user_movie_reaction"),
    )


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


    author: Mapped["UserModel"] = relationship("UserModel", lazy="selectin")