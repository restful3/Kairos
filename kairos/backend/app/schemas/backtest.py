from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class BacktestRequest(BaseModel):
    """백테스트 요청 모델"""
    strategy_id: str = Field(..., description="전략 ID")
    days: int = Field(90, description="백테스팅 기간(일)")
    initial_capital: float = Field(10000000, description="초기 자본금")
    fee_rate: float = Field(0.00015, description="거래 수수료율")
    use_real_data: bool = Field(True, description="실제 데이터 사용 여부")

class TradeSchema(BaseModel):
    """거래 내역 스키마"""
    date: str
    type: str  # buy, sell
    price: float
    quantity: int
    amount: float
    profit: Optional[float] = None
    profit_pct: Optional[float] = None
    reason: Optional[str] = None

class PortfolioValueSchema(BaseModel):
    """포트폴리오 가치 스키마"""
    date: str
    cash: float
    stock_value: float
    total_value: float
    daily_return: Optional[float] = None

class MetricsSchema(BaseModel):
    """성과 지표 스키마"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    win_count: int
    loss_count: int
    total_trades: int

class BacktestResultSchema(BaseModel):
    """백테스트 결과 스키마"""
    id: Optional[str] = None
    strategy_id: str
    strategy: Dict[str, Any]
    trades: List[Dict[str, Any]]
    portfolio_values: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    backtest_params: Dict[str, Any]
    date: str 