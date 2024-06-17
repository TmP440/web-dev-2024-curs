from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

# Промежуточная таблица для связи "многие ко многим"
music_style_table = db.Table(
    'MusicStyle',
    db.Model.metadata,
    db.Column('music_id', db.ForeignKey('music.id'), primary_key=True),
    db.Column('style_id', db.ForeignKey('style.id'), primary_key=True),
    extend_existing=True
)


class Role(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(64), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(
        db.String(100), nullable=False, unique=True
    )

    users: Mapped[list["User"]] = db.relationship(back_populates="role", uselist=True)


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(300), nullable=False)
    last_name: Mapped[str] = mapped_column(db.String(64), nullable=False)
    first_name: Mapped[str] = mapped_column(db.String(64), nullable=False)
    middle_name: Mapped[str] = mapped_column(db.String(64))
    role_id: Mapped[int] = mapped_column(db.ForeignKey("role.id"))

    role: Mapped["Role"] = db.relationship(back_populates="users", uselist=False)
    reviews: Mapped[list["Review"]] = db.relationship(
        back_populates="user", uselist=True
    )


class Music(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), unique=True, nullable=False)
    short_description: Mapped[str] = mapped_column(db.Text, nullable=False)
    year: Mapped[int] = mapped_column(db.SmallInteger, nullable=False)
    label: Mapped[str] = mapped_column(db.String(64), nullable=False)
    author: Mapped[str] = mapped_column(db.String(64), nullable=False)
    pages: Mapped[int] = mapped_column(nullable=False)
    cover_id: Mapped[int] = mapped_column(db.ForeignKey("cover.id"))

    cover: Mapped["Cover"] = db.relationship(back_populates="musics", uselist=False)
    styles: Mapped[list["Style"]] = db.relationship(
        back_populates="musics", uselist=True, secondary=music_style_table
    )
    reviews: Mapped[list["Review"]] = db.relationship(
        back_populates="music", uselist=True, cascade="all, delete-orphan"
    )


class Style(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    style_name: Mapped[str] = mapped_column(db.String(200), nullable=False, unique=True)

    musics: Mapped[list["Music"]] = db.relationship(
        back_populates="styles", uselist=True, secondary=music_style_table
    )


class Cover(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    MIME_type: Mapped[str] = mapped_column(db.String(200), nullable=False)
    MD5_hash: Mapped[str] = mapped_column(db.String(200), nullable=False)

    musics: Mapped[list["Music"]] = db.relationship(back_populates="cover", uselist=True)


class Review(db.Model):
    music_id: Mapped[int] = mapped_column(db.ForeignKey("music.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("user.id"), primary_key=True)
    score: Mapped[int] = mapped_column(nullable=False)
    text: Mapped[int] = mapped_column(db.Text, nullable=False)
    creation_date: Mapped[int] = mapped_column(db.TIMESTAMP, default=func.now())

    music: Mapped["Music"] = db.relationship(back_populates="reviews", uselist=False)
    user: Mapped["User"] = db.relationship(back_populates="reviews", uselist=False)
