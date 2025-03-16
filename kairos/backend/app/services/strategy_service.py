"""
전략 관리 서비스 모듈입니다.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from ..database.database import db

logger = logging.getLogger(__name__)

class StrategyService:
    """전략 관리 서비스 클래스"""
    
    def __init__(self, database=None):
        """
        전략 서비스 초기화
        
        Args:
            database: 데이터베이스 인스턴스 (기본값: 전역 db 인스턴스)
        """
        self.db = database or db
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """
        모든 전략 조회
        
        Returns:
            전략 목록
        """
        try:
            # 임시로 현재 라우터에서 처리하는 방식으로 구현
            # 나중에 DB에서 조회하는 방식으로 변경 필요
            from ..routers.strategy import strategy_store
            return strategy_store.get_all()
        except Exception as e:
            logger.error(f"전략 목록 조회 실패: {str(e)}")
            return []
    
    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """
        활성화된 전략 조회
        
        Returns:
            활성화된 전략 목록
        """
        try:
            strategies = self.get_all_strategies()
            return [s for s in strategies if s.get('is_active', False)]
        except Exception as e:
            logger.error(f"활성 전략 목록 조회 실패: {str(e)}")
            return []
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 전략 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            전략 정보 또는 None
        """
        try:
            from ..routers.strategy import strategy_store
            return strategy_store.get(strategy_id)
        except Exception as e:
            logger.error(f"전략 조회 실패: {str(e)}")
            return None
    
    def create_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        전략 생성
        
        Args:
            strategy: 전략 정보
            
        Returns:
            생성된 전략
        """
        try:
            from ..routers.strategy import strategy_store
            return strategy_store.create(strategy)
        except Exception as e:
            logger.error(f"전략 생성 실패: {str(e)}")
            raise
    
    def update_strategy(self, strategy_id: str, strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        전략 업데이트
        
        Args:
            strategy_id: 전략 ID
            strategy: 업데이트할 전략 정보
            
        Returns:
            업데이트된 전략 또는 None
        """
        try:
            from ..routers.strategy import strategy_store
            return strategy_store.update(strategy_id, strategy)
        except Exception as e:
            logger.error(f"전략 업데이트 실패: {str(e)}")
            return None
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        전략 삭제
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            from ..routers.strategy import strategy_store
            return strategy_store.delete(strategy_id)
        except Exception as e:
            logger.error(f"전략 삭제 실패: {str(e)}")
            return False 