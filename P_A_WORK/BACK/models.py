from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.future import select

from typing import List, Optional

from sqlalchemy.orm import Session
session: Session = None
#from database import session

def set_session(some_session: Session): 
    """
    Редкостное ...
    """
    global session
    session = some_session



# /\/\/\/\/\/\/\/\/\/\/\/\/\
from aiologger.loggers.json import JsonLogger
from aiologger.formatters.json import FUNCTION_NAME_FIELDNAME, LOGGED_AT_FIELDNAME

logger = JsonLogger.with_default_handlers(
    level="DEBUG",
    serializer_kwargs={"ensure_ascii": False},
    exclude_fields=[
        FUNCTION_NAME_FIELDNAME,
        LOGGED_AT_FIELDNAME,
        "file_path",
        "line_number",
    ],
)
# \/\/\/\/\/\/\/\/\/\/\/\/\/

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    api_key = mapped_column(String, index=True, unique=True, nullable=False)
    name = mapped_column(String, nullable=False)

    tweets: Mapped[List["Tweet"]] = relationship(
        lazy="selectin", back_populates="author"
    )

    following: List["User"] = []
    followers: List["User"] = []

    def as_dict(self):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        result.update({"followers": self.followers, "following": self.following})
        return result

    @classmethod
    async def get_by_api_key(cls, key: str) -> tuple["User", Optional[dict]]:
        """
        Возвращает пользователя по api-key и None.<br>
        Либо наоборот - None и словарь с описанием ошибки.
        """
        res = await session.execute(select(User).where(User.api_key == key))
        res = res.scalar()
        if res is None:
            logger.info(f"---===USER DOESN'T EXIST===---")
            return None, {
                "result": False,
                "error_type": "record not found",
                "error_message": f"User with api-key: '{key}' doesn't exist.",
            }
        return res, None

    async def get_up_follows(self):
        """
        Заполняет списки последователей и за кем следует сам. <br>
        Применимо к объекту с уже сформированным id.
        """
        user_id = self.id
        res = await session.execute(
            (
                select(User)
                .join(UserUser, User.id == UserUser.id)
                .filter(user_id == UserUser.follow_to_id)
            )
        )
        self.followers = res.scalars().all()
        res = await session.execute(
            (
                select(User)
                .join(UserUser, User.id == UserUser.follow_to_id)
                .filter(user_id == UserUser.id)
            )
        )
        self.following = res.scalars().all()


class Tweet(Base):
    __tablename__ = "tweets"
    id = mapped_column(Integer, primary_key=True)
    content = mapped_column(String, nullable=False)
    author_id = mapped_column(Integer, ForeignKey("users.id"))

    author: Mapped["User"] = relationship(
        lazy="selectin", uselist=False, back_populates="tweets"
    )

    attachments: List[str] = []

    pictures: Mapped[List["Picture"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    like_as_user_tweet_ass: Mapped[List["Like"]] = relationship(
        back_populates="tweets",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    likes: AssociationProxy[List[User]] = association_proxy(
        "like_as_user_tweet_ass",
        "user",
        creator=lambda user_obj: Like(user=user_obj),
    )

    def get_attach_from_pic(self):
        arr = self.pictures
        self.attachments = []
        for pic in arr:
            self.attachments.append(pic.file_path)


class Like(Base):
    __tablename__ = "likes"
    user_id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    tweet_id = mapped_column(Integer, ForeignKey("tweets.id"), primary_key=True)

    tweets: Mapped[Tweet] = relationship(
        lazy="selectin", back_populates="like_as_user_tweet_ass"
    )
    user: Mapped[User] = relationship(lazy="selectin", uselist=False)


class UserUser(Base):
    __tablename__ = "users_users"
    id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    follow_to_id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)

    user: Mapped["User"] = relationship(
        lazy="selectin", uselist=False, foreign_keys=[id]
    )
    follow_to_user: Mapped["User"] = relationship(
        lazy="selectin", uselist=False, foreign_keys=[follow_to_id]
    )


class Picture(Base):
    __tablename__ = "pictures"
    id = mapped_column(Integer, primary_key=True)
    tweet_id = mapped_column(Integer, ForeignKey("tweets.id"), nullable=True)
    file_path = mapped_column(String, nullable=False)
