"""
종목 관리 컨트롤러 모듈입니다.
"""
import logging
from typing import Dict, List, Any, Optional

from ..api.client import api_client

logger = logging.getLogger(__name__)

class StockController:
    """종목 관리 컨트롤러 클래스"""
    
    def __init__(self):
        """종목 컨트롤러 초기화"""
        self.api_client = api_client
    
    def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        종목 검색
        
        Args:
            query: 검색어 (종목명 또는 코드)
            limit: 최대 결과 수
            
        Returns:
            검색된 종목 목록
        """
        try:
            results = self.api_client.search_stocks(query=query, limit=limit)
            logger.info(f"종목 검색 성공: {query} ({len(results)}개 결과)")
            return results
        except Exception as e:
            logger.error(f"종목 검색 실패: {str(e)}")
            return []
    
    def get_popular_stocks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        인기 종목 조회
        
        Args:
            limit: 최대 결과 수
            
        Returns:
            인기 종목 목록
        """
        try:
            results = self.api_client.get_popular_stocks(limit=limit)
            logger.info(f"인기 종목 조회 성공 ({len(results)}개)")
            return results
        except Exception as e:
            logger.error(f"인기 종목 조회 실패: {str(e)}")
            return []
    
    def get_stock_detail(self, code: str) -> Optional[Dict[str, Any]]:
        """
        종목 상세 정보 조회
        
        Args:
            code: 종목 코드
            
        Returns:
            종목 상세 정보 또는 None
        """
        try:
            result = self.api_client.get_stock_detail(code)
            logger.info(f"종목 상세 정보 조회 성공: {code}")
            return result
        except Exception as e:
            logger.error(f"종목 상세 정보 조회 실패: {code} - {str(e)}")
            return None
    
    def get_stock_sectors(self) -> List[str]:
        """
        업종 목록 조회
        
        Returns:
            업종 목록
        """
        try:
            results = self.api_client.get_stock_sectors()
            logger.info(f"업종 목록 조회 성공 ({len(results)}개)")
            return results
        except Exception as e:
            logger.error(f"업종 목록 조회 실패: {str(e)}")
            return []
    
    def get_stocks_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        """
        업종별 종목 조회
        
        Args:
            sector: 업종명
            
        Returns:
            해당 업종의 종목 목록
        """
        try:
            results = self.api_client.get_stocks_by_sector(sector)
            logger.info(f"업종별 종목 조회 성공: {sector} ({len(results)}개)")
            return results
        except Exception as e:
            logger.error(f"업종별 종목 조회 실패: {sector} - {str(e)}")
            return [] 