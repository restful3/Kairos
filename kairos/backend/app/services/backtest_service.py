"""
백테스팅 서비스 모듈입니다.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid
import time

import pandas as pd
import numpy as np

from ..services.stock_service import StockService
from ..services.signal_service import SignalService
from ..database.backtest_store import BacktestStore
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class BacktestService:
    """백테스팅 서비스 클래스"""
    
    def __init__(self, stock_service=None, signal_service=None, backtest_store=None):
        """
        백테스팅 서비스 초기화
        
        Args:
            stock_service: 주식 데이터 서비스 (기본값: None, 자동 생성)
            signal_service: 매매 신호 서비스 (기본값: None, 자동 생성)
            backtest_store: 백테스트 결과 저장소 (기본값: None, 자동 생성)
        """
        self.stock_service = stock_service or StockService()
        self.signal_service = signal_service or SignalService()
        self.backtest_store = backtest_store or BacktestStore()
    
    def run_backtest(self, strategy_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        백테스트 실행

        Args:
            strategy_id: 전략 ID
            params: 백테스트 매개변수

        Returns:
            백테스트 결과
        """
        # 로깅용 ID 생성
        backtest_id = str(uuid.uuid4())
        
        # 전략 가져오기
        from ..services.strategy_service import StrategyService
        strategy_service = StrategyService()
        
        try:
            strategy = strategy_service.get_strategy(strategy_id)
            if not strategy:
                raise ValueError(f"ID가 {strategy_id}인 전략을 찾을 수 없습니다")
            
            # Strategy 객체를 딕셔너리로 변환 (필요한 경우)
            if hasattr(strategy, 'dict'):
                strategy_dict = strategy.dict()
            else:
                # 이미 딕셔너리인 경우
                strategy_dict = strategy
            
            logger.info(f"백테스트 실행 (ID: {backtest_id}) - 전략: '{strategy_dict.get('name', 'Unknown')}'")
            
            # 데이터 가져오기
            stock_code = strategy_dict.get('stock_code')
            if not stock_code:
                raise ValueError("전략에 종목 코드가 없습니다")
            
            days = params.get('days', 30)
            
            # 실제 또는 모의 데이터 사용 결정
            use_real_data = params.get('use_real_data', False)
            
            # 시작 자본금
            initial_capital = float(params.get('initial_capital', 
                                              strategy_dict.get('investment_amount', 1000000)))
            
            # 수수료
            fee_rate = float(params.get('fee_rate', 0.00015))
            
            # 데이터 가져오기
            data = self._get_stock_data(stock_code, days, use_real_data)
            if data.empty:
                raise ValueError(f"종목 '{stock_code}'에 대한 데이터를 가져올 수 없습니다")
            
            # 성능 측정 시작
            start_time = time.time()
            
            # 백테스트 실행
            strategy_type = strategy_dict.get('type')
            strategy_params = strategy_dict.get('params', {})
            
            results = self._execute_backtest(
                strategy_type=strategy_type,
                strategy_params=strategy_params,
                data=data,
                initial_capital=initial_capital,
                fee_rate=fee_rate,
                backtest_id=backtest_id
            )
            
            # 성능 측정 종료
            execution_time = time.time() - start_time
            logger.info(f"백테스트 실행 완료 (ID: {backtest_id}) - 소요 시간: {execution_time:.2f}초")
            
            # 결과 처리
            result = self._process_backtest_results(results, backtest_id, {
                "strategy_id": strategy_id,
                "days": days,
                "initial_capital": initial_capital,
                "fee_rate": fee_rate,
                "use_real_data": use_real_data
            })
            
            # 전략에 백테스트 결과 추가
            self._add_backtest_to_strategy(strategy_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"백테스트 실행 중 오류 발생: {str(e)}")
            # 오류 정보를 클라이언트에게 전달
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"백테스팅 실행 중 오류 발생: {str(e)}"
            )
    
    def get_backtest_result(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """
        백테스트 결과 조회
        
        Args:
            backtest_id: 백테스트 ID
            
        Returns:
            백테스트 결과 또는 None
        """
        return self.backtest_store.get(backtest_id)
    
    def get_backtest_results(self, strategy_id: str) -> List[Dict[str, Any]]:
        """
        전략의 백테스트 결과 목록 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            백테스트 결과 목록
        """
        return self.backtest_store.get_by_strategy(strategy_id)
    
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
    
    def _generate_signals(self, stock_data: pd.DataFrame, strategy: Dict[str, Any]) -> pd.DataFrame:
        """
        매매 신호 생성
        
        Args:
            stock_data: 주가 데이터
            strategy: 매매 전략
            
        Returns:
            신호가 추가된 DataFrame
        """
        return self.signal_service.generate_signals(stock_data, strategy)
    
    def _simulate_trades(
        self, 
        signals: pd.DataFrame, 
        initial_capital: float, 
        fee_rate: float,
        investment_amount: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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
        
        # 신호 확인 로깅
        buy_signals = (signals['position'] == 1).sum()
        sell_signals = (signals['position'] == -1).sum()
        logger.info(f"시뮬레이션 시작: 총 {len(signals)}일 중 매수 신호 {buy_signals}회, 매도 신호 {sell_signals}회")
        
        # 각 날짜별로 시뮬레이션
        for idx, row in signals.iterrows():
            date = row.name if isinstance(row.name, datetime) else pd.to_datetime(row.name)
            close_price = row['close']
            position_signal = row['position']
            
            # 포트폴리오 가치 계산
            current_value = cash + position * close_price
            portfolio_values.append({
                "date": date,
                "cash": cash,
                "holdings": position * close_price,
                "total_value": current_value
            })
            
            # 매수 신호 - 초기 매수 또는 추가 매수
            if position_signal == 1 and cash >= close_price:  # 현금이 충분한 경우에만 매수
                # 투자 금액 계산 (가용 현금의 50%까지만 사용)
                available_percentage = 0.5  # 가용 현금의 50%
                amount_to_invest = min(cash * available_percentage, investment_amount)
                
                # 수수료 고려하여 매수 수량 계산
                shares_to_buy = int(amount_to_invest / (close_price * (1 + fee_rate)))
                
                if shares_to_buy > 0:
                    # 매수 비용 계산
                    cost = shares_to_buy * close_price
                    fee = cost * fee_rate
                    total_cost = cost + fee
                    
                    # 현금 감소, 포지션 증가
                    cash -= total_cost
                    position += shares_to_buy
                    
                    # 거래 기록 추가
                    trades.append({
                        "date": date,
                        "type": "buy",
                        "price": close_price,
                        "quantity": shares_to_buy,
                        "amount": total_cost,
                        "fee": fee,
                        "reason": "RSI 매수 신호"
                    })
                    
                    # 평균 진입 가격 계산
                    entry_price = (entry_price * (position - shares_to_buy) + cost) / position if position > 0 else 0
                    
                    logger.info(f"매수 실행: {date}, 가격: {close_price}, 수량: {shares_to_buy}, 금액: {total_cost}")
            
            # 매도 신호
            elif (position_signal == -1 or row.get('force_sell', False)) and position > 0:
                # 매도 금액 계산
                proceeds = position * close_price
                fee = proceeds * fee_rate
                total_proceeds = proceeds - fee
                
                # 수익률 계산
                profit = total_proceeds - (position * entry_price * (1 + fee_rate))
                profit_pct = profit / (position * entry_price * (1 + fee_rate)) * 100
                
                # 현금 증가, 포지션 청산
                cash += total_proceeds
                
                # 거래 기록 추가
                trades.append({
                    "date": date,
                    "type": "sell",
                    "price": close_price,
                    "quantity": position,
                    "amount": total_proceeds,
                    "fee": fee,
                    "profit": profit,
                    "profit_pct": profit_pct,
                    "reason": "매도 신호" if position_signal == -1 else "강제 매도"
                })
                
                logger.info(f"[{date.date()}] 매도: {position}주 @ {close_price:,.0f}원 (수익률: {profit_pct:.2f}%)")
                
                position = 0
                entry_price = 0.0
            
            # 매도 체결 후 포트폴리오 가치 갱신 (수정된 현금 및 포지션 반영)
            current_value = cash + position * close_price
        
        # 시뮬레이션이 끝났을 때 아직 주식을 보유하고 있으면 청산
        if position > 0:
            last_date = signals.index[-1]
            if isinstance(last_date, pd._libs.tslibs.timestamps.Timestamp):
                last_date = last_date.to_pydatetime()
            
            close_price = signals.iloc[-1]['close']
            
            # 매도 수익/손실 계산
            gross_sale = position * close_price
            fee = gross_sale * fee_rate
            net_sale = gross_sale - fee
            
            # 매도 처리
            cash += net_sale
            stock_value = 0
            
            # 거래 기록 추가
            trades.append({
                "date": last_date,
                "type": "sell (청산)",
                "price": close_price,
                "quantity": position,
                "amount": gross_sale,
                "fee": fee,
                "reason": "시뮬레이션 종료"
            })
            
            position = 0
            
            logger.info(f"[{last_date}] 보유 주식 청산: {position}주 @ {close_price:,.0f}원 (총 {net_sale:,.0f}원)")
        
        return trades, portfolio_values
    
    def _calculate_metrics(
        self, 
        portfolio_values: List[Dict[str, Any]], 
        trades: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        성과 지표 계산
        
        Args:
            portfolio_values: 포트폴리오 가치 추적 데이터
            trades: 거래 내역
            
        Returns:
            성과 지표 딕셔너리
        """
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
        
        # 초기 및 최종 포트폴리오 가치
        initial_value = portfolio_values[0]["total_value"]
        final_value = portfolio_values[-1]["total_value"]
        
        # 총 수익률
        total_return = ((final_value / initial_value) - 1) * 100
        
        # 일별 수익률
        daily_returns = [p.get("daily_return", 0) for p in portfolio_values]
        daily_returns = [r for r in daily_returns if r is not None]
        
        # 최대 낙폭
        peak = portfolio_values[0]["total_value"]
        max_drawdown = 0.0
        
        for value in portfolio_values:
            total_value = value["total_value"]
            
            if total_value > peak:
                peak = total_value
            else:
                drawdown = (peak - total_value) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        # 운용 기간
        days = len(portfolio_values)
        
        # 연간화 수익률
        if days > 1:
            annualized_return = ((final_value / initial_value) ** (365 / days) - 1) * 100
        else:
            annualized_return = 0.0
        
        # 변동성
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0.0
        
        # 샤프 비율 (무위험 수익률 0% 가정)
        sharpe_ratio = (annualized_return / 100) / (volatility / 100) if volatility > 0 else 0.0
        
        # 승률 계산
        win_count = 0
        loss_count = 0
        
        for trade in trades:
            if trade["type"] in ['sell', 'sell (청산)'] and "profit_pct" in trade:
                if trade["profit_pct"] > 0:
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
    
    def _execute_backtest(
        self,
        strategy_type: str,
        strategy_params: Dict[str, Any],
        data: pd.DataFrame,
        initial_capital: float,
        fee_rate: float,
        backtest_id: str
    ) -> Dict[str, Any]:
        """
        백테스트 실행
        
        Args:
            strategy_type: 전략 유형
            strategy_params: 전략 매개변수
            data: 주가 데이터
            initial_capital: 초기 자본금
            fee_rate: 거래 수수료율
            backtest_id: 백테스트 ID
            
        Returns:
            백테스트 결과
        """
        # 전략 정보 설정
        strategy_info = {
            "type": strategy_type,
            "params": strategy_params
        }
        
        # 매매 신호 생성
        signals = self._generate_signals(data, strategy_info)
        logger.info(f"매매 신호 생성 완료 (ID: {backtest_id})")
        
        # 매매 시뮬레이션
        trades, portfolio_values = self._simulate_trades(
            signals=signals,
            initial_capital=initial_capital,
            fee_rate=fee_rate,
            investment_amount=strategy_params.get('investment_amount', initial_capital)
        )
        logger.info(f"매매 시뮬레이션 완료 (ID: {backtest_id}) - {len(trades)}건의 거래")
        
        # 성과 지표 계산
        metrics = self._calculate_metrics(portfolio_values, trades)
        
        return {
            "signals": signals,
            "trades": trades,
            "portfolio_values": portfolio_values,
            "metrics": metrics
        }
    
    def _process_backtest_results(
        self,
        results: Dict[str, Any],
        backtest_id: str,
        backtest_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        백테스트 결과 처리
        
        Args:
            results: 백테스트 실행 결과
            backtest_id: 백테스트 ID
            backtest_params: 백테스트 매개변수
            
        Returns:
            처리된 백테스트 결과
        """
        # DataFrame을 리스트로 변환
        signals = results.get("signals", pd.DataFrame())
        signals_list = []
        
        if not signals.empty:
            # 인덱스를 날짜 문자열로 변환
            signals_df = signals.reset_index()
            signals_df['date'] = signals_df['index'].apply(
                lambda x: x.isoformat() if isinstance(x, datetime) else pd.to_datetime(x).isoformat()
            )
            signals_df = signals_df.drop('index', axis=1)
            
            # 데이터프레임을 레코드 리스트로 변환
            signals_list = signals_df.to_dict('records')
        
        # 포트폴리오 값 가져오기
        portfolio_values = results.get("portfolio_values", [])
        
        # Timestamp 객체를 문자열로 변환
        for pv in portfolio_values:
            if 'date' in pv and not isinstance(pv['date'], str):
                pv['date'] = pv['date'].isoformat() if hasattr(pv['date'], 'isoformat') else str(pv['date'])
        
        # 거래 내역 가져오기
        trades = results.get("trades", [])
        
        # Timestamp 객체를 문자열로 변환
        for trade in trades:
            if 'date' in trade and not isinstance(trade['date'], str):
                trade['date'] = trade['date'].isoformat() if hasattr(trade['date'], 'isoformat') else str(trade['date'])
        
        # 결과 구성
        result = {
            "id": backtest_id,
            "strategy_id": backtest_params.get("strategy_id", ""),
            "date": datetime.now().isoformat(),
            "signals": signals_list,
            "trades": trades,
            "portfolio_values": portfolio_values,
            "metrics": results.get("metrics", {}),
            "backtest_params": backtest_params
        }
        
        # 결과 저장
        self.backtest_store.save(result)
        logger.info(f"백테스트 결과 저장 완료 (ID: {backtest_id})")
        
        return result
    
    def _add_backtest_to_strategy(self, strategy_id: str, result: Dict[str, Any]) -> None:
        """
        전략에 백테스트 결과 추가
        
        Args:
            strategy_id: 전략 ID
            result: 백테스트 결과
        """
        from ..services.strategy_service import StrategyService
        strategy_service = StrategyService()
        
        try:
            # 전략 가져오기
            strategy = strategy_service.get_strategy(strategy_id)
            if not strategy:
                logger.warning(f"ID가 {strategy_id}인 전략을 찾을 수 없어 백테스트 결과를 추가할 수 없습니다")
                return
            
            # Strategy 객체를 딕셔너리로 변환 (필요한 경우)
            if hasattr(strategy, 'dict') and callable(getattr(strategy, 'dict')):
                strategy_dict = strategy.dict()
            else:
                # 이미 딕셔너리인 경우
                strategy_dict = strategy
            
            # 결과 요약 생성
            metrics = result.get("metrics", {})
            backtest_params = result.get("backtest_params", {})
            
            summary = {
                "id": result.get("id"),
                "date": result.get("date"),
                "params": {
                    "period": f"최근 {backtest_params.get('days', 0)}일",
                    "days": backtest_params.get("days", 0),
                    "initial_capital": backtest_params.get("initial_capital", 0),
                    "fee_rate": backtest_params.get("fee_rate", 0),
                    "use_real_data": backtest_params.get("use_real_data", False)
                },
                "metrics": {
                    "total_return": metrics.get("total_return", 0),
                    "annualized_return": metrics.get("annualized_return", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "volatility": metrics.get("volatility", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0)
                }
            }
            
            # 백테스트 히스토리 추가 준비
            if "backtest_history" not in strategy_dict:
                strategy_dict["backtest_history"] = []
                
            strategy_dict["backtest_history"].append(summary)
            
            # 전략 업데이트
            strategy_service.update_strategy(strategy_id, strategy_dict)
            logger.info(f"전략 '{strategy_dict.get('name', 'Unknown')}'에 백테스트 결과 추가: {summary['date']}")
            
        except Exception as e:
            logger.error(f"백테스트 결과 추가 중 오류 발생: {e}") 