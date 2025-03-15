import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings

# FastAPI 앱 생성
app = FastAPI(
    title="Kairos - 실시간 퀀트 트레이딩 플랫폼",
    description="한국투자증권 Open Trading API를 활용한 실시간 퀀트 트레이딩 플랫폼 백엔드. Kairos는 그리스어로 '적절한 시기'를 의미하며, 거래에서 가장 중요한 타이밍의 개념을 담고 있습니다.",
    version="0.1.0",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix=settings.API_PREFIX)

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 