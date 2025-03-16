import logging
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional

from .database import db

logger = logging.getLogger(__name__)

class BacktestStore:
    """백테스트 결과 저장소 클래스"""
    
    def __init__(self, database=None):
        """
        백테스트 저장소 초기화
        
        Args:
            database: 데이터베이스 인스턴스 (기본값: 전역 db 인스턴스)
        """
        self.db = database or db
    
    def save(self, result: Dict[str, Any]) -> str:
        """
        백테스트 결과 저장
        
        Args:
            result: 백테스트 결과 데이터
            
        Returns:
            저장된 백테스트 ID
        """
        # ID가 없으면 생성
        if 'id' not in result or not result['id']:
            result['id'] = str(uuid.uuid4())
        
        # 날짜가 없으면 현재 시간 사용
        if 'date' not in result or not result['date']:
            result['date'] = datetime.now().isoformat()
        
        # 데이터베이스에 저장
        try:
            backtest_id = self.db.insert_backtest_result(result)
            logger.info(f"백테스트 결과 저장 완료: {backtest_id}")
            return backtest_id
        except Exception as e:
            logger.error(f"백테스트 결과 저장 실패: {str(e)}")
            raise
    
    def get(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 백테스트 결과 조회
        
        Args:
            backtest_id: 백테스트 ID
            
        Returns:
            백테스트 결과 또는 None
        """
        try:
            result = self.db.get_backtest_result(backtest_id)
            return result
        except Exception as e:
            logger.error(f"백테스트 결과 조회 실패: {str(e)}")
            return None
    
    def get_by_strategy(self, strategy_id: str) -> List[Dict[str, Any]]:
        """
        전략 ID로 백테스트 결과 목록 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            백테스트 결과 목록
        """
        try:
            results = self.db.get_backtest_results_by_strategy(strategy_id)
            return results
        except Exception as e:
            logger.error(f"전략 {strategy_id}의 백테스트 결과 목록 조회 실패: {str(e)}")
            return [] 