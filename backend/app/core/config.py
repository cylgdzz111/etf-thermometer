from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    DB_URL: str = 'mysql+aiomysql://root:root@localhost:3306/etf_thermometer'
    DB_ECHO: bool = False
    TUSHARE_TOKEN: str = ''


settings = Settings()
