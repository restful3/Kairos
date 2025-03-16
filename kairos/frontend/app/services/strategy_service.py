"""
매매 전략 관리를 위한 서비스 모듈입니다.
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from ..api.client import api_client
from ..models.strategy import TradingStrategy

logger = logging.getLogger(__name__)

class StrategyService:
    """매매 전략 관리 서비스 클래스"""
    
    def __init__(self, strategies_dir: str = None):
        """
        매매 전략 관리 서비스 초기화
        
        Args:
            strategies_dir: 전략 저장 디렉토리 경로 (기본값: 현재 디렉토리 내 'strategies')
        """
        if strategies_dir is None:
            # frontend/data/strategies 디렉토리를 사용
            self.strategies_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data',
                'strategies'
            )
        else:
            self.strategies_dir = strategies_dir
        
        self._ensure_strategies_dir()
    
    def _ensure_strategies_dir(self) -> None:
        """전략 저장 디렉토리가 존재하는지 확인하고 없으면 생성"""
        if not os.path.exists(self.strategies_dir):
            try:
                os.makedirs(self.strategies_dir)
                logger.info(f"전략 저장 디렉토리 생성: {self.strategies_dir}")
            except Exception as e:
                logger.error(f"전략 저장 디렉토리 생성 실패: {e}")
                raise
    
    def validate_strategy(self, strategy: TradingStrategy) -> Tuple[bool, str]:
        """
        전략 데이터 유효성 검사
        
        Args:
            strategy: 검사할 전략 객체
            
        Returns:
            (유효성 여부, 메시지)
        """
        if not strategy.name:
            return False, "전략 이름은 필수입니다."
            
        if not strategy.stock_code or not strategy.stock_name:
            return False, "종목 코드와 종목명은 필수입니다."
            
        if not strategy.strategy_type:
            return False, "전략 유형은 필수입니다."
            
        if not strategy.params:
            return False, "전략 매개변수는 필수입니다."
            
        return True, "유효성 검사 통과"
    
    def get_all_strategies(self) -> List[TradingStrategy]:
        """
        저장된 모든 전략 가져오기
        
        Returns:
            전략 객체 리스트
        """
        try:
            strategies_data = api_client.get_strategies()
            return [TradingStrategy.from_dict(data) for data in strategies_data]
        except Exception as e:
            logger.error(f"전략 목록 로드 실패: {e}")
            return []
    
    def get_strategy_by_name(self, name: str) -> Optional[TradingStrategy]:
        """
        이름으로 전략 가져오기
        
        Args:
            name: 전략 이름
            
        Returns:
            전략 객체 또는 None (찾지 못한 경우)
        """
        strategies = self.get_all_strategies()
        for strategy in strategies:
            if strategy.name == name:
                return strategy
        return None
    
    def get_strategies_by_stock_code(self, stock_code: str) -> List[TradingStrategy]:
        """
        종목 코드로 전략 검색
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            전략 객체 리스트
        """
        strategies = self.get_all_strategies()
        return [s for s in strategies if s.stock_code == stock_code]
    
    def get_strategies_by_type(self, strategy_type: str) -> List[TradingStrategy]:
        """
        전략 유형으로 전략 검색
        
        Args:
            strategy_type: 전략 유형
            
        Returns:
            전략 객체 리스트
        """
        strategies = self.get_all_strategies()
        return [s for s in strategies if s.strategy_type == strategy_type]
    
    def get_active_strategies(self) -> List[TradingStrategy]:
        """
        활성화된 전략만 가져오기
        
        Returns:
            활성화된 전략 객체 리스트
        """
        try:
            strategies_data = api_client.get_strategies(active_only=True)
            return [TradingStrategy.from_dict(data) for data in strategies_data]
        except Exception as e:
            logger.error(f"활성 전략 목록 로드 실패: {e}")
            return []
    
    def save_strategy(self, strategy: TradingStrategy) -> Tuple[bool, str]:
        """
        전략 저장하기
        
        Args:
            strategy: 저장할 전략 객체
            
        Returns:
            (저장 성공 여부, 메시지)
        """
        # 유효성 검사
        is_valid, message = self.validate_strategy(strategy)
        if not is_valid:
            return False, message
            
        try:
            strategy_data = strategy.to_dict()
            
            if strategy.id:  # 기존 전략 수정
                success = api_client.update_strategy(strategy.id, strategy_data)
                action = "수정"
            else:  # 새 전략 생성
                strategy_id = api_client.create_strategy(strategy_data)
                success = bool(strategy_id)
                action = "생성"
            
            if success:
                logger.info(f"전략 '{strategy.name}' {action} 완료")
                return True, f"전략이 성공적으로 {action}되었습니다."
            else:
                return False, f"전략 {action}에 실패했습니다."
                
        except Exception as e:
            error_msg = f"전략 저장 실패: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_strategy(self, name: str) -> bool:
        """
        전략 삭제
        
        Args:
            name: 삭제할 전략 이름
            
        Returns:
            삭제 성공 여부
        """
        try:
            strategy = self.get_strategy_by_name(name)
            if not strategy or not strategy.id:
                logger.warning(f"삭제할 전략 '{name}'을 찾을 수 없음")
                return False
            
            success = api_client.delete_strategy(strategy.id)
            
            if success:
                logger.info(f"전략 '{name}' 삭제 완료")
                return True
            else:
                logger.error(f"전략 '{name}' 삭제 실패")
                return False
                
        except Exception as e:
            logger.error(f"전략 삭제 중 오류 발생: {str(e)}")
            return False
    
    def toggle_strategy_status(self, strategy_name: str) -> Tuple[bool, Optional[TradingStrategy]]:
        """
        전략 활성화 상태 토글
        
        Args:
            strategy_name: 전략 이름
            
        Returns:
            (성공 여부, 업데이트된 전략 객체)
        """
        strategy = self.get_strategy_by_name(strategy_name)
        if not strategy:
            logger.warning(f"전략 '{strategy_name}'을 찾을 수 없어 상태를 변경할 수 없음")
            return False, None
        
        try:
            success = api_client.update_strategy(
                strategy.id,
                {"is_active": not strategy.is_active}
            )
            
            if success:
                strategy.is_active = not strategy.is_active
                logger.info(f"전략 '{strategy_name}' 상태가 '{strategy.is_active}'로 변경됨")
                return True, strategy
            else:
                logger.error(f"전략 '{strategy_name}' 상태 변경 실패")
                return False, None
                
        except Exception as e:
            logger.error(f"전략 상태 변경 중 오류 발생: {str(e)}")
            return False, None
    
    def create_example_strategies(self) -> List[TradingStrategy]:
        """
        예제 전략 생성
        
        Returns:
            생성된 예제 전략 리스트
        """
        example_strategies = []
        
        # 이동평균 교차 전략
        ma_cross = TradingStrategy(
            name="삼성전자 MA 교차 전략",
            stock_code="005930",
            stock_name="삼성전자",
            strategy_type="이동평균 교차",
            params={
                "fast_period": 5,
                "slow_period": 20,
                "signal_period": 9
            },
            take_profit=10.0,
            stop_loss=5.0,
            investment_amount=1000000,
            is_active=True
        )
        
        # RSI 전략
        rsi = TradingStrategy(
            name="현대차 RSI 전략",
            stock_code="005380",
            stock_name="현대자동차",
            strategy_type="RSI",
            params={
                "period": 14,
                "overbought": 70,
                "oversold": 30
            },
            take_profit=15.0,
            stop_loss=7.0,
            investment_amount=500000,
            is_active=False
        )
        
        # 가격 돌파 전략
        breakout = TradingStrategy(
            name="카카오 가격 돌파 전략",
            stock_code="035720",
            stock_name="카카오",
            strategy_type="가격 돌파",
            params={
                "lookback_period": 20,
                "breakout_type": "신고가"
            },
            take_profit=20.0,
            stop_loss=10.0,
            investment_amount=1000000,
            is_active=True
        )
        
        # 예제 전략 저장
        for strategy in [ma_cross, rsi, breakout]:
            success, _ = self.save_strategy(strategy)
            if success:
                example_strategies.append(strategy)
        
        return example_strategies 