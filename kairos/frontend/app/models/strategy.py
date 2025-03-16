import datetime
from typing import Dict, List, Union, Optional, Any

class TradingStrategy:
    """매매 전략 클래스"""
    
    def __init__(
        self,
        name: str,
        stock_code: str,
        stock_name: str,
        strategy_type: str,
        params: Dict[str, Any],
        take_profit: float = 5.0,
        stop_loss: float = -5.0,
        investment_amount: int = 100000,
        is_active: bool = False,
        created_at: Optional[str] = None,
        backtest_history: Optional[List[Dict[str, Any]]] = None
    ):
        """
        매매 전략 객체 초기화
        
        Args:
            name: 전략 이름
            stock_code: 종목 코드
            stock_name: 종목 이름
            strategy_type: 전략 유형 (예: "이동평균선 교차 전략")
            params: 전략별 매개변수
            take_profit: 목표 수익률(%)
            stop_loss: 손절 손실률(%, 음수 값)
            investment_amount: 1회 투자금액(원)
            is_active: 전략 활성화 상태
            created_at: 생성일시(문자열)
            backtest_history: 백테스트 이력
        """
        self.name = name
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.strategy_type = strategy_type
        self.params = params
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.investment_amount = investment_amount
        self.is_active = is_active
        
        # 생성일시가 없으면 현재 시간으로 설정
        if created_at is None:
            self.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.created_at = created_at
            
        # 백테스트 이력 초기화
        self.backtest_history = backtest_history or []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingStrategy':
        """딕셔너리에서 전략 객체 생성
        
        Args:
            data: 전략 정보가 담긴 딕셔너리
            
        Returns:
            생성된 전략 객체
        """
        return cls(
            name=data.get("name", ""),
            stock_code=data.get("stock_code", ""),
            stock_name=data.get("stock_name", ""),
            strategy_type=data.get("strategy_type", ""),
            params=data.get("params", {}),
            take_profit=data.get("take_profit", 5.0),
            stop_loss=data.get("stop_loss", -5.0),
            investment_amount=data.get("investment_amount", 100000),
            is_active=data.get("is_active", False),
            created_at=data.get("created_at"),
            backtest_history=data.get("backtest_history", [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """전략 객체를 딕셔너리로 변환
        
        Returns:
            전략 정보가 담긴 딕셔너리
        """
        return {
            "name": self.name,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "strategy_type": self.strategy_type,
            "params": self.params,
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "investment_amount": self.investment_amount,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "backtest_history": self.backtest_history
        }
    
    def add_backtest_result(self, result: Dict[str, Any]) -> None:
        """백테스트 결과를 이력에 추가
        
        Args:
            result: 백테스트 결과 정보
        """
        backtest_entry = {
            "date": result.get("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "return": result.get("metrics", {}).get("total_return", 0.0),
            "win_rate": result.get("metrics", {}).get("win_rate", 0.0),
            "max_drawdown": result.get("metrics", {}).get("max_drawdown", 0.0),
            "simplified": result.get("simplified", True),
            "days": result.get("backtest_params", {}).get("days", 30),
            "use_real_data": result.get("use_real_data", True)
        }
        
        self.backtest_history.append(backtest_entry)
    
    def toggle_active_status(self) -> None:
        """전략의 활성화 상태를 토글합니다."""
        self.is_active = not self.is_active
    
    @property
    def last_backtest_result(self) -> Optional[Dict[str, Any]]:
        """가장 최근 백테스트 결과를 반환합니다.
        
        Returns:
            최근 백테스트 결과 또는 None
        """
        if not self.backtest_history:
            return None
        
        return self.backtest_history[-1] 