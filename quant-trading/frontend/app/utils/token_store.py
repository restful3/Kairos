import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 토큰 저장 파일 경로
TOKEN_DIR = Path.home() / ".quant_trading"
TOKEN_FILE = TOKEN_DIR / "token.json"

def save_token(token: str, username: str = None, expires_in: int = 86400):
    """
    토큰을 파일에 저장
    
    Args:
        token: 접근 토큰
        username: 사용자 이름 (식별용)
        expires_in: 토큰 유효 시간(초), 기본 24시간
    """
    # 토큰 저장 디렉토리 생성
    os.makedirs(TOKEN_DIR, exist_ok=True)
    
    # 현재 시간과 만료 시간 계산
    current_time = int(time.time())
    expiry_time = current_time + expires_in
    
    # 저장할 데이터
    token_data = {
        "token": token,
        "username": username,
        "created_at": current_time,
        "expires_at": expiry_time,
        "expires_at_human": datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 파일에 저장
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

def load_token(username: str = None):
    """
    저장된 토큰 불러오기
    
    Args:
        username: 사용자 이름 (선택적, 지정시 해당 사용자의 토큰만 로드)
        
    Returns:
        토큰이 유효하면 토큰 정보 반환, 아니면 None 반환
    """
    # 파일이 없으면 None 반환
    if not os.path.exists(TOKEN_FILE):
        return None
    
    try:
        # 파일에서 토큰 데이터 읽기
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
        
        # 사용자 이름 일치 여부 확인 (지정된 경우)
        if username and token_data.get("username") != username:
            return None
        
        # 토큰 만료 여부 확인
        current_time = int(time.time())
        if token_data.get("expires_at", 0) <= current_time:
            # 만료된 토큰
            return None
        
        # 남은 시간 계산 (분 단위)
        remaining_minutes = (token_data.get("expires_at", 0) - current_time) // 60
        token_data["remaining_minutes"] = remaining_minutes
        
        return token_data
    except Exception as e:
        print(f"토큰 로드 중 오류 발생: {str(e)}")
        return None

def delete_token():
    """저장된 토큰 삭제"""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE) 