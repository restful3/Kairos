"""
매매 신호 생성 서비스 모듈입니다.
"""
import logging
from typing import Dict, Any, Callable, Optional

import pandas as pd
import numpy as np
import talib

from ..models.strategy import TradingStrategy

logger = logging.getLogger(__name__)

class SignalService:
    """매매 신호 생성 서비스 클래스"""
    
    def __init__(self):
        """매매 신호 생성 서비스 초기화"""
        # 전략 유형별 신호 생성 함수 매핑
        self.signal_generators = {
            "이동평균 교차": self._generate_ma_cross_signals,
            "RSI": self._generate_rsi_signals,
            "가격 돌파": self._generate_price_breakout_signals
        }
    
    def generate_signals(self, strategy: TradingStrategy, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        전략에 따른 매매 신호 생성
        
        Args:
            strategy: 매매 전략
            stock_data: 주가 데이터 DataFrame
            
        Returns:
            신호가 추가된 DataFrame
        """
        if not isinstance(stock_data, pd.DataFrame) or stock_data.empty:
            raise ValueError("유효한 주가 데이터가 필요합니다")
        
        # 전략 유형 확인
        strategy_type = strategy.strategy_type
        
        if strategy_type not in self.signal_generators:
            raise ValueError(f"지원하지 않는 전략 유형입니다: {strategy_type}")
        
        # 해당 전략의 신호 생성 함수 호출
        logger.info(f"'{strategy.name}' 전략({strategy_type})의 매매 신호 생성 중...")
        signals_df = self.signal_generators[strategy_type](stock_data, strategy.params)
        
        # 이익실현/손절매 조건 추가
        logger.info(f"이익실현/손절매 조건 적용 중 (이익실현: {strategy.take_profit}%, 손절매: {strategy.stop_loss}%)")
        signals_df = self._apply_exit_conditions(signals_df, strategy.take_profit, strategy.stop_loss)
        
        return signals_df
    
    def _generate_ma_cross_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        이동평균 교차 전략 신호 생성
        
        Args:
            data: 주가 데이터
            params: 전략 파라미터 (fast_period, slow_period, signal_period)
            
        Returns:
            신호가 추가된 DataFrame
        """
        # 파라미터 가져오기
        fast_period = params.get('fast_period', 5)
        slow_period = params.get('slow_period', 20)
        signal_period = params.get('signal_period', 9)
        
        # 데이터 복사
        signals = data.copy()
        
        # 이동평균 계산
        signals['fast_ma'] = signals['Close'].rolling(window=fast_period).mean()
        signals['slow_ma'] = signals['Close'].rolling(window=slow_period).mean()
        
        # MACD 계산 (선택적)
        if signal_period > 0:
            signals['macd'], signals['macd_signal'], signals['macd_hist'] = talib.MACD(
                signals['Close'], 
                fastperiod=fast_period, 
                slowperiod=slow_period, 
                signalperiod=signal_period
            )
        
        # 신호 생성 (기본: 빠른 이동평균이 느린 이동평균을 상향 돌파 -> 매수, 하향 돌파 -> 매도)
        signals['position'] = 0  # 0: 중립, 1: 매수, -1: 매도
        
        # 크로스오버 감지
        signals['fast_gt_slow'] = signals['fast_ma'] > signals['slow_ma']
        signals['crossover'] = signals['fast_gt_slow'].astype(int).diff()
        
        # 매수/매도 신호 설정
        signals.loc[signals['crossover'] > 0, 'position'] = 1  # 골든 크로스 (매수)
        signals.loc[signals['crossover'] < 0, 'position'] = -1  # 데드 크로스 (매도)
        
        # NaN 값을 가진 행 제거 (처음 몇 행은 이동평균을 계산할 수 없음)
        signals = signals.dropna()
        
        logger.info(f"이동평균 교차 신호 생성 완료 (빠른 기간: {fast_period}, 느린 기간: {slow_period})")
        return signals
    
    def _generate_rsi_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        RSI 전략 신호 생성
        
        Args:
            data: 주가 데이터
            params: 전략 파라미터 (period, overbought, oversold)
            
        Returns:
            신호가 추가된 DataFrame
        """
        # 파라미터 가져오기
        period = params.get('period', 14)
        overbought = params.get('overbought', 70)
        oversold = params.get('oversold', 30)
        
        # 데이터 복사
        signals = data.copy()
        
        # RSI 계산
        signals['rsi'] = talib.RSI(signals['Close'], timeperiod=period)
        
        # 신호 생성
        signals['position'] = 0  # 0: 중립, 1: 매수, -1: 매도
        
        # 과매도 상태에서 매수, 과매입 상태에서 매도
        # 직접 비교하면 같은 신호가 연속해서 나올 수 있으므로 상태 변화 감지
        signals['oversold'] = signals['rsi'] < oversold
        signals['overbought'] = signals['rsi'] > overbought
        
        # 과매도 상태에서 회복될 때 매수
        signals['oversold_exit'] = (signals['oversold'].shift(1) == True) & (signals['oversold'] == False)
        signals.loc[signals['oversold_exit'], 'position'] = 1
        
        # 과매입 상태에서 하락할 때 매도
        signals['overbought_exit'] = (signals['overbought'].shift(1) == True) & (signals['overbought'] == False)
        signals.loc[signals['overbought_exit'], 'position'] = -1
        
        # NaN 값을 가진 행 제거
        signals = signals.dropna()
        
        logger.info(f"RSI 신호 생성 완료 (기간: {period}, 과매입: {overbought}, 과매도: {oversold})")
        return signals
    
    def _generate_price_breakout_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        가격 돌파 전략 신호 생성
        
        Args:
            data: 주가 데이터
            params: 전략 파라미터 (lookback_period, breakout_type)
            
        Returns:
            신호가 추가된 DataFrame
        """
        # 파라미터 가져오기
        lookback_period = params.get('lookback_period', 20)
        breakout_type = params.get('breakout_type', '신고가')  # '신고가' 또는 '신저가'
        
        # 데이터 복사
        signals = data.copy()
        
        # 이전 고가/저가 계산
        signals['max_lookback'] = signals['High'].rolling(window=lookback_period).max().shift(1)
        signals['min_lookback'] = signals['Low'].rolling(window=lookback_period).min().shift(1)
        
        # 신호 생성
        signals['position'] = 0  # 0: 중립, 1: 매수, -1: 매도
        
        if breakout_type == '신고가':
            # 신고가 돌파 시 매수, 신저가 하회 시 매도
            signals.loc[signals['High'] > signals['max_lookback'], 'position'] = 1
            signals.loc[signals['Low'] < signals['min_lookback'], 'position'] = -1
        else:  # '신저가'
            # 신저가 하회 시 매수(역추세), 신고가 돌파 시 매도(역추세)
            signals.loc[signals['Low'] < signals['min_lookback'], 'position'] = 1
            signals.loc[signals['High'] > signals['max_lookback'], 'position'] = -1
        
        # 동일한 날에 매수/매도 신호가 모두 발생하면 중립으로 설정
        signals.loc[(signals['High'] > signals['max_lookback']) & 
                    (signals['Low'] < signals['min_lookback']), 'position'] = 0
        
        # NaN 값을 가진 행 제거
        signals = signals.dropna()
        
        logger.info(f"가격 돌파 신호 생성 완료 (관찰 기간: {lookback_period}, 돌파 유형: {breakout_type})")
        return signals
    
    def _apply_exit_conditions(self, signals: pd.DataFrame, take_profit: float, stop_loss: float) -> pd.DataFrame:
        """
        이익실현/손절매 조건 적용
        
        Args:
            signals: 신호가 포함된 DataFrame
            take_profit: 이익실현 목표 비율 (%)
            stop_loss: 손절매 목표 비율 (%)
            
        Returns:
            이익실현/손절매 조건이 적용된 DataFrame
        """
        # 데이터 복사
        result = signals.copy()
        
        # 이익실현/손절매 비율을 소수점으로 변환
        take_profit_ratio = take_profit / 100.0
        stop_loss_ratio = stop_loss / 100.0
        
        # 진입 가격 추적
        result['entry_price'] = 0.0
        
        # 각 매수 신호마다 진입 가격 설정
        entry_price = 0.0
        position = 0
        
        for i in range(len(result)):
            current_signal = result.iloc[i]
            
            # 매수 시 진입 가격 설정
            if current_signal['position'] == 1:
                entry_price = current_signal['Close']
                position = 1
                result.loc[result.index[i], 'entry_price'] = entry_price
            
            # 매도 시 진입 가격 초기화
            elif current_signal['position'] == -1:
                entry_price = 0.0
                position = 0
                result.loc[result.index[i], 'entry_price'] = 0.0
            
            # 이미 포지션이 있는 경우, 해당 포지션의 진입 가격을 유지
            elif position == 1:
                result.loc[result.index[i], 'entry_price'] = entry_price
                
                # 이익실현/손절매 확인
                if entry_price > 0:
                    current_price = current_signal['Close']
                    price_change = (current_price - entry_price) / entry_price
                    
                    # 이익실현 조건
                    if price_change >= take_profit_ratio:
                        result.loc[result.index[i], 'position'] = -1  # 매도 신호로 변경
                        position = 0
                        entry_price = 0.0
                        logger.info(f"이익실현 조건 충족: {price_change*100:.2f}% (목표: {take_profit}%)")
                    
                    # 손절매 조건
                    elif price_change <= -stop_loss_ratio:
                        result.loc[result.index[i], 'position'] = -1  # 매도 신호로 변경
                        position = 0
                        entry_price = 0.0
                        logger.info(f"손절매 조건 충족: {price_change*100:.2f}% (목표: -{stop_loss}%)")
        
        return result 