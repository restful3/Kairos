from fastapi import APIRouter
from app.api import auth, account

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(account.router, prefix="/account", tags=["계좌정보"])
