from contextlib import contextmanager
from typing import Optional, List

from loguru import logger
from sqlmodel import SQLModel, Field, Text, Relationship
from sqlmodel import create_engine, Session

from agent.common.config import SETTINGS
from agent.common.utils.utils import generate_id


class World(SQLModel, table=True):
    __tablename__ = "world"

    id: Optional[str] = Field(primary_key=True, default_factory=generate_id)
    name: str

    definition: List["WorldDefinition"] = Relationship(back_populates="world")
    reaction: List["ReactionDefinition"] = Relationship(back_populates="world")


class WorldDefinition(SQLModel, table=True):
    __tablename__ = "world_definition"

    id: Optional[int] = Field(default=None, primary_key=True)
    world_id: str = Field(foreign_key="world.id")
    value: str = Field(sa_type=Text)

    world: World = Relationship(back_populates="definition")


class ReactionDefinition(SQLModel, table=True):
    __tablename__ = "reaction_definition"

    id: Optional[int] = Field(default=None, primary_key=True)
    world_id: str = Field(foreign_key="world.id")
    name: str = Field(sa_type=Text)
    description: str = Field(default="", sa_type=Text)
    user_reaction: str = Field(default="", sa_type=Text)
    target_reaction: str = Field(default="", sa_type=Text)

    world: World = Relationship(back_populates="reaction")


class CharacterDefinition(SQLModel, table=True):
    __tablename__ = "character_definition"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_type=Text)
    description: str = Field(sa_type=Text)


class RuntimeData(SQLModel, table=True):
    __tablename__ = "runtime_data"

    id: Optional[str] = Field(primary_key=True, default_factory=generate_id)
    world_id: str = Field(foreign_key="world.id")
    label: str


class RawRequestRespondPair(SQLModel, table=True):
    __tablename__ = "raw_request_response_pair"
    id: Optional[int] = Field(default=None, primary_key=True)

    runtime_id: str = Field(foreign_key="runtime_data.id")
    request: str = Field(sa_type=Text)
    respond: str = Field(sa_type=Text)
    event_brief: str = Field(sa_type=Text)


engine = create_engine(
    url=SETTINGS.sql_db_url,
    echo=False,
    pool_size=SETTINGS.pool_size,
    max_overflow=SETTINGS.max_overflow,
)


def init_db():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_db_session():
    try:
        with Session(engine) as session:
            try:
                logger.trace("db session start!")
                yield session

                # with 块执行完毕后回到这里
                logger.trace(f"db session end!")

                # 无异常,提交事务
                session.commit()
                logger.trace(f"db session commit!")

            except Exception as e:      # 发生异常,回滚事务  重新抛出异常
                logger.exception(e)
                session.rollback()
                raise
            finally:        # 无论是否异常 , 都会记录
                logger.trace(f"db session closed!")

    except Exception as e:
        logger.error("无法创建session")
        logger.exception(e)


def get_test_session():

    session = Session(engine)

    yield session

    session.commit()
    session.close()
