from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Link(Base):
    __tablename__ = "links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shortcode: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expiry_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)
    clicks_count: Mapped[int] = mapped_column(Integer, default=0)

    clicks: Mapped[list["Click"]] = relationship(back_populates="link", cascade="all, delete-orphan")

class Click(Base):
    __tablename__ = "clicks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id"), nullable=False, index=True)
    timestamp: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    referrer: Mapped[str] = mapped_column(Text, nullable=True)
    ip: Mapped[str] = mapped_column(String(64), nullable=True)
    country: Mapped[str] = mapped_column(String(8), nullable=True, default="unknown")

    link: Mapped["Link"] = relationship(back_populates="clicks")
