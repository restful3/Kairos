from fastapi import APIRouter
from .routers import strategy

api_router = APIRouter()

api_router.include_router(strategy.router) 