import pytest

from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from contextlib import asynccontextmanager

from BACK.app import create_app
import BACK.models as models

from database_t import engine, session

GLOB_DICT = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    await session.rollback()
    await session.close()
    await engine.dispose()

app = create_app(session, lifespan)

#Запросы на "бэк" (8000)

def test_get_empty_user():
    with TestClient(app, base_url="http://127.0.0.1:8000/api") as client:
        response = client.get(
            "/users/123",
            headers={"X-Token": "coneofsilence"},
        )
    assert response.status_code == 404

def test_get_testuser():
    with TestClient(app, base_url="http://127.0.0.1:8000/api") as client:
        response = client.get(
            "users/1",
            headers={"X-Token": "coneofsilence"},
        )
    # 
    assert response.status_code == 200
    res_data: dict = response.json()
    assert res_data.get("user").get("name") == "Test User"

def test_get_user_me():
    with TestClient(app, base_url="http://127.0.0.1:8000/api") as client:
        response = client.get(
            "users/me",
            headers={"api-key": "test"},
        )
    # 
    assert response.status_code == 200
    res_data: dict = response.json()
    assert res_data.get("user").get("name") == "Test User"

def test_post_tweet_create():
    d_data = {"tweet_data": "ABCDEF"}
    with TestClient(app, base_url="http://127.0.0.1:8000/api") as client:
        response = client.post(
            "tweets",
            headers={"api-key": "test"},
            json=d_data
        )
        assert response.status_code == 200
        
        resp_data: dict = response.json()
        tweet_id = resp_data.get("tweet_id")
        GLOB_DICT["tweet_id"] = tweet_id
    
        

@pytest.mark.asyncio        
async def test_inner_check():
    tweet_id = GLOB_DICT.get("tweet_id")
    res = await session.execute(select(models.Tweet).where(models.Tweet.id==tweet_id))
    tweet: models.Tweet = res.scalar()
    assert tweet.content == "ABCDEF" 
    
def test_post_tweet_delete():
    tweet_id = GLOB_DICT.get("tweet_id")
    with TestClient(app, base_url="http://127.0.0.1:8000/api") as client:
        response = client.delete(
                f"tweets/{tweet_id}",
                headers={"api-key": "test"},
            )
    assert response.status_code == 200
 
