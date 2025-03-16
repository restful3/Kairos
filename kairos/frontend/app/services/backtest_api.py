"""
백테스팅 관련 API 호출 모듈
"""
import logging
import requests
from typing import Dict, List, Any, Optional
import json

from app.api.client import api_client as default_api_client

logger = logging.getLogger(__name__)

class BacktestAPI:
    """백테스팅 API 클라이언트 클래스"""
    
    def __init__(self, api_client=None):
        """
        백테스팅 API 클라이언트 초기화
        
        Args:
            api_client: API 클라이언트 (기본값: None, 자동으로 생성)
        """
        self.api_client = api_client or default_api_client
        self.base_url = "/backtest"
    
    def run_backtest(
        self, 
        strategy_id: str, 
        days: int = 90, 
        initial_capital: float = 10000000, 
        fee_rate: float = 0.00015, 
        use_real_data: bool = True
    ) -> Dict[str, Any]:
        """
        백테스팅 실행
        
        Args:
            strategy_id: 전략 ID
            days: 백테스팅 기간 (일)
            initial_capital: 초기 자본금
            fee_rate: 거래 수수료율
            use_real_data: 실제 데이터 사용 여부
            
        Returns:
            백테스팅 결과
        """
        try:
            payload = {
                "strategy_id": strategy_id,
                "days": days,
                "initial_capital": initial_capital,
                "fee_rate": fee_rate,
                "use_real_data": use_real_data
            }
            
            response = self.api_client.post(f"{self.base_url}", json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"백테스팅 API 호출 실패: {response.status_code}, {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"백테스팅 API 호출 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def get_backtest_result(self, backtest_id: str) -> Dict[str, Any]:
        """
        특정 백테스트 결과 조회
        
        Args:
            backtest_id: 백테스트 ID
            
        Returns:
            백테스트 결과
        """
        try:
            response = self.api_client.get(f"{self.base_url}/{backtest_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"백테스트 결과 조회 실패: {response.status_code}, {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"백테스트 결과 조회 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def get_strategy_backtests(self, strategy_id: str) -> List[Dict[str, Any]]:
        """
        전략의 백테스트 결과 목록 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            백테스트 결과 목록
        """
        try:
            response = self.api_client.get(f"{self.base_url}/strategy/{strategy_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"전략 백테스트 목록 조회 실패: {response.status_code}, {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"전략 백테스트 목록 조회 중 오류 발생: {str(e)}")
            return [] 