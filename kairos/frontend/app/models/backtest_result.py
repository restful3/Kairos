"""
백테스팅 결과 관련 데이터 모델 정의 모듈입니다.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

class Trade:
    """매매 내역 클래스"""
    
    def __init__(
        self,
        date: datetime,
        type: str,  # 'buy' 또는 'sell'
        price: float,
        shares: int,
        fee: float,
        cash_after: float,
        cost: Optional[float] = None,  # 매수 시
        revenue: Optional[float] = None,  # 매도 시
        profit_pct: Optional[float] = None  # 매도 시
    ):
        """
        매매 내역 초기화
        
        Args:
            date: 거래일
            type: 거래 유형 ('buy', 'sell', 'sell (청산)')
            price: 거래 가격
            shares: 거래 수량
            fee: 수수료
            cash_after: 거래 후 현금
            cost: 매수 비용 (매수 시)
            revenue: 매도 수익 (매도 시)
            profit_pct: 수익률 (매도 시)
        """
        self.date = date
        self.type = type
        self.price = price
        self.shares = shares
        self.fee = fee
        self.cash_after = cash_after
        self.cost = cost
        self.revenue = revenue
        self.profit_pct = profit_pct
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """
        딕셔너리에서 Trade 객체 생성
        
        Args:
            data: 거래 내역 데이터
            
        Returns:
            Trade 객체
        """
        return cls(
            date=data.get('date'),
            type=data.get('type'),
            price=data.get('price'),
            shares=data.get('shares'),
            fee=data.get('fee'),
            cash_after=data.get('cash_after'),
            cost=data.get('cost'),
            revenue=data.get('revenue'),
            profit_pct=data.get('profit_pct')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Trade 객체를 딕셔너리로 변환
        
        Returns:
            딕셔너리 형태의 거래 내역
        """
        result = {
            'date': self.date,
            'type': self.type,
            'price': self.price,
            'shares': self.shares,
            'fee': self.fee,
            'cash_after': self.cash_after
        }
        
        if self.type == 'buy' and self.cost is not None:
            result['cost'] = self.cost
        
        if (self.type == 'sell' or self.type == 'sell (청산)') and self.revenue is not None:
            result['revenue'] = self.revenue
            if self.profit_pct is not None:
                result['profit_pct'] = self.profit_pct
        
        return result


class PortfolioValue:
    """포트폴리오 가치 추적 클래스"""
    
    def __init__(
        self,
        date: datetime,
        cash: float,
        stock_value: float,
        total_value: float,
        position: int
    ):
        """
        포트폴리오 가치 초기화
        
        Args:
            date: 날짜
            cash: 현금
            stock_value: 주식 가치
            total_value: 총 가치
            position: 보유 주식 수
        """
        self.date = date
        self.cash = cash
        self.stock_value = stock_value
        self.total_value = total_value
        self.position = position
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioValue':
        """
        딕셔너리에서 PortfolioValue 객체 생성
        
        Args:
            data: 포트폴리오 가치 데이터
            
        Returns:
            PortfolioValue 객체
        """
        return cls(
            date=data.get('date'),
            cash=data.get('cash'),
            stock_value=data.get('stock_value'),
            total_value=data.get('total_value'),
            position=data.get('position')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        PortfolioValue 객체를 딕셔너리로 변환
        
        Returns:
            딕셔너리 형태의 포트폴리오 가치
        """
        return {
            'date': self.date,
            'cash': self.cash,
            'stock_value': self.stock_value,
            'total_value': self.total_value,
            'position': self.position
        }


class BacktestResult:
    """백테스팅 결과 클래스"""
    
    def __init__(
        self,
        strategy: Dict[str, Any],
        stock_data: pd.DataFrame,
        signals: pd.DataFrame,
        trades: List[Dict[str, Any]],
        portfolio_values: List[Dict[str, Any]],
        metrics: Dict[str, float],
        backtest_params: Dict[str, Any],
        date: str
    ):
        """
        백테스팅 결과 초기화
        
        Args:
            strategy: 백테스팅한 전략 정보
            stock_data: 주가 데이터
            signals: 매매 신호 데이터
            trades: 거래 내역
            portfolio_values: 포트폴리오 가치 추적 데이터
            metrics: 성과 지표
            backtest_params: 백테스팅 파라미터
            date: 백테스팅 실행 일시
        """
        self.strategy = strategy
        self.stock_data = stock_data
        self.signals = signals
        self.trades = trades
        self.portfolio_values = portfolio_values
        self.metrics = metrics
        self.backtest_params = backtest_params
        self.date = date
    
    @property
    def total_return(self) -> float:
        """총 수익률"""
        return self.metrics.get("total_return", 0.0)
    
    @property
    def win_rate(self) -> float:
        """승률"""
        return self.metrics.get("win_rate", 0.0)
    
    @property
    def max_drawdown(self) -> float:
        """최대 낙폭"""
        return self.metrics.get("max_drawdown", 0.0)
    
    @property
    def annualized_return(self) -> float:
        """연간화 수익률"""
        return self.metrics.get("annualized_return", 0.0)
    
    @property
    def volatility(self) -> float:
        """변동성"""
        return self.metrics.get("volatility", 0.0)
    
    @property
    def sharpe_ratio(self) -> float:
        """샤프 비율"""
        return self.metrics.get("sharpe_ratio", 0.0)
    
    @property
    def is_profitable(self) -> bool:
        """수익성 여부"""
        return self.total_return > 0
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """
        요약 정보를 딕셔너리로 반환
        
        Returns:
            요약 정보 딕셔너리
        """
        return {
            "date": self.date,
            "strategy_name": self.strategy.get("name", ""),
            "stock_code": self.strategy.get("stock_code", ""),
            "stock_name": self.strategy.get("stock_name", ""),
            "days": self.backtest_params.get("days", 0),
            "total_return": self.total_return,
            "win_rate": self.win_rate,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "trade_count": len(self.trades) if self.trades else 0
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """
        전체 결과를 딕셔너리로 반환
        
        Returns:
            전체 결과 딕셔너리
        """
        return {
            "strategy": self.strategy,
            "metrics": self.metrics,
            "backtest_params": self.backtest_params,
            "date": self.date,
            "trades": self.trades,
            "portfolio_values": self.portfolio_values
        } 