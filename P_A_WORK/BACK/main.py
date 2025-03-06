from fastapi import FastAPI
from sqlalchemy.dialects.postgresql import insert

import models
from database import engine, session
from app import create_app

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


app = create_app(session, lifespan)
