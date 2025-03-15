from fastapi import APIRouter
from app.api import auth, account, stocks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(account.router, prefix="/account", tags=["계좌정보"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["종목정보"])
