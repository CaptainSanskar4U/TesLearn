from datetime import datetime, timezone

from sqlmodel import Field, Session, SQLModel, create_engine

from config import DB_PATH


class Clip(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str
    duration: int = 12
    filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Podcast(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str
    filename: str
    script_json: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Mindmap(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str
    filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Comic(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str
    title: str = ""
    filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Note(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str
    notes_markdown: str = ""
    handwritten_json: str = "[]"
    diagrams_json: str = "[]"
    images_status: str = "pending"
    error: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Lab(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str
    filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
