from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict, Any

from app.schemas.auth import TokenResponse, UserResponse, ErrorResponse
from app.utils.auth import authenticate_user, create_access_token, get_current_user, get_admin_user
from app.core.config import settings
from app.services.kis_service import KisService

router = APIRouter()

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    """
    사용자 로그인 및 액세스 토큰 발급
    
    이 엔드포인트는 클라이언트(프론트엔드)의 인증을 처리합니다.
    사용자 ID/비밀번호가 인증되면 백엔드 API 사용을 위한 액세스 토큰을 발급합니다.
    """
    # 사용자 인증
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "is_admin": user.get("is_admin", False)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 초 단위로 변환
    }

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    현재 인증된 사용자 정보 조회
    
    이 엔드포인트는 현재 인증된 사용자의 정보를 반환합니다.
    """
    return {
        "username": current_user.get("username"),
        "is_admin": current_user.get("is_admin", False),
        "created_at": current_user.get("created_at", None)
    }

@router.post("/kis-token", response_model=TokenResponse)
async def get_kis_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    한국투자증권 API 토큰 발급
    
    이 엔드포인트는 서버에 저장된 한국투자증권 API 키/시크릿을 사용하여
    한국투자증권 API 토큰을 발급하고 반환합니다.
    """
    try:
        # KIS 서비스 인스턴스 생성
        kis_service = KisService()
        
        # 토큰 발급
        token_data = kis_service.get_access_token()
        
        return {
            "access_token": token_data.get("access_token"),
            "token_type": "bearer",
            "expires_in": token_data.get("expires_in", 86400)  # 기본값 1일(86400초)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"한국투자증권 API 토큰 발급 실패: {str(e)}"
        )