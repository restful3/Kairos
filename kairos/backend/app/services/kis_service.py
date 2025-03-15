import requests
import json
import yaml
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from app.core.config import settings
from app.utils.token_store import save_token, load_token, delete_token

class KisService:
    """한국투자증권 API 통신을 위한 서비스 클래스"""
    
    def __init__(self):
        """초기화 및 토큰 설정"""
        self.app_key = settings.KIS_APP_KEY
        self.app_secret = settings.KIS_APP_SECRET
        self.account = settings.KIS_ACCOUNT
        self.product_code = settings.KIS_PRODUCT_CODE
        self.base_url = settings.KIS_BASE_URL
        self.environment = settings.KIS_ENVIRONMENT
        self.token = None
        self.token_expires_at = None
        
        # 저장된 토큰 불러오기 시도
        self._load_saved_token()
        
        # 자동 토큰 발급은 필요할 때만 하도록 변경
        # self.ensure_token()
    
    def _load_saved_token(self) -> bool:
        """저장된 토큰 불러오기"""
        token_data = load_token(self.app_key)
        if token_data:
            self.token = token_data.get("token")
            self.token_expires_at = datetime.fromtimestamp(token_data.get("expires_at"))
            return True
        return False
    
    def ensure_token(self) -> None:
        """토큰이 없거나 만료되었을 경우 재발급"""
        now = datetime.utcnow()
        
        # 토큰이 없거나 만료 10분 전이면 갱신
        if (not self.token or 
            not self.token_expires_at or 
            (self.token_expires_at - now).total_seconds() < 600):  # 10분 전
            self.get_access_token()
    
    def get_access_token(self) -> Dict[str, Any]:
        """
        KIS API 접근 토큰 발급
        
        Returns:
            Dict[str, Any]: 토큰 정보 (access_token, expires_in)
        """
        # 1분 내에 토큰을 발급받은 적이 있는지 확인
        token_data = load_token(self.app_key)
        if token_data:
            # 토큰이 있고 1분 내에 생성된 것이면 재사용
            created_at = token_data.get("created_at", 0)
            if (int(datetime.utcnow().timestamp()) - created_at) < 60:  # 1분 이내
                print("1분 이내에 이미 토큰을 발급받았습니다. 같은 토큰을 재사용합니다.")
                self.token = token_data.get("token")
                self.token_expires_at = datetime.fromtimestamp(token_data.get("expires_at"))
                
                # 남은 시간(초) 계산
                expires_in = int((self.token_expires_at - datetime.utcnow()).total_seconds())
                return {
                    "access_token": self.token,
                    "expires_in": expires_in
                }
        
        url = f"{self.base_url}/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            response_data = response.json()
            
            if response.status_code == 200:
                self.token = response_data.get("access_token")
                # 토큰 만료 시간 설정
                expires_str = response_data.get("access_token_token_expired")
                if expires_str:
                    self.token_expires_at = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                else:
                    # 만료 시간이 없으면 1일로 설정
                    self.token_expires_at = datetime.utcnow().replace(hour=23, minute=59, second=59)
                
                # 토큰 저장
                save_token(self.token, self.app_key, self.token_expires_at)
                
                # 남은 시간(초) 계산
                expires_in = int((self.token_expires_at - datetime.utcnow()).total_seconds())
                return {
                    "access_token": self.token,
                    "expires_in": expires_in
                }
            else:
                print(f"토큰 발급 실패: {response.status_code} - {response_data}")
                raise Exception(f"토큰 발급 실패: {response_data.get('error_description', '알 수 없는 오류')}")
        except Exception as e:
            print(f"토큰 발급 중 오류 발생: {str(e)}")
            raise
    
    def get_base_headers(self) -> Dict[str, str]:
        """API 요청에 필요한 기본 헤더 반환"""
        self.ensure_token()
        
        return {
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "",  # 각 API 호출 시 설정
            "custtype": "P"  # 개인
        }
    
    def get_hashkey(self, params: Dict[str, Any]) -> Optional[str]:
        """주문 API에 필요한 해시키 생성"""
        url = f"{self.base_url}/uapi/hashkey"
        headers = self.get_base_headers()
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(params))
            if response.status_code == 200:
                return response.json().get("HASH")
            return None
        except Exception as e:
            print(f"해시키 생성 중 오류 발생: {str(e)}")
            return None
    
    def get_account_info(self) -> Dict[str, Any]:
        """계좌 정보 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        headers = self.get_base_headers()
        headers["tr_id"] = "VTTC8434R" if self.environment == "vps" else "TTTC8434R"
        
        params = {
            "CANO": self.account,
            "ACNT_PRDT_CD": self.product_code,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "N",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                response_data = response.json()
                print(f"계좌 정보 조회 실패: {response.status_code}, {response_data}")
                
                # 토큰 오류인 경우 토큰 삭제 후 재발급 시도
                error_msg = response_data.get("msg1", "")
                if "token" in error_msg.lower() or response.status_code == 401:
                    print("토큰 오류 감지, 토큰을 재발급합니다...")
                    delete_token()  # 기존 토큰 삭제
                    self.token = None  # 토큰 초기화
                    self.ensure_token()  # 새 토큰 발급
                    
                    # 토큰 재발급 후 다시 시도
                    headers = self.get_base_headers()
                    headers["tr_id"] = "VTTC8434R" if self.environment == "vps" else "TTTC8434R"
                    response = requests.get(url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        return response.json()
                
                # 여전히 오류가 있거나 토큰 문제가 아닌 경우
                return {"error": "계좌 정보 조회 실패", "status_code": response.status_code}
        except Exception as e:
            print(f"계좌 정보 조회 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def get_account_balance(self) -> Dict[str, Any]:
        """계좌 잔고 조회"""
        response = self.get_account_info()
        
        if "error" in response:
            return response
        
        try:
            if response.get("rt_cd") == "0":  # 성공
                # 예수금 정보
                output2 = response.get("output2", [])
                dn_deposit_amt = int(output2[0].get("dnca_tot_amt", "0")) if output2 else 0
                
                # 주식 보유 목록
                output1 = response.get("output1", [])
                stocks = []
                
                for stock in output1:
                    stocks.append({
                        "symbol": stock.get("pdno", ""),
                        "name": stock.get("prdt_name", ""),
                        "quantity": int(stock.get("hldg_qty", "0")),
                        "avg_price": float(stock.get("pchs_avg_pric", "0")),
                        "current_price": int(stock.get("prpr", "0")),
                        "profit_loss_rate": float(stock.get("evlu_pfls_rt", "0")),
                        "profit_loss": int(stock.get("evlu_pfls_amt", "0")),
                        "sellable_quantity": int(stock.get("ord_psbl_qty", "0"))
                    })
                
                # 결과 조합
                result = {
                    "deposit": dn_deposit_amt,
                    "stocks": stocks,
                    "total_evaluated_price": sum([s["current_price"] * s["quantity"] for s in stocks]),
                    "total_purchase_price": sum([s["avg_price"] * s["quantity"] for s in stocks])
                }
                
                return result
            else:
                return {
                    "error": response.get("msg1", "알 수 없는 오류"),
                    "code": response.get("rt_cd")
                }
        except Exception as e:
            print(f"잔고 정보 처리 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def get_stock_price(self, code: str) -> Dict[str, Any]:
        """
        종목 현재가 조회
        
        Args:
            code: 종목코드
            
        Returns:
            종목 현재가 정보
        """
        self.ensure_token()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("rt_cd") == "0":  # 성공
                    output = data.get("output", {})
                    
                    # 기본 정보 추출
                    current_price = int(output.get("stck_prpr", "0"))  # 현재가
                    price_change = int(output.get("prdy_vrss", "0"))  # 전일 대비
                    change_rate = float(output.get("prdy_ctrt", "0"))  # 전일 대비율
                    volume = int(output.get("acml_vol", "0"))  # 거래량
                    high_price = int(output.get("stck_hgpr", "0"))  # 고가
                    low_price = int(output.get("stck_lwpr", "0"))  # 저가
                    open_price = int(output.get("stck_oprc", "0"))  # 시가
                    prev_close = int(output.get("prdy_clpr", "0"))  # 전일 종가
                    
                    # 추가 정보 계산
                    market_cap = current_price * int(output.get("lstn_stcn", "0"))  # 시가총액 = 현재가 * 상장주식수
                    
                    # 52주 최고/최저 (별도 API 호출이 필요할 수 있음, 임시 데이터)
                    high_52wk = int(output.get("w52_hgpr", "0"))  # 52주 최고가
                    low_52wk = int(output.get("w52_lwpr", "0"))  # 52주 최저가
                    
                    # PER, PBR (별도 API 호출이 필요할 수 있음, 임시 데이터)
                    per = float(output.get("per", "0"))
                    pbr = float(output.get("pbr", "0"))
                    
                    # 상장주식수
                    listed_shares = int(output.get("lstn_stcn", "0"))
                    
                    result = {
                        "current_price": current_price,
                        "price_change": price_change,
                        "change_rate": change_rate,
                        "volume": volume,
                        "high_price": high_price,
                        "low_price": low_price,
                        "open_price": open_price,
                        "prev_close": prev_close,
                        "market_cap": market_cap,
                        "high_52wk": high_52wk if high_52wk > 0 else high_price,
                        "low_52wk": low_52wk if low_52wk > 0 else low_price,
                        "per": per,
                        "pbr": pbr,
                        "listed_shares": listed_shares
                    }
                    
                    return result
                else:
                    print(f"API 호출 실패: {data.get('msg1')}")
                    return {}
            else:
                print(f"API 호출 실패: {response.status_code}")
                return {}
        except Exception as e:
            print(f"종목 현재가 조회 중 오류: {str(e)}")
            return {} 