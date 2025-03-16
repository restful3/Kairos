import os
import requests
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from app.utils.token_store import save_token, load_token, delete_token
from datetime import datetime, timedelta
import logging
import time

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
STOCK_DAILY_ENDPOINT = f"{API_URL}/stocks/{{}}/daily"  # 일별 시세 조회 엔드포인트

# 백테스팅 관련 엔드포인트
BACKTEST_ENDPOINT = f"{API_URL}/backtest"
BACKTEST_DETAIL_ENDPOINT = f"{API_URL}/backtest/{{}}"
BACKTEST_STRATEGY_ENDPOINT = f"{API_URL}/backtest/strategy/{{}}"

logger = logging.getLogger(__name__)

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
    
    def get_stock_history(self, code: str, days: int = 90) -> List[Dict[str, Any]]:
        """
        종목의 일별 시세 데이터 조회
        
        Args:
            code: 종목코드
            days: 조회 기간(일)
            
        Returns:
            일별 시세 데이터 목록
            
        Raises:
            Exception: API 호출 실패시 예외 발생
        """
        if not self.token:
            raise Exception("로그인이 필요합니다.")
            
        try:
            # 현재 날짜와 시작 날짜 계산
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            # 실제 API 호출
            endpoint = STOCK_DAILY_ENDPOINT.format(code)
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            print(f"[DEBUG] 주가 데이터 조회: {endpoint} | 기간: {days}일")
            
            response = requests.get(
                endpoint,
                headers={"Authorization": f"Bearer {self.token}"},
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_msg = response.json().get("detail", "주가 데이터 조회 실패")
                raise Exception(f"주가 데이터 조회 실패: {error_msg}")
        except Exception as e:
            raise Exception(f"주가 데이터 조회 중 오류 발생: {str(e)}")

    def _handle_response(self, response: requests.Response):
        """API 응답 처리"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP 오류: {e}"
            if response.content:
                try:
                    error_detail = response.json().get('detail', str(e))
                    error_msg = f"API 오류: {error_detail}"
                except:
                    pass
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"API 호출 중 오류 발생: {e}")
            raise

    def create_strategy(self, strategy_data: Dict[str, Any]) -> Optional[str]:
        """
        새로운 전략 생성
        
        Args:
            strategy_data: 전략 데이터
            
        Returns:
            생성된 전략 ID 또는 None
        """
        try:
            if not self.token:
                logger.error("인증 토큰이 없습니다.")
                return None

            logger.debug(f"전략 생성 요청: {strategy_data.get('name')}")
            response = requests.post(
                f"{API_URL}/strategies",
                json=strategy_data,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                strategy_id = response.json()
                logger.info(f"전략 생성 성공 - ID: {strategy_id}")
                return strategy_id
            else:
                error_msg = response.json().get("detail", "알 수 없는 오류")
                logger.error(f"전략 생성 실패: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"전략 생성 중 오류 발생: {str(e)}")
            return None
            
    def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> bool:
        """
        전략 업데이트
        
        Args:
            strategy_id: 전략 ID
            strategy_data: 업데이트할 전략 데이터
            
        Returns:
            성공 여부
        """
        try:
            if not self.token:
                logger.error("인증 토큰이 없습니다.")
                return False

            response = requests.put(
                f"{API_URL}/strategies/{strategy_id}",
                json=strategy_data,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"전략 업데이트 중 오류 발생: {str(e)}")
            return False
            
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        전략 삭제
        
        Args:
            strategy_id: 삭제할 전략 ID
            
        Returns:
            성공 여부
        """
        try:
            if not self.token:
                logger.error("인증 토큰이 없습니다.")
                return False

            response = requests.delete(
                f"{API_URL}/strategies/{strategy_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"전략 삭제 중 오류 발생: {str(e)}")
            return False
            
    def get_strategies(self, active_only: bool = False, flush_cache: bool = False) -> List[Dict[str, Any]]:
        """
        전략 목록 조회
        
        Args:
            active_only: 활성화된 전략만 조회할지 여부
            flush_cache: 캐시를 무시하고 새로 조회할지 여부
            
        Returns:
            전략 목록
        """
        try:
            if not self.token:
                logger.error("인증 토큰이 없습니다.")
                return []

            endpoint = f"{API_URL}/strategies"
            params = {"active_only": "true" if active_only else "false"}
            
            if flush_cache:
                # 캐시 무시를 위한 랜덤 파라미터 추가
                params["_nocache"] = str(int(time.time()))
            
            logger.debug(f"전략 목록 조회 요청 시작 - URL: {endpoint}, Params: {params}")
            
            response = requests.get(
                endpoint,
                headers={"Authorization": f"Bearer {self.token}"},
                params=params
            )
            
            logger.debug(f"전략 목록 조회 응답 - Status: {response.status_code}, Content: {response.text[:1000]}")
            
            if response.status_code == 200:
                try:
                    strategies = response.json()
                    if isinstance(strategies, dict) and 'strategies' in strategies:
                        # 응답이 {'strategies': [...]} 형태인 경우
                        strategies = strategies['strategies']
                    elif not isinstance(strategies, list):
                        # 응답이 리스트가 아닌 경우 (단일 전략인 경우)
                        strategies = [strategies] if strategies else []
                        
                    logger.info(f"전략 목록 조회 성공 - {len(strategies)}개 전략")
                    logger.debug(f"조회된 전략 목록: {json.dumps(strategies, ensure_ascii=False)}")
                    return strategies
                except json.JSONDecodeError as e:
                    logger.error(f"전략 목록 JSON 파싱 실패: {str(e)}")
                    return []
            else:
                error_msg = "알 수 없는 오류"
                try:
                    error_msg = response.json().get("detail", error_msg)
                except:
                    error_msg = response.text
                logger.error(f"전략 목록 조회 실패: {error_msg}")
                return []
                
        except Exception as e:
            logger.error(f"전략 목록 조회 중 오류 발생: {str(e)}")
            return []
            
    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        전략 상세 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            전략 데이터 또는 None
        """
        try:
            if not self.token:
                logger.error("인증 토큰이 없습니다.")
                return None

            response = requests.get(
                f"{API_URL}/strategies/{strategy_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"전략 조회 실패: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"전략 조회 중 오류 발생: {str(e)}")
            return None

    def run_backtest(
        self, 
        strategy_id: str, 
        days: int = 90, 
        initial_capital: float = 10000000, 
        fee_rate: float = 0.00015, 
        use_real_data: bool = True
    ) -> Dict[str, Any]:
        """
        백테스팅 실행
        
        Args:
            strategy_id: 전략 ID
            days: 백테스팅 기간 (일)
            initial_capital: 초기 자본금
            fee_rate: 거래 수수료율
            use_real_data: 실제 데이터 사용 여부
            
        Returns:
            백테스팅 결과
        """
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            
            payload = {
                "strategy_id": strategy_id,
                "days": days,
                "initial_capital": initial_capital,
                "fee_rate": fee_rate,
                "use_real_data": use_real_data
            }
            
            response = requests.post(BACKTEST_ENDPOINT, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                self._handle_response(response)
                logger.warning(f"백테스팅 실행 실패: {response.status_code}")
                return {"error": f"백테스팅 실행 실패: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"백테스팅 API 호출 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def get_backtest_result(self, backtest_id: str) -> Dict[str, Any]:
        """
        특정 백테스트 결과 조회
        
        Args:
            backtest_id: 백테스트 ID
            
        Returns:
            백테스트 결과
        """
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            response = requests.get(BACKTEST_DETAIL_ENDPOINT.format(backtest_id), headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self._handle_response(response)
                logger.warning(f"백테스트 결과 조회 실패: {response.status_code}")
                return {"error": f"백테스트 결과 조회 실패: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"백테스트 결과 조회 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def get_strategy_backtests(self, strategy_id: str) -> List[Dict[str, Any]]:
        """
        전략의 백테스트 결과 목록 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            백테스트 결과 목록
        """
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            response = requests.get(BACKTEST_STRATEGY_ENDPOINT.format(strategy_id), headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self._handle_response(response)
                logger.warning(f"전략 백테스트 목록 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"전략 백테스트 목록 조회 중 오류 발생: {str(e)}")
            return []

    # HTTP 요청 메서드 추가
    def get(self, url: str, params: Dict = None, headers: Dict = None) -> requests.Response:
        """
        GET 요청 수행
        
        Args:
            url: API 엔드포인트 URL
            params: 쿼리 파라미터
            headers: HTTP 헤더
            
        Returns:
            Response 객체
        """
        # 기본 헤더에 인증 토큰 추가
        default_headers = {}
        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"
        
        # 사용자 지정 헤더가 있으면 병합
        if headers:
            default_headers.update(headers)
        
        # API URL 구성 (상대 경로인 경우 절대 경로로 변환)
        full_url = url if url.startswith("http") else f"{API_URL}{url}"
        
        # GET 요청 실행
        return requests.get(full_url, params=params, headers=default_headers)
    
    def post(self, url: str, json: Dict = None, data: Dict = None, headers: Dict = None) -> requests.Response:
        """
        POST 요청 수행
        
        Args:
            url: API 엔드포인트 URL
            json: JSON 형식 데이터
            data: form 데이터
            headers: HTTP 헤더
            
        Returns:
            Response 객체
        """
        # 기본 헤더에 인증 토큰 추가
        default_headers = {}
        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"
        
        # 사용자 지정 헤더가 있으면 병합
        if headers:
            default_headers.update(headers)
        
        # API URL 구성 (상대 경로인 경우 절대 경로로 변환)
        full_url = url if url.startswith("http") else f"{API_URL}{url}"
        
        # POST 요청 실행
        return requests.post(full_url, json=json, data=data, headers=default_headers)
    
    def put(self, url: str, json: Dict = None, data: Dict = None, headers: Dict = None) -> requests.Response:
        """
        PUT 요청 수행
        
        Args:
            url: API 엔드포인트 URL
            json: JSON 형식 데이터
            data: form 데이터
            headers: HTTP 헤더
            
        Returns:
            Response 객체
        """
        # 기본 헤더에 인증 토큰 추가
        default_headers = {}
        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"
        
        # 사용자 지정 헤더가 있으면 병합
        if headers:
            default_headers.update(headers)
        
        # API URL 구성 (상대 경로인 경우 절대 경로로 변환)
        full_url = url if url.startswith("http") else f"{API_URL}{url}"
        
        # PUT 요청 실행
        return requests.put(full_url, json=json, data=data, headers=default_headers)
    
    def delete(self, url: str, params: Dict = None, headers: Dict = None) -> requests.Response:
        """
        DELETE 요청 수행
        
        Args:
            url: API 엔드포인트 URL
            params: 쿼리 파라미터
            headers: HTTP 헤더
            
        Returns:
            Response 객체
        """
        # 기본 헤더에 인증 토큰 추가
        default_headers = {}
        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"
        
        # 사용자 지정 헤더가 있으면 병합
        if headers:
            default_headers.update(headers)
        
        # API URL 구성 (상대 경로인 경우 절대 경로로 변환)
        full_url = url if url.startswith("http") else f"{API_URL}{url}"
        
        # DELETE 요청 실행
        return requests.delete(full_url, params=params, headers=default_headers)

# API 클라이언트 인스턴스 생성 (싱글톤)
api_client = ApiClient() 