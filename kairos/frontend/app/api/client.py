import os
import requests
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from app.utils.token_store import save_token, load_token, delete_token

# 환경 변수 로드
load_dotenv()

# API 서버 URL
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

# API 엔드포인트
AUTH_ENDPOINT = f"{API_URL}/auth/token"
ME_ENDPOINT = f"{API_URL}/auth/me"
KIS_TOKEN_ENDPOINT = f"{API_URL}/auth/kis-token"
ACCOUNT_BALANCE_ENDPOINT = f"{API_URL}/account/balance"

# 종목 관련 엔드포인트
STOCKS_SEARCH_ENDPOINT = f"{API_URL}/stocks/search"
STOCK_DETAIL_ENDPOINT = f"{API_URL}/stocks"
STOCKS_SECTOR_ENDPOINT = f"{API_URL}/stocks/sector"
STOCKS_POPULAR_ENDPOINT = f"{API_URL}/stocks/popular"

class ApiClient:
    """백엔드 API 호출을 위한 클라이언트"""
    
    def __init__(self):
        self.token = None
        self._load_saved_token()
    
    def _load_saved_token(self):
        """저장된 토큰 불러오기"""
        token_data = load_token()
        if token_data:
            self.token = token_data.get("token")
            print(f"저장된 토큰을 로드했습니다. 만료까지 {token_data.get('remaining_minutes')}분 남았습니다.")
            return True
        return False
    
    def get_token(self) -> Optional[str]:
        """저장된 토큰 반환"""
        return self.token
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        백엔드 API 로그인
        
        Args:
            username: 사용자 아이디
            password: 비밀번호
            
        Returns:
            로그인 결과 (토큰 정보)
            
        Raises:
            Exception: 로그인 실패시 예외 발생
        """
        # 사용자명/비밀번호 유효성 검사
        if not username or not password:
            raise ValueError("사용자명과 비밀번호가 필요합니다.")
        
        # 로그인 요청 (OAuth2 폼 형식)
        try:
            response = requests.post(
                AUTH_ENDPOINT,
                data={
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                
                # 토큰 저장
                if self.token:
                    save_token(self.token, username)
                
                return data
            else:
                error_msg = response.json().get("detail", "로그인 실패")
                raise Exception(f"로그인 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"로그인 요청 중 오류 발생: {str(e)}")
    
    def logout(self):
        """로그아웃 및 토큰 삭제"""
        self.token = None
        delete_token()
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        현재 사용자 정보 조회
        
        Returns:
            사용자 정보
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
            
        try:
            response = requests.get(
                ME_ENDPOINT,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "사용자 정보 조회 실패")
                raise Exception(f"사용자 정보 조회 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"사용자 정보 조회 중 오류 발생: {str(e)}")
    
    def get_kis_token(self) -> Dict[str, Any]:
        """
        한국투자증권 API 토큰 발급
        
        Returns:
            KIS API 토큰 정보
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
            
        try:
            response = requests.post(
                KIS_TOKEN_ENDPOINT,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "KIS 토큰 발급 실패")
                raise Exception(f"KIS 토큰 발급 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"KIS 토큰 발급 중 오류 발생: {str(e)}")
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        계좌 잔고 정보 조회
        
        Returns:
            계좌 잔고 정보
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
        
        try:
            response = requests.get(
                ACCOUNT_BALANCE_ENDPOINT,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "계좌 잔고 조회 실패")
                raise Exception(f"계좌 잔고 조회 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"계좌 잔고 조회 중 오류 발생: {str(e)}")
    
    def search_stocks(self, query: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """
        종목 검색
        
        Args:
            query: 검색어 (종목명 또는 종목코드)
            limit: 최대 결과 수
            
        Returns:
            검색된 종목 목록
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
            
        try:
            params = {}
            if query:
                params["query"] = query
            if limit:
                params["limit"] = limit
                
            # 디버깅 로그 추가
            print(f"API 호출: {STOCKS_SEARCH_ENDPOINT} | 쿼리: {query} | 토큰: {self.token[:10]}...")
                
            response = requests.get(
                STOCKS_SEARCH_ENDPOINT,
                headers={"Authorization": f"Bearer {self.token}"},
                params=params
            )
            
            # 디버깅 로그 추가
            print(f"API 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                # 디버깅 로그 추가
                print(f"검색 결과 개수: {len(result)}")
                return result
            else:
                error_msg = response.json().get("detail", "종목 검색 실패")
                # 디버깅 로그 추가
                print(f"API 오류 응답: {response.text}")
                raise Exception(f"종목 검색 실패: {error_msg}")
        except Exception as e:
            # 디버깅 로그 추가
            import traceback
            print(f"종목 검색 예외: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"종목 검색 중 오류 발생: {str(e)}")
    
    def get_stock_detail(self, code: str) -> Dict[str, Any]:
        """
        종목 상세 정보 조회
        
        Args:
            code: 종목코드
            
        Returns:
            종목 상세 정보
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
            
        try:
            # 디버깅 로그 추가
            print(f"[DEBUG] 종목 상세 정보 조회: {code} | 엔드포인트: {STOCK_DETAIL_ENDPOINT}/{code}")
            
            # 실제 API 호출
            response = requests.get(
                f"{STOCK_DETAIL_ENDPOINT}/{code}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_msg = response.json().get("detail", "종목 상세 정보 조회 실패")
                raise Exception(f"종목 상세 정보 조회 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"종목 상세 정보 조회 중 오류 발생: {str(e)}")
    
    def get_stocks_by_sector(self, sector: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        업종별 종목 조회
        
        Args:
            sector: 업종명
            limit: 최대 결과 수
            
        Returns:
            업종별 종목 목록
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
            
        try:
            # 디버깅 로그 추가
            print(f"[DEBUG] 업종별 종목 호출: {STOCKS_SECTOR_ENDPOINT}/{sector} | 토큰: {self.token[:10]}...")
            
            # 실제 API 호출
            params = {"limit": limit} if limit else {}
            response = requests.get(
                f"{STOCKS_SECTOR_ENDPOINT}/{sector}",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_msg = response.json().get("detail", "업종별 종목 조회 실패")
                raise Exception(f"업종별 종목 조회 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"업종별 종목 조회 중 오류 발생: {str(e)}")
    
    def get_popular_stocks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        인기 종목 조회
        
        Args:
            limit: 최대 결과 수
            
        Returns:
            인기 종목 목록
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
            
        try:
            # 디버깅 로그 추가
            print(f"[DEBUG] 인기 종목 호출: {STOCKS_POPULAR_ENDPOINT} | 토큰: {self.token[:10]}...")
            
            # 실제 API 호출
            params = {"limit": limit} if limit else {}
            response = requests.get(
                STOCKS_POPULAR_ENDPOINT,
                headers={"Authorization": f"Bearer {self.token}"},
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_msg = response.json().get("detail", "인기 종목 조회 실패")
                raise Exception(f"인기 종목 조회 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"인기 종목 조회 중 오류 발생: {str(e)}")

# API 클라이언트 인스턴스 생성 (싱글톤)
api_client = ApiClient() 