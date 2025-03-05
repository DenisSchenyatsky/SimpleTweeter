from typing import List, Union, Annotated, Optional

from fastapi import FastAPI, Header, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.expression import update

import models

import schemas
from database import engine, session

import random
import os
import util_func

from contextlib import asynccontextmanager

from models import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    await logger.info("---===< DB and its ORM try to init...>===---")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    try:
        # await session.add(models.User(id=0, api_key='None', name='None'))
        await session.execute(
            insert(models.User)
            .values(id=0, api_key="None", name="None")
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await session.execute(
            insert(models.User)
            .values(id=1, api_key="test", name="Test User")
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await session.execute(
            insert(models.User)
            .values(id=2, api_key="test2", name="Test User2")
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await session.execute(
            insert(models.UserUser)
            .values(id=1, follow_to_id=2)
            .on_conflict_do_nothing(index_elements=["id", "follow_to_id"])
        )
        # await session.add(models.Tweet(id=0, content='None', author_id=0))
        await session.execute(
            insert(models.Tweet)
            .values(id=0, content="None", author_id=0)
            .on_conflict_do_nothing(index_elements=["id"])
        )

        await session.commit()
    except Exception:
        pass

    yield
    await logger.info("---===< DB and its ORM try to tear down...>===---")
    await session.rollback()
    await session.close()
    await engine.dispose()


IMG_PATH = "./IMG"

app = FastAPI(lifespan=lifespan)


#   API USERS
#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.get(
    "/api/users/{user_id}/",
    response_model=Union[schemas.UserResultOut, schemas.ErrResultOut],
)
async def user_by_id(
    user_id: Optional[str] = 0,
    api_key: Annotated[str | None, Header()] = None,
) -> Union[models.User, dict]:
    """
    <h1>
    Информация о пользователе по id или 'me' ключом.
    </h1>
    """
    if user_id == "me":
        user, err_dict = await models.User.get_by_api_key(api_key)
        if user is None:
            return err_dict
    else:
        user_id = int(user_id)
        res = await session.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user = res.scalar()
        if user is None:
            return util_func.get_err_JSONRes(
                404, "not found", f"User with id: {user_id} doesn't exist."
            )

    await user.get_up_follows()
    result = {"result": True, "user": user.as_dict()}
    return result


#  /API/USERS  /FOLLOW
#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.post(
    "/api/users/{user_id}/follow/",
    response_model=Union[schemas.ResultOut, schemas.ErrResultOut],
)
async def start_follow_by_id(
    api_key: Annotated[str | None, Header()] = None, user_id: Optional[int] = None
) -> dict:
    """
    <h1>
    Стать последователем.
    </h1>
    """
    persecutor, err_dict = await models.User.get_by_api_key(api_key)
    if persecutor is None:
        return err_dict

    res = await session.execute(select(models.User).where(models.User.id == user_id))
    victim = res.scalar()
    if victim is None:
        return util_func.get_err_dict(
            "not found", f"User with id: {user_id} doesn't exist."
        )

    new_useruser = models.UserUser()
    new_useruser.user = persecutor
    new_useruser.follow_to_user = victim
    try:
        session.add(new_useruser)
        await session.commit()
    except Exception as err:
        await session.rollback()
        return {"result": False, "error_type": "read below", "error_message": str(err)}
    return {"result": True}


#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.delete(
    "/api/users/{user_id}/follow/",
    response_model=Union[schemas.ResultOut, schemas.ErrResultOut],
)
async def end_follow_by_id(
    api_key: Annotated[str | None, Header()] = None, user_id: int = 0
) -> dict:
    """
    <h1>
    Прекратить преследование.
    </h1>
    """
    try:
        res = await session.execute(
            select(models.UserUser)
            .join(models.User, models.User.id == models.UserUser.id)
            .where(
                and_(
                    models.User.api_key == api_key,
                    models.UserUser.follow_to_id == user_id,
                )
            )
        )
        record_uu = res.scalar()
        if record_uu is None:
            return JSONResponse(
                status_code=404,
                content=util_func.get_err_dict(
                    "not found",
                    f"Following to '{user_id}' for api-key: '{api_key}' doesn't exist.",
                ),
            )
        await session.delete(record_uu)
        await session.commit()
    except Exception as err:
        await session.rollback()
        return {"result": False, "error_type": "read below", "error_message": str(err)}
    return {"result": True}


