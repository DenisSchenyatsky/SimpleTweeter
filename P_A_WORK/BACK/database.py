from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# DATABASE_URL = "sqlite+aiosqlite:///./DB/tw.db"

DATABASE_URL = "postgresql+asyncpg://admin:admin@postgres_container:5432/admin"

engine = create_async_engine(DATABASE_URL, echo=True)
# expire_on_commit=False will prevent attributes from being expired
# after commit.
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
session = async_session()


class Base(DeclarativeBase):
    pass
