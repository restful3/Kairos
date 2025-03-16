from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class RiskManagement(BaseModel):
    take_profit: float = Field(..., description="익절 기준 (%)")
    stop_loss: float = Field(..., description="손절 기준 (%)")
    investment_amount: int = Field(..., description="투자 금액 (원)")

class StrategyCreate(BaseModel):
    name: str = Field(..., description="전략 이름")
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str = Field(..., description="종목 이름")
    strategy_type: str = Field(..., description="전략 유형")
    params: Dict = Field(..., description="전략 파라미터")
    take_profit: float = Field(..., description="익절 기준 (%)")
    stop_loss: float = Field(..., description="손절 기준 (%)")
    investment_amount: int = Field(..., description="투자 금액 (원)")

class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, description="전략 이름")
    stock_code: Optional[str] = Field(None, description="종목 코드")
    stock_name: Optional[str] = Field(None, description="종목 이름")
    strategy_type: Optional[str] = Field(None, description="전략 유형")
    params: Optional[Dict] = Field(None, description="전략 파라미터")
    take_profit: Optional[float] = Field(None, description="익절 기준 (%)")
    stop_loss: Optional[float] = Field(None, description="손절 기준 (%)")
    investment_amount: Optional[int] = Field(None, description="투자 금액 (원)")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

class BacktestResult(BaseModel):
    return_rate: float = Field(..., description="수익률 (%)")
    win_rate: float = Field(..., description="승률 (%)")
    max_drawdown: float = Field(..., description="최대 낙폭 (%)")
    trade_count: int = Field(..., description="거래 횟수")
    days: int = Field(..., description="백테스트 기간 (일)")
    params: Dict = Field(..., description="백테스트 시 사용된 파라미터")

class StrategyVersion(BaseModel):
    version: int = Field(..., description="버전 번호")
    date: datetime = Field(..., description="생성 일시")
    params: Dict = Field(..., description="전략 파라미터")

class Strategy(BaseModel):
    id: str = Field(..., description="전략 ID")
    name: str = Field(..., description="전략 이름")
    stock: Dict = Field(..., description="종목 정보")
    type: str = Field(..., description="전략 유형")
    params: Dict = Field(..., description="전략 파라미터")
    risk_management: RiskManagement = Field(..., description="리스크 관리 설정")
    status: Dict = Field(..., description="전략 상태")
    versions: List[StrategyVersion] = Field(default_factory=list, description="버전 히스토리")
    backtest_history: List[BacktestResult] = Field(default_factory=list, description="백테스트 히스토리") 