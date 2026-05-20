from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    DB_HOST: str = 'localhost'
    DB_PORT: int = 3306
    DB_USER: str = 'root'
    DB_PASSWORD: str = 'root'
    DB_NAME: str = 'etf_thermometer'
    DB_ECHO: bool = False

    TUSHARE_TOKEN: str = ''

    @property
    def db_url_async(self) -> str:
        """aiomysql 异步驱动，用于 FastAPI 运行时"""
        return f'mysql+aiomysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def db_url_sync(self) -> str:
        """pymysql 同步驱动，用于 alembic migration"""
        return f'mysql+pymysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


settings = Settings()
