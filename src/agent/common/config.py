from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序配置类，包含数据库和LLM相关设置"""
    sql_db_url: str = "postgresql://test:test@192.168.3.184:5432/test"
    pool_size: int = 256
    max_overflow: int = 0

    llm_model: str = "unsloth/Gemma4"
    llm_api_key: str = "cx"
    llm_api_base: str = "http://10.6.0.102:8000/v1"


SETTINGS = Settings()
