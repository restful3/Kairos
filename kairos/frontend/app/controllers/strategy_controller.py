"""
전략 관리 및 백테스팅 컨트롤러 모듈입니다.
UI 컴포넌트와 서비스 레이어 간의 상호작용을 담당합니다.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from ..api.client import api_client
from ..services.stock_service import StockService
from ..services.backtest_service import BacktestService

logger = logging.getLogger(__name__)

class StrategyController:
    """전략 관리 및 백테스팅 컨트롤러 클래스"""
    
    def __init__(self):
        """전략 컨트롤러 초기화"""
        self.stock_service = StockService()
        self.backtest_service = BacktestService(
            stock_service=self.stock_service
        )
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """
        모든 전략 목록 가져오기
        
        Returns:
            전략 딕셔너리 목록
        """
        try:
            return api_client.get_strategies()
        except Exception as e:
            logger.error(f"전략 목록 조회 실패: {e}")
            return []
    
    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """
        활성화된 전략 목록 가져오기
        
        Returns:
            활성화된 전략 딕셔너리 목록
        """
        try:
            return api_client.get_strategies(active_only=True)
        except Exception as e:
            logger.error(f"활성 전략 목록 조회 실패: {e}")
            return []
    
    def get_strategy_by_id(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 전략 가져오기
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            전략 딕셔너리 또는 None
        """
        try:
            return api_client.get_strategy(strategy_id)
        except Exception as e:
            logger.error(f"전략 조회 실패: {e}")
            return None
    
    def save_strategy(self, strategy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        전략 저장하기
        
        Args:
            strategy_data: 전략 데이터 딕셔너리
            
        Returns:
            (성공 여부, 메시지)
        """
        try:
            # 필수 필드 검증
            required_fields = {
                "name": "전략 이름",
                "stock_code": "종목 코드",
                "stock_name": "종목명",
                "strategy_type": "전략 유형",
                "params": "전략 매개변수",
                "take_profit": "이익실현 비율",
                "stop_loss": "손절매 비율",
                "investment_amount": "투자금액"
            }
            
            for field, name in required_fields.items():
                if not strategy_data.get(field):
                    return False, f"{name}은(는) 필수 입력 항목입니다."
            
            # 전략 저장
            if strategy_data.get("id"):  # 기존 전략 수정
                success = api_client.update_strategy(
                    strategy_data["id"],
                    strategy_data
                )
                action = "수정"
            else:  # 새 전략 생성
                strategy_id = api_client.create_strategy(strategy_data)
                success = bool(strategy_id)
                action = "생성"
            
            if success:
                logger.info(f"전략 '{strategy_data.get('name')}' {action} 성공")
                return True, f"전략이 성공적으로 {action}되었습니다."
            else:
                logger.error(f"전략 '{strategy_data.get('name')}' {action} 실패")
                return False, f"전략 {action}에 실패했습니다."
                
        except Exception as e:
            error_msg = f"전략 저장 중 예외 발생: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_strategy(self, strategy_id: str) -> Tuple[bool, str]:
        """
        전략 삭제
        
        Args:
            strategy_id: 삭제할 전략 ID
            
        Returns:
            (성공 여부, 메시지)
        """
        try:
            success = api_client.delete_strategy(strategy_id)
            if success:
                return True, "전략이 삭제되었습니다."
            else:
                return False, "전략 삭제에 실패했습니다."
        except Exception as e:
            logger.error(f"전략 삭제 중 오류 발생: {e}")
            return False, f"전략 삭제 중 오류가 발생했습니다: {str(e)}"
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        종목 정보 가져오기
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            종목 정보 또는 None
        """
        return self.stock_service.get_stock_info(stock_code)
    
    def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        종목 검색
        
        Args:
            query: 검색어
            limit: 검색 결과 최대 개수
            
        Returns:
            검색 결과 목록
        """
        return self.stock_service.search_stocks(query, limit)
    
    def get_popular_stocks(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        인기 종목 목록 가져오기
        
        Args:
            limit: 최대 개수
            
        Returns:
            인기 종목 목록
        """
        return self.stock_service.get_popular_stocks(limit) 