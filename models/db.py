import os
from typing import Type, List, TypeVar

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, Field, Session, select, delete
from sqlmodel.ext.asyncio.session import AsyncSession

from tools import LanguageSingleton

T = TypeVar("T")


class ChapterFile(SQLModel, table=True):
    url: str = Field(primary_key=True)
    file_id: str
    file_unique_id: str
    cbz_id: str
    cbz_unique_id: str
    telegraph_url: str


class MangaOutput(SQLModel, table=True):
    user_id: str = Field(primary_key=True, regex=r'\d+')
    output: int = Field


class Subscription(SQLModel, table=True):
    url: str = Field(primary_key=True)
    user_id: str = Field(primary_key=True, regex=r'\d+')


class LastChapter(SQLModel, table=True):
    url: str = Field(primary_key=True)
    chapter_url: str = Field


class MangaName(SQLModel, table=True):
    url: str = Field(primary_key=True)
    name: str = Field


class DB(metaclass=LanguageSingleton):
    
    def __init__(self, dbname: str = 'sqlite:///test.db'):
        if dbname.startswith('postgres://'):
            dbname = dbname.replace('postgres://', 'postgresql+asyncpg://', 1)
        if dbname.startswith('sqlite'):
            dbname = dbname.replace('sqlite', 'sqlite+aiosqlite', 1)
    
        self.engine = create_async_engine(dbname)
        
    async def connect(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)

    async def add(self, other: SQLModel):
        async with AsyncSession(self.engine) as session:  # type: AsyncSession
            async with session.begin():
                session.add(other)

    async def get(self, table: Type[T], id) -> T:
        async with AsyncSession(self.engine) as session:  # type: AsyncSession
            return await session.get(table, id)

    async def get_all(self, table: Type[T]) -> List[T]:
        async with AsyncSession(self.engine) as session:  # type: AsyncSession
            statement = select(table)
            return await session.exec(statement=statement)

    async def erase(self, other: SQLModel):
        async with AsyncSession(self.engine) as session:  # type: AsyncSession
            async with session.begin():
                await session.delete(other)

    async def get_chapter_file_by_id(self, id: str):
        async with AsyncSession(self.engine) as session:  # type: AsyncSession
            statement = select(ChapterFile).where((ChapterFile.file_unique_id == id) |
                                                  (ChapterFile.cbz_unique_id == id) |
                                                  (ChapterFile.telegraph_url == id))
            return (await session.exec(statement=statement)).first()

    async def get_subs(self, user_id: str) -> List[MangaName]:
        async with AsyncSession(self.engine) as session:
            statement = select(MangaName).where(Subscription.user_id == user_id).where(Subscription.url == MangaName.url)
            return (await session.exec(statement=statement)).all()

    async def erase_subs(self, user_id: str):
        async with AsyncSession(self.engine) as session:
            async with session.begin():
                statement = delete(Subscription).where(Subscription.user_id == user_id)
                await session.exec(statement=statement)