#       /API/TWEETS
#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.post(
    "/api/tweets/",
    response_model=Union[schemas.TweetResultOut, schemas.ErrResultOut],
)
async def add_tweet(
    api_key: Annotated[str | None, Header()] = None, tweet: schemas.TweetIn = None
) -> dict:
    """
    <h1>
    Добавить твит.
    </h1>
    """
    user, err_dict = await models.User.get_by_api_key(api_key)
    if user is None:
        return err_dict
    try:
        tweet_record = models.Tweet(content=tweet.tweet_data)
        tweet_record.author = user

        session.add(tweet_record)
        await session.flush()
        tweet_id = tweet_record.id
        if tweet.tweet_media_ids:
            await session.execute(
                update(models.Picture)
                .where(models.Picture.id.in_(tweet.tweet_media_ids))
                .values(tweet_id=tweet_id)
            )
        await session.commit()

    except Exception as err:
        await session.rollback()
        await logger.info(f"---===EXCEPTION ON ADD TWEET===---")
        return {"result": False, "error_type": "read below", "error_message": str(err)}
    return {"result": True, "tweet_id": tweet_id}


#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.delete(
    "/api/tweets/{tweet_id}",
    response_model=Union[schemas.ResultOut, schemas.ErrResultOut],
)
async def delete_tweet(
    api_key: Annotated[str | None, Header()] = None, tweet_id: int = 0
) -> dict:
    """
    <h1>
    Удалить твит.
    </h1>
    """
    user, err_dict = await models.User.get_by_api_key(api_key)
    if user is None:
        return err_dict
    author_id = user.id
    try:
        res = await session.execute(
            select(models.Tweet).where(
                and_(models.Tweet.id == tweet_id, models.Tweet.author_id == author_id)
            )
        )
        tweet: models.Tweet = res.scalar()
        if not tweet:
            return JSONResponse(
                status_code=404,
                content=util_func.get_err_dict(
                    "not found",
                    f"Tweet: {tweet_id} and author: {api_key} doesn't exist.",
                ),
            )

        await session.delete(tweet)
        await session.commit()
    except Exception as err:
        await session.rollback()
        await logger.info(f"---===EXCEPTION ON ADD TWEET===---")
        return {"result": False, "error_type": "read below", "error_message": str(err)}
    return {"result": True, "tweet_id": tweet_id}


#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.get(
    "/api/tweets/",
    response_model=Union[schemas.TweetResultListOut, schemas.ErrResultOut],
)
async def get_all_tweets_by_api_key(
    api_key: Annotated[str | None, Header()] = None,
) -> dict:
    """
    <h1>
    Получить все твиты пользователя.<br>
    И все твиты пользователей за твитами которых он поглядвает.
    </p>
    """
    user, err_dict = await models.User.get_by_api_key(api_key)
    if user is None:
        return err_dict
    try:
        own_id = user.id
        res = await session.execute(
            select(models.Tweet).filter(models.Tweet.author_id == own_id)
        )
        own_tweets = list(res.scalars())

        res = await session.execute(
            select(models.Tweet)
            .join(models.User, models.User.id == models.Tweet.author_id)
            .join(models.UserUser, models.UserUser.follow_to_id == models.User.id)
            .filter(models.UserUser.id == own_id)
        )
        tweets: List[models.Tweet] = list(res.scalars())
        tweets.extend(own_tweets)
        for t in tweets:
            t.get_attach_from_pic()

    except Exception as err:
        await logger.info(f"---===EXCEPTION ON TWEETS LIST===---")
        return {"result": False, "error_type": "read below", "error_message": str(err)}
    return {"result": True, "tweets": tweets}


