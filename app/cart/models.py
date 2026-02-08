from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

user_bought_movies = Table(
    "user_bought_movies",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
)

class CartModel(Base):
    __tablename__ = "carts"

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

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(default=datetime.now)

    cart = relationship("CartModel", back_populates="items")
    movie = relationship("MovieModel")

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="uq_cart_movie"),
    )