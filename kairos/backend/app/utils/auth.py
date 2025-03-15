from datetime import datetime, timedelta
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# 사용자 데이터 저장 경로 (admin.py와 동일)
USERS_DIR = Path.home() / ".quant_trading_backend"
USERS_FILE = USERS_DIR / "users.json"

# OAuth2 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")

def load_users() -> Dict[str, Any]:
    """사용자 데이터 로드"""
    if not os.path.exists(USERS_FILE):
        return {}
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"사용자 데이터 로드 중 오류 발생: {str(e)}")
        return {}

def verify_password(password: str, password_data: Dict[str, Any]) -> bool:
    """
    비밀번호 검증 (admin.py의 함수와 동일한 구현)
    
    Args:
        password: 검증할 비밀번호
        password_data: 저장된 비밀번호 데이터 {'hash': 해시값, 'salt': 솔트, 'iterations': 반복 횟수}
        
    Returns:
        검증 결과 (True/False)
    """
    import hashlib
    import base64
    
    # PBKDF2 해싱
    hash_value = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        password_data['salt'].encode('utf-8'), 
        password_data['iterations']
    )
    
    # base64로 인코딩
    hash_b64 = base64.b64encode(hash_value).decode('utf-8')
    
    return hash_b64 == password_data['hash']

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    사용자 인증
    
    Args:
        username: 사용자명
        password: 비밀번호
        
    Returns:
        인증 성공 시 사용자 정보, 실패 시 None
    """
    users = load_users()
    
    if username not in users:
        return None
    
    user_data = users[username]
    if not verify_password(password, user_data["password_data"]):
        return None
    
    # 인증 성공 시 사용자 정보 반환 (비밀번호 데이터 제외)
    user_info = user_data.copy()
    user_info.pop("password_data", None)
    user_info["username"] = username
    
    return user_info

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간
        
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    현재 요청의 사용자 정보 조회
    
    Args:
        token: JWT 토큰
        
    Returns:
        사용자 정보
        
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 검증
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # 사용자 데이터 확인
    users = load_users()
    if username not in users:
        raise credentials_exception
    
    user_data = users[username]
    user_data["username"] = username
    
    return user_data

async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    현재 요청의 사용자가 관리자인지 확인
    
    Args:
        current_user: 현재 사용자 정보
        
    Returns:
        관리자 사용자 정보
        
    Raises:
        HTTPException: 관리자가 아닌 경우
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    return current_user 