#       /API/TWEETS/    LIKES
#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.post(
    "/api/tweets/{tweet_id}/likes",
    response_model=Union[schemas.ResultOut, schemas.ErrResultOut],
)
async def add_like_to_tweet(
    api_key: Annotated[str | None, Header()] = None, tweet_id: int = 0
) -> dict:
    """
    <h1>
    Выразить своё согласие с написанным.
    </h1>
    """
    user, err_dict = await models.User.get_by_api_key(api_key)
    if user is None:
        return err_dict

    res = await session.execute(
        select(models.Tweet)
        .join(models.Like, models.Like.tweet_id == models.Tweet.id)
        .where(models.Tweet.id == tweet_id)
    )
    tweet: models.Tweet = res.scalar()
    if tweet is None:
        tweet = await session.get(models.Tweet, tweet_id)
        if tweet is None:
            return util_func.get_err_dict(
                "not found", f"Tweet with id: {tweet_id} doesn't exist."
            )
    try:
        tweet.likes.append(user)
        await session.commit()
    except Exception as err:
        await session.rollback()
        await logger.info(f"---===EXCEPTION ON LIKE ADD===---")
        return {"result": False, "error_type": "read below", "error_message": str(err)}
    return {"result": True}


#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
@app.delete(
    "/api/tweets/{tweet_id}/likes",
    response_model=Union[schemas.ResultOut, schemas.ErrResultOut],
)
async def delete_like_from_tweet(
    api_key: Annotated[str | None, Header()] = None, tweet_id: int = 0
) -> dict:
    """
    <h1>
    Опомниться и отозвать своё согласие с написанным.
    </h1>
    """
    user, err_dict = await models.User.get_by_api_key(api_key)
    if user is None:
        return err_dict
    user_id = user.id
    res = await session.execute(
        select(models.Like).where(
            and_(models.Tweet.id == tweet_id, models.Like.user_id == user_id)
        )
    )
    like_record: models.Tweet = res.scalar()
    if like_record is None:
        return util_func.get_err_dict(
            "not found",
            f"Like record with api: {api_key} and ip: {tweet_id} doesn't exist.",
        )
    try:
        await session.delete(like_record)
        await session.commit()
    except Exception as err:
        await logger.info(f"---===EXCEPTION ON LIKE DELETE===---")
        await session.rollback()
        return util_func.get_err_dict("read below", str(err))
    return {"result": True}


#       /API/MEDIAS
#   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *


@app.post(
    "/api/medias/",
    response_model=Union[schemas.MediaResultOut, schemas.ErrResultOut],
)
async def get_image_from_form(
    api_key: Annotated[str, Header()] = None,
    file: UploadFile | None = None,
) -> dict:
    """
    <h2>
    Загрузка картинки file для твита. </h2> с tweed_id = None.
    Создается запись в б.д. Отплевывается id записи.
    После, когда произойдёт запрос на создание твита
    фронт предоставит id которые надо связать с этим запросом.

    """
    file_dir = os.path.join(IMG_PATH, api_key)
    try:
        os.makedirs(file_dir)
    except FileExistsError:
        # directory already exists
        pass

    try:
        if file is None:
            await logger.info("---=== FILE IS NONE ===---")
            return util_func.get_err_dict("???", "File is None")
        file_name = file.filename
        await logger.info(f"---=== new_pic_id: { file_name } ===---")

        prefix = str(random.randint(1, 99999))
        file_path = os.path.join(file_dir, "".join([prefix, "_", file_name]))

        res = await session.execute(
            insert(models.Picture)
            .values(file_path=file_path, tweet_id=0)
            .returning(models.Picture)
        )
        new_picture = res.scalar()
        media_id = new_picture.id

        await util_func.save_file(file, file_path)

    except Exception as err:
        await session.rollback()
        await logger.info("---===EXCEPTION MEDIA RECIEVE===---")
        return util_func.get_err_dict("read below", str(err))
    return {"result": True, "media_id": media_id}
