"""
백테스팅 서비스 모듈입니다.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

from ..models.strategy import TradingStrategy
from ..models.backtest_result import BacktestResult, Trade, PortfolioValue
from .stock_service import StockService
from .signal_service import SignalService

logger = logging.getLogger(__name__)

class BacktestService:
    """백테스팅 서비스 클래스"""
    
    def __init__(self, stock_service: Optional[StockService] = None, signal_service: Optional[SignalService] = None):
        """
        백테스팅 서비스 초기화
        
        Args:
            stock_service: 주식 데이터 서비스 (기본값: None, 자동 생성)
            signal_service: 매매 신호 서비스 (기본값: None, 자동 생성)
        """
        self.stock_service = stock_service if stock_service else StockService()
        self.signal_service = signal_service if signal_service else SignalService()
    
    def run_backtest(
        self, 
        strategy: TradingStrategy, 
        days: int = 90, 
        initial_capital: float = 10000000, 
        fee_rate: float = 0.00015, 
        simplified: bool = False,
        use_real_data: bool = False
    ) -> BacktestResult:
        """
        백테스팅 실행
        
        Args:
            strategy: 백테스팅할 전략
            days: 백테스팅 기간 (일)
            initial_capital: 초기 자본금
            fee_rate: 거래 수수료율
            simplified: 간소화된 결과 반환 여부
            use_real_data: 실제 데이터 사용 여부
            
        Returns:
            백테스팅 결과
        """
        logger.info(f"'{strategy.name}' 전략 백테스팅 시작 ({days}일)")
        
        try:
            # 종목 코드 유효성 검사
            self._validate_stock_code(strategy.stock_code)
            
            # 주가 데이터 가져오기
            stock_data = self._get_stock_data(strategy.stock_code, days, use_real_data)
            logger.info(f"주가 데이터 로드 완료: {len(stock_data)}일")
            
            # 매매 신호 생성
            signals = self._generate_trade_signals(strategy, stock_data)
            logger.info(f"매매 신호 생성 완료")
            
            # 매매 시뮬레이션
            trades, portfolio_values = self._simulate_trades(
                signals, initial_capital, fee_rate, strategy.investment_amount
            )
            logger.info(f"매매 시뮬레이션 완료: {len(trades)}건의 거래")
            
            # 성과 지표 계산
            metrics = self._calculate_performance_metrics(portfolio_values, trades)
            logger.info(f"성과 지표 계산 완료: 총 수익률 {metrics['total_return']:.2f}%")
            
            # 백테스팅 결과 생성
            result = BacktestResult(
                strategy=strategy.to_dict(),
                stock_data=stock_data,
                signals=signals,
                trades=[t.to_dict() for t in trades],
                portfolio_values=[p.to_dict() for p in portfolio_values],
                metrics=metrics,
                backtest_params={
                    "days": days,
                    "initial_capital": initial_capital,
                    "fee_rate": fee_rate,
                    "simplified": simplified,
                    "use_real_data": use_real_data
                },
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # 백테스팅 결과 저장
            self.save_backtest_result(strategy, result)
            logger.info(f"백테스팅 결과 저장 완료")
            
            return result
        
        except Exception as e:
            logger.error(f"백테스팅 실행 중 오류 발생: {e}")
            raise
    
    def _validate_stock_code(self, stock_code: str) -> None:
        """
        종목 코드 유효성 검사
        
        Args:
            stock_code: 종목 코드
            
        Raises:
            ValueError: 종목 코드가 유효하지 않은 경우
        """
        if not stock_code:
            raise ValueError("종목 코드가 필요합니다")
        
        # 한국 주식 종목 코드는 보통 6자리 숫자
        if not re.match(r'^\d{6}$', stock_code):
            raise ValueError(f"유효하지 않은 종목 코드 형식입니다: {stock_code}")
    
    def _get_stock_data(self, stock_code: str, days: int, use_real_data: bool) -> pd.DataFrame:
        """
        주가 데이터 가져오기
        
        Args:
            stock_code: 종목 코드
            days: 데이터 일수
            use_real_data: 실제 데이터 사용 여부
            
        Returns:
            주가 데이터 DataFrame
        """
        return self.stock_service.get_stock_price_data(stock_code, days, use_real_data)
    
    def _generate_trade_signals(self, strategy: TradingStrategy, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        매매 신호 생성
        
        Args:
            strategy: 매매 전략
            stock_data: 주가 데이터
            
        Returns:
            신호가 추가된 DataFrame
        """
        return self.signal_service.generate_signals(strategy, stock_data)
    
    def _simulate_trades(
        self, 
        signals: pd.DataFrame, 
        initial_capital: float, 
        fee_rate: float,
        investment_amount: Optional[float] = None
    ) -> Tuple[List[Trade], List[PortfolioValue]]:
        """
        매매 시뮬레이션
        
        Args:
            signals: 매매 신호가 포함된 DataFrame
            initial_capital: 초기 자본금
            fee_rate: 거래 수수료율
            investment_amount: 투자 금액 (None인 경우 전체 자본금)
            
        Returns:
            (거래 내역 리스트, 포트폴리오 가치 추적 리스트)
        """
        if not investment_amount or investment_amount <= 0:
            investment_amount = initial_capital
        
        # 초기 설정
        cash = initial_capital
        position = 0  # 보유 주식 수
        trades = []
        portfolio_values = []
        entry_price = 0.0
        
        # 각 날짜에 대해 거래 시뮬레이션
        for i, day in signals.iterrows():
            date = day['Date']
            current_price = day['Close']
            
            # 주식 가치 계산
            stock_value = position * current_price
            total_value = cash + stock_value
            
            # 포트폴리오 가치 추적
            portfolio_values.append(PortfolioValue(
                date=date,
                cash=cash,
                stock_value=stock_value,
                total_value=total_value,
                position=position
            ))
            
            # 매매 신호 확인
            signal = day['position']
            
            # 매수 신호 (현재 포지션이 없을 때만)
            if signal == 1 and position == 0:
                # 투자 금액 계산 (최대 가용 현금까지)
                invest = min(investment_amount, cash)
                
                # 수수료 고려
                fee = invest * fee_rate
                available = invest - fee
                
                # 최대 매수 가능 수량 (정수)
                shares_to_buy = int(available / current_price)
                
                if shares_to_buy > 0:
                    # 실제 투자 금액
                    actual_cost = shares_to_buy * current_price
                    actual_fee = actual_cost * fee_rate
                    total_cost = actual_cost + actual_fee
                    
                    # 거래 실행
                    cash -= total_cost
                    position += shares_to_buy
                    entry_price = current_price
                    
                    # 거래 내역 기록
                    trades.append(Trade(
                        date=date,
                        type='buy',
                        price=current_price,
                        shares=shares_to_buy,
                        fee=actual_fee,
                        cash_after=cash,
                        cost=total_cost
                    ))
                    
                    logger.info(f"[{date.strftime('%Y-%m-%d')}] 매수: {shares_to_buy}주 @ {current_price:.2f}원 "
                               f"(비용: {total_cost:.2f}원, 수수료: {actual_fee:.2f}원)")
            
            # 매도 신호 (포지션이 있을 때만)
            elif signal == -1 and position > 0:
                # 매도 금액
                revenue = position * current_price
                fee = revenue * fee_rate
                net_revenue = revenue - fee
                
                # 수익률 계산
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                
                # 거래 실행
                cash += net_revenue
                
                # 거래 내역 기록
                trades.append(Trade(
                    date=date,
                    type='sell',
                    price=current_price,
                    shares=position,
                    fee=fee,
                    cash_after=cash,
                    revenue=net_revenue,
                    profit_pct=profit_pct
                ))
                
                logger.info(f"[{date.strftime('%Y-%m-%d')}] 매도: {position}주 @ {current_price:.2f}원 "
                           f"(수익: {net_revenue:.2f}원, 수익률: {profit_pct:.2f}%, 수수료: {fee:.2f}원)")
                
                # 포지션 초기화
                position = 0
                entry_price = 0.0
        
        # 마지막 날에 포지션이 남아있으면 청산
        if position > 0:
            last_day = signals.iloc[-1]
            date = last_day['Date']
            current_price = last_day['Close']
            
            # 매도 금액
            revenue = position * current_price
            fee = revenue * fee_rate
            net_revenue = revenue - fee
            
            # 수익률 계산
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            
            # 거래 실행
            cash += net_revenue
            
            # 거래 내역 기록
            trades.append(Trade(
                date=date,
                type='sell (청산)',
                price=current_price,
                shares=position,
                fee=fee,
                cash_after=cash,
                revenue=net_revenue,
                profit_pct=profit_pct
            ))
            
            logger.info(f"[{date.strftime('%Y-%m-%d')}] 청산: {position}주 @ {current_price:.2f}원 "
                       f"(수익: {net_revenue:.2f}원, 수익률: {profit_pct:.2f}%, 수수료: {fee:.2f}원)")
            
            # 포지션 초기화
            position = 0
            
            # 마지막 포트폴리오 가치 업데이트
            portfolio_values.append(PortfolioValue(
                date=date,
                cash=cash,
                stock_value=0,
                total_value=cash,
                position=0
            ))
        
        return trades, portfolio_values
    
    def _calculate_performance_metrics(
        self, 
        portfolio_values: List[PortfolioValue], 
        trades: List[Trade]
    ) -> Dict[str, float]:
        """
        성과 지표 계산
        
        Args:
            portfolio_values: 포트폴리오 가치 추적 리스트
            trades: 거래 내역 리스트
            
        Returns:
            성과 지표 딕셔너리
        """
        # 포트폴리오 가치가 없는 경우
        if not portfolio_values:
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "win_count": 0,
                "loss_count": 0,
                "total_trades": 0
            }
        
        # 초기/최종 포트폴리오 가치
        initial_value = portfolio_values[0].total_value
        final_value = portfolio_values[-1].total_value
        
        # 총 수익률
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        # 일별 수익률 계산
        daily_returns = []
        max_value = initial_value
        max_drawdown = 0.0
        
        for i in range(1, len(portfolio_values)):
            prev_value = portfolio_values[i-1].total_value
            curr_value = portfolio_values[i].total_value
            
            # 일별 수익률
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)
            
            # 최대 낙폭 갱신
            if curr_value > max_value:
                max_value = curr_value
            else:
                drawdown = (max_value - curr_value) / max_value * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        # 연간화 수익률
        days = len(portfolio_values)
        if days > 1:
            annualized_return = ((final_value / initial_value) ** (365 / days) - 1) * 100
        else:
            annualized_return = 0.0
        
        # 변동성
        volatility = np.std(daily_returns) * np.sqrt(252) * 100 if daily_returns else 0.0
        
        # 샤프 비율 (무위험 수익률 0% 가정)
        sharpe_ratio = (annualized_return / 100) / (volatility / 100) if volatility > 0 else 0.0
        
        # 승률 계산
        win_count = 0
        loss_count = 0
        
        for trade in trades:
            if trade.type in ['sell', 'sell (청산)'] and hasattr(trade, 'profit_pct'):
                if trade.profit_pct > 0:
                    win_count += 1
                else:
                    loss_count += 1
        
        total_trades = win_count + loss_count
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
        
        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "win_count": win_count,
            "loss_count": loss_count,
            "total_trades": total_trades
        }
    
    def save_backtest_result(self, strategy: TradingStrategy, result: BacktestResult) -> None:
        """
        백테스팅 결과 저장
        
        Args:
            strategy: 전략 객체
            result: 백테스팅 결과
        """
        # 결과 요약 생성
        summary = result.to_summary_dict()
        
        # 전략에 백테스트 결과 추가
        strategy.add_backtest_result(summary)
        
        logger.info(f"전략 '{strategy.name}'에 백테스트 결과 추가: {summary['date']}")
    
    def get_last_backtest_result(self, strategy: TradingStrategy) -> Optional[Dict[str, Any]]:
        """
        마지막 백테스트 결과 가져오기
        
        Args:
            strategy: 전략 객체
            
        Returns:
            마지막 백테스트 결과 또는 None
        """
        return strategy.last_backtest_result() 