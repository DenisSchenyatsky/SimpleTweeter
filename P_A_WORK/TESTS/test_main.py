from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import insert
from fastapi import FastAPI
from contextlib import asynccontextmanager

from BACK.app import create_app
import BACK.models as models

from database_t import engine, session

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

client = TestClient(app)

id_arr = []


def test_get_empty_user():
    response = client.get(
        "http://127.0.0.1:8000/api/users/123",
        headers={"X-Token": "coneofsilence"},
    )
    assert response.status_code == 404
    
def test_get_testuser():
    response = client.get(
        "http://127.0.0.1:8000/api/users/1",
        headers={"X-Token": "coneofsilence"},
    )
    # 
    assert response.status_code == 200
    res_data = response.json()
    assert res_data.get("user").get("name") == "Test User"
