import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# 토큰 저장 파일 경로
TOKEN_DIR = Path.home() / ".quant_trading_backend"
TOKEN_FILE = TOKEN_DIR / "token.json"

def save_token(token: str, app_key: str, expires_at: datetime):
    """
    토큰을 파일에 저장
    
    Args:
        token: 접근 토큰
        app_key: 앱 키 (식별용)
        expires_at: 토큰 만료 시간 (datetime 객체)
    """
    # 토큰 저장 디렉토리 생성
    os.makedirs(TOKEN_DIR, exist_ok=True)
    
    # 저장할 데이터
    token_data = {
        "token": token,
        "app_key": app_key,
        "created_at": int(time.time()),
        "expires_at": int(expires_at.timestamp()),
        "expires_at_human": expires_at.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 파일에 저장
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    
    print(f"토큰이 저장되었습니다. 만료시간: {token_data['expires_at_human']}")

def load_token(app_key: str = None) -> Optional[Dict[str, Any]]:
    """
    저장된 토큰 불러오기
    
    Args:
        app_key: 앱 키 (선택적, 지정시 해당 앱키의 토큰만 로드)
        
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
        
        # 앱키 일치 여부 확인 (지정된 경우)
        if app_key and token_data.get("app_key") != app_key:
            return None
        
        # 토큰 만료 여부 확인
        current_time = int(time.time())
        if token_data.get("expires_at", 0) <= current_time:
            # 만료된 토큰
            print("저장된 토큰이 만료되었습니다.")
            return None
        
        # 남은 시간 계산 (분 단위)
        remaining_minutes = (token_data.get("expires_at", 0) - current_time) // 60
        token_data["remaining_minutes"] = remaining_minutes
        
        print(f"저장된 토큰을 로드했습니다. 만료까지 {remaining_minutes}분 남았습니다.")
        return token_data
    except Exception as e:
        print(f"토큰 로드 중 오류 발생: {str(e)}")
        return None

def delete_token():
    """저장된 토큰 삭제"""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print("토큰이 삭제되었습니다.") 