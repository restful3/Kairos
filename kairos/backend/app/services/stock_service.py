import os
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime

class StockService:
    """주식 종목 정보 제공 서비스"""
    
    def __init__(self):
        """초기화"""
        self.kospi_stocks = self._load_kospi_stocks()
        self.kosdaq_stocks = self._load_kosdaq_stocks()
        self.all_stocks = {**self.kospi_stocks, **self.kosdaq_stocks}
    
    def _load_kospi_stocks(self) -> Dict[str, Dict[str, Any]]:
        """KOSPI 종목 정보 로드"""
        try:
            # 실제 구현 시 stocks_info 모듈을 사용하여 최신 데이터 가져오기
            # 예시로 하드코딩된 데이터 사용
            stocks = {
                "005930": {"code": "005930", "name": "삼성전자", "market": "KOSPI", "sector": "전기전자"},
                "000660": {"code": "000660", "name": "SK하이닉스", "market": "KOSPI", "sector": "전기전자"},
                "035420": {"code": "035420", "name": "NAVER", "market": "KOSPI", "sector": "서비스업"},
                "005380": {"code": "005380", "name": "현대차", "market": "KOSPI", "sector": "운수장비"},
                "051910": {"code": "051910", "name": "LG화학", "market": "KOSPI", "sector": "화학"}
            }
            return stocks
        except Exception as e:
            print(f"KOSPI 종목 정보 로드 중 오류: {str(e)}")
            return {}
    
    def _load_kosdaq_stocks(self) -> Dict[str, Dict[str, Any]]:
        """KOSDAQ 종목 정보 로드"""
        try:
            # 실제 구현 시 stocks_info 모듈을 사용하여 최신 데이터 가져오기
            # 예시로 하드코딩된 데이터 사용
            stocks = {
                "068270": {"code": "068270", "name": "셀트리온", "market": "KOSDAQ", "sector": "의약품"},
                "035720": {"code": "035720", "name": "카카오", "market": "KOSDAQ", "sector": "서비스업"},
                "091990": {"code": "091990", "name": "셀트리온헬스케어", "market": "KOSDAQ", "sector": "의약품"},
                "066570": {"code": "066570", "name": "LG전자", "market": "KOSDAQ", "sector": "전기전자"},
                "096770": {"code": "096770", "name": "SK이노베이션", "market": "KOSDAQ", "sector": "화학"}
            }
            return stocks
        except Exception as e:
            print(f"KOSDAQ 종목 정보 로드 중 오류: {str(e)}")
            return {}
    
    def search_stocks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        종목 검색 (종목명 또는 종목코드로 검색)
        
        Args:
            query: 검색어 (종목명 또는 종목코드)
            limit: 최대 결과 수
            
        Returns:
            검색된 종목 목록
        """
        if not query:
            # 검색어가 없으면 전체 종목의 일부 반환
            results = list(self.all_stocks.values())[:limit]
        else:
            # 종목명 또는 종목코드로 검색
            query = query.upper()  # 대소문자 구분 없이 검색
            results = []
            
            for code, stock in self.all_stocks.items():
                # 종목코드 검색
                if query in code:
                    results.append(stock)
                # 종목명 검색
                elif query in stock['name'].upper():
                    results.append(stock)
                    
                # 최대 결과 수에 도달하면 중단
                if len(results) >= limit:
                    break
                    
        # 검색 결과에 실시간 가격 정보 추가
        for stock in results:
            try:
                price_info = self.get_stock_price_info(stock['code'])
                if price_info:
                    stock.update(price_info)
            except Exception as e:
                print(f"종목 {stock['code']} 가격 정보 추가 중 오류: {str(e)}")
                
        return results
    
    def get_stock_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        종목코드로 종목 정보 조회
        
        Args:
            code: 종목코드
            
        Returns:
            종목 정보 또는 None
        """
        stock = self.all_stocks.get(code)
        if stock:
            # 실시간 가격 정보 추가
            try:
                price_info = self.get_stock_price_info(code)
                if price_info:
                    stock.update(price_info)
            except Exception as e:
                print(f"종목 {code} 가격 정보 추가 중 오류: {str(e)}")
        return stock
    
    def get_stocks_by_sector(self, sector: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        업종별 종목 조회
        
        Args:
            sector: 업종명
            limit: 최대 결과 수
            
        Returns:
            해당 업종의 종목 목록
        """
        results = []
        
        for stock in self.all_stocks.values():
            if stock['sector'] == sector:
                # 실시간 가격 정보 추가
                try:
                    price_info = self.get_stock_price_info(stock['code'])
                    if price_info:
                        stock.update(price_info)
                except Exception as e:
                    print(f"종목 {stock['code']} 가격 정보 추가 중 오류: {str(e)}")
                
                results.append(stock)
                
            if len(results) >= limit:
                break
                
        return results
        
    def get_stock_price_info(self, code: str) -> Dict[str, Any]:
        """
        종목의 실시간 가격 정보 조회
        
        Args:
            code: 종목코드
            
        Returns:
            가격 정보 (현재가, 전일대비, 등락률, 거래량 등)
        """
        try:
            # KIS API를 통해 현재가, 등락률 등 정보 가져오기
            from app.services.kis_service import KisService
            kis = KisService()
            
            # 실제 KIS API 연동
            price_info = kis.get_stock_price(code)
            
            # API 호출 실패시 빈 딕셔너리 반환
            if not price_info:
                print(f"종목 {code} 가격 정보 조회 실패")
                # 백업으로 테스트 데이터 생성
                return self._generate_test_data(code)
            
            return price_info
            
        except Exception as e:
            print(f"종목 가격 정보 조회 중 오류: {str(e)}")
            # 오류 발생시 테스트 데이터 반환
            return self._generate_test_data(code)
    
    def _generate_test_data(self, code: str) -> Dict[str, Any]:
        """테스트용 가격 데이터 생성"""
        import random
        
        # 종목코드에 따라 랜덤하지만 일관된 값 생성
        random.seed(int(code))
        current_price = round(random.uniform(10000, 100000) / 100) * 100
        price_change = round(random.uniform(-5000, 5000) / 100) * 100
        change_rate = round(price_change / (current_price - price_change) * 100, 2)
        volume = random.randint(10000, 1000000)
        
        return {
            "current_price": current_price,
            "price_change": price_change,
            "change_rate": change_rate,
            "volume": volume,
            "market_cap": current_price * random.randint(1000000, 10000000),
            "high_52wk": current_price + round(random.uniform(1000, 20000) / 100) * 100,
            "low_52wk": current_price - round(random.uniform(1000, 20000) / 100) * 100,
            "per": round(random.uniform(5, 30), 2),
            "pbr": round(random.uniform(0.5, 5), 2),
            "listed_shares": random.randint(1000000, 1000000000),
            "is_test_data": True  # 테스트 데이터임을 표시
        }
        
    def get_popular_stocks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        인기 종목 목록 조회
        
        Args:
            limit: 최대 결과 수
            
        Returns:
            인기 종목 목록
        """
        # 인기 종목 코드 목록 (시가총액 상위 종목)
        popular_codes = [
            "005930",  # 삼성전자
            "000660",  # SK하이닉스
            "005380",  # 현대차
            "051910",  # LG화학
            "035420",  # NAVER
            "068270",  # 셀트리온
            "035720",  # 카카오
            "066570",  # LG전자
            "096770",  # SK이노베이션
            "091990",  # 셀트리온헬스케어
            "000270",  # 기아
            "006400",  # 삼성SDI
            "207940",  # 삼성바이오로직스
            "012330",  # 현대모비스
            "055550",  # 신한지주
            "028260",  # 삼성물산
            "015760",  # 한국전력
            "105560",  # KB금융
            "017670",  # SK텔레콤
            "036570",  # 엔씨소프트
        ]
        
        # 인기 종목 정보 가져오기
        results = []
        for code in popular_codes[:limit]:
            stock = self.get_stock_by_code(code)
            if stock:
                results.append(stock)
                
        return results 