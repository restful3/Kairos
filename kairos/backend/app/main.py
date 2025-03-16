from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import strategy
from .routers import backtest  # 백테스트 라우터 추가
from .api import api_router
from .core.config import settings
from .database import create_tables  # 데이터베이스 초기화 함수 추가

app = FastAPI(
    title="Kairos Trading API",
    description="자동 매매 전략 관리 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 초기화
create_tables()

# API 라우터 등록
app.include_router(strategy.router, prefix="/api")  # 전략 관리 API
app.include_router(backtest.router, prefix="/api")  # 백테스팅 API 추가
app.include_router(api_router, prefix="/api")  # 인증, 계좌, 주식 API

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "ok"} 