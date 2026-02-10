from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.movies.models import MovieModel

bought_movies_table = Table(
    "user_bought_movies",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
)

class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )

    user = relationship("UserModel", back_populates="cart")
    items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE")
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE")
    )

    added_at: Mapped[datetime] = mapped_column(default=datetime.now)

    movie = relationship("MovieModel", back_populates="cart_items")
    cart = relationship("CartModel", back_populates="items")

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="uq_cart_movie"),
    )