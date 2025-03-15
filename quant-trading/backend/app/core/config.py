from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    # API 설정
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    
    # 보안 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # CORS 설정
    ALLOW_ORIGINS: List[str] = ["http://localhost:8501", "http://frontend:8501"]
    
    # KIS API 설정
    KIS_ENVIRONMENT: str = os.getenv("KIS_ENVIRONMENT", "vps")  # 'prod' 또는 'vps' (모의투자)
    KIS_APP_KEY: str = os.getenv("KIS_APP_KEY", "")
    KIS_APP_SECRET: str = os.getenv("KIS_APP_SECRET", "")
    KIS_ACCOUNT: str = os.getenv("KIS_ACCOUNT", "")
    KIS_PRODUCT_CODE: str = os.getenv("KIS_PRODUCT_CODE", "01")
    KIS_HTS_ID: str = os.getenv("KIS_HTS_ID", "")
    
    # URL 설정
    KIS_PROD_URL: str = os.getenv("KIS_PROD_URL", "https://openapi.koreainvestment.com:9443")
    KIS_PROD_WS: str = os.getenv("KIS_PROD_WS", "ws://ops.koreainvestment.com:21000")
    KIS_VPS_URL: str = os.getenv("KIS_VPS_URL", "https://openapivts.koreainvestment.com:29443")
    KIS_VPS_WS: str = os.getenv("KIS_VPS_WS", "ws://ops.koreainvestment.com:31000")
    
    # API 서버 설정
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    @property
    def KIS_BASE_URL(self) -> str:
        """현재 설정된 환경에 따른 KIS API 기본 URL 반환"""
        return self.KIS_PROD_URL if self.KIS_ENVIRONMENT == "prod" else self.KIS_VPS_URL
    
    @property
    def KIS_WS_URL(self) -> str:
        """현재 설정된 환경에 따른 KIS 웹소켓 URL 반환"""
        return self.KIS_PROD_WS if self.KIS_ENVIRONMENT == "prod" else self.KIS_VPS_WS
    
    class Config:
        case_sensitive = True

# 설정 인스턴스 생성
settings = Settings() 