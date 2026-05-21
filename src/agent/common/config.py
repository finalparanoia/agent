from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sql_db_url: str = "postgresql://test:test@192.168.3.184:5432/test"
    pool_size: int = 256
    max_overflow: int = 0


SETTINGS = Settings()
