from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from uuid import uuid4

class StrategyParams(BaseModel):
    fast_period: int
    slow_period: int
    signal_period: int

class Strategy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""  # 기본값 추가
    type: str = Field(alias="strategy_type")  # strategy_type을 type으로 매핑
    params: Dict[str, Any]  # parameters를 params로 변경
    stock_code: str
    stock_name: str
    take_profit: float
    stop_loss: float
    investment_amount: float
    is_active: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    backtest_history: List[Dict] = Field(default_factory=list)

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        return d

    class Config:
        populate_by_name = True  # alias 사용 시 필요
        json_schema_extra = {
            "example": {
                "name": "RSI 전략",
                "description": "RSI 지표를 이용한 매매 전략",
                "strategy_type": "RSI",
                "stock_code": "005380",
                "stock_name": "현대차",
                "params": {
                    "period": 14,
                    "overbought": 70,
                    "oversold": 30
                },
                "take_profit": 0.05,
                "stop_loss": 0.03,
                "investment_amount": 1000000,
                "is_active": False
            }
        } 