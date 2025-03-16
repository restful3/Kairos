from fastapi import APIRouter
from app.api import auth, account, stocks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(account.router, prefix="/account", tags=["계정"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["종목정보"])

# 백테스트 라우터 추가
from app.routers import backtest
api_router.include_router(backtest.router, prefix="/api", tags=["백테스트"])
