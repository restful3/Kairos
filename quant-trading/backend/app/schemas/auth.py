from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List

class TokenRequest(BaseModel):
    """토큰 요청 스키마"""
    app_key: str = Field(..., description="KIS Developers에서 발급받은 앱키")
    app_secret: str = Field(..., description="KIS Developers에서 발급받은 앱시크릿")
    
    class Config:
        schema_extra = {
            "example": {
                "app_key": "PSA5ZTBBTPU70OHTV5ZB",
                "app_secret": "XPGCFK8P9JLY1ILRFMXJWXXX7A4RWUK4ZNKA"
            }
        }

class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""
    username: str
    is_admin: bool = False
    created_at: Optional[str] = None

class UserCreate(BaseModel):
    """사용자 생성 요청 스키마"""
    username: str
    password: str
    is_admin: bool = False

class Account(BaseModel):
    """계좌 기본 정보 스키마"""
    account_number: str = Field(..., description="계좌번호")
    product_code: str = Field(..., description="상품코드")
    
    class Config:
        schema_extra = {
            "example": {
                "account_number": "12345678",
                "product_code": "01"
            }
        }

class Stock(BaseModel):
    """보유 종목 정보 스키마"""
    symbol: str = Field(..., description="종목코드")
    name: str = Field(..., description="종목명")
    quantity: int = Field(..., description="보유수량")
    avg_price: float = Field(..., description="매입평균가")
    current_price: int = Field(..., description="현재가")
    profit_loss_rate: float = Field(..., description="손익률")
    profit_loss: int = Field(..., description="손익금액")
    sellable_quantity: int = Field(..., description="매도가능수량")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "005930",
                "name": "삼성전자",
                "quantity": 10,
                "avg_price": 67500.0,
                "current_price": 70000,
                "profit_loss_rate": 3.7,
                "profit_loss": 25000,
                "sellable_quantity": 10
            }
        }

class AccountBalance(BaseModel):
    """계좌 잔고 정보 스키마"""
    deposit: int
    stocks: List[Dict[str, Any]] = []
    total_evaluated_price: int = 0
    total_purchase_price: int = 0
    
    @property
    def total_asset(self) -> int:
        """총자산 (예수금 + 주식평가금액)"""
        return self.deposit + self.total_evaluated_price
    
    @property
    def total_profit_loss(self) -> int:
        """총손익금액"""
        return self.total_evaluated_price - self.total_purchase_price
    
    @property
    def total_profit_loss_rate(self) -> float:
        """총손익률"""
        if self.total_purchase_price == 0:
            return 0.0
        return (self.total_profit_loss / self.total_purchase_price) * 100
    
    class Config:
        schema_extra = {
            "example": {
                "deposit": 1000000,
                "stocks": [
                    {
                        "symbol": "005930",
                        "name": "삼성전자",
                        "quantity": 10,
                        "avg_price": 67500.0,
                        "current_price": 70000,
                        "profit_loss_rate": 3.7,
                        "profit_loss": 25000,
                        "sellable_quantity": 10
                    }
                ],
                "total_evaluated_price": 700000,
                "total_purchase_price": 675000
            }
        }

class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    detail: str
    
    class Config:
        schema_extra = {
            "example": {
                "error": "계좌 정보 조회 실패",
                "code": "EXXXXXXX"
            }
        } 