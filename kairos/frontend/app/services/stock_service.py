"""
주식 데이터 관련 서비스 모듈입니다.
"""
import json
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np
import requests

logger = logging.getLogger(__name__)

class StockService:
    """주식 데이터 관리 서비스 클래스"""
    
    def __init__(self, data_dir: str = None, cache_expiry: int = 24):
        """
        주식 데이터 서비스 초기화
        
        Args:
            data_dir: 데이터 캐시 디렉토리 경로 (기본값: 현재 디렉토리 내 'stock_data')
            cache_expiry: 캐시 만료 시간 (시간 단위, 기본값: 24시간)
        """
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'stock_data')
        else:
            self.data_dir = data_dir
        
        self.cache_expiry = cache_expiry
        self._ensure_data_dir()
        
        # 인기 종목 목록
        self.popular_stocks = [
            {"code": "005930", "name": "삼성전자", "sector": "전기전자"},
            {"code": "000660", "name": "SK하이닉스", "sector": "전기전자"},
            {"code": "035720", "name": "카카오", "sector": "서비스업"},
            {"code": "005380", "name": "현대자동차", "sector": "운수장비"},
            {"code": "051910", "name": "LG화학", "sector": "화학"},
            {"code": "035420", "name": "NAVER", "sector": "서비스업"},
            {"code": "068270", "name": "셀트리온", "sector": "의약품"},
            {"code": "105560", "name": "KB금융", "sector": "금융업"},
            {"code": "055550", "name": "신한지주", "sector": "금융업"},
            {"code": "096770", "name": "SK이노베이션", "sector": "화학"}
        ]
    
    def _ensure_data_dir(self) -> None:
        """데이터 디렉토리가 존재하는지 확인하고 없으면 생성"""
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                logger.info(f"주식 데이터 디렉토리 생성: {self.data_dir}")
            except Exception as e:
                logger.error(f"주식 데이터 디렉토리 생성 실패: {e}")
                raise
    
    def get_stock_price_data(self, stock_code: str, days: int = 90, use_real_data: bool = True) -> pd.DataFrame:
        """
        주식 가격 데이터 가져오기
        
        Args:
            stock_code: 종목 코드
            days: 데이터 일수
            use_real_data: 실제 데이터 사용 여부 (False면 시뮬레이션 데이터 생성)
            
        Returns:
            주가 데이터 DataFrame (날짜, 시가, 고가, 저가, 종가, 거래량)
        """
        if not stock_code:
            raise ValueError("종목 코드가 필요합니다")
        
        # 캐시 파일 경로
        cache_file = os.path.join(self.data_dir, f"{stock_code}_{days}d.csv")
        
        # 캐시 파일이 있고 만료되지 않았으면 사용
        if os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if (datetime.now() - cache_time).total_seconds() < self.cache_expiry * 3600:
                try:
                    df = pd.read_csv(cache_file, parse_dates=['Date'])
                    logger.info(f"{stock_code} 캐시 데이터 로드 성공 ({days}일)")
                    return df
                except Exception as e:
                    logger.warning(f"{stock_code} 캐시 데이터 로드 실패: {e}")
        
        # 캐시가 없거나 만료됐으면 새로 데이터 가져오기
        if use_real_data:
            try:
                df = self._fetch_stock_data(stock_code, days)
                # 데이터 캐싱
                df.to_csv(cache_file, index=False)
                logger.info(f"{stock_code} 실제 데이터 가져오기 성공 ({days}일)")
                return df
            except Exception as e:
                logger.error(f"{stock_code} 실제 데이터 가져오기 실패: {e}")
                logger.info("시뮬레이션 데이터 생성 중...")
        
        # 실제 데이터 사용 안하거나 가져오기 실패한 경우 시뮬레이션 데이터 생성
        df = self._generate_simulation_data(stock_code, days)
        df.to_csv(cache_file, index=False)
        logger.info(f"{stock_code} 시뮬레이션 데이터 생성 완료 ({days}일)")
        return df
    
    def _fetch_stock_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        실제 주식 데이터 API에서 가져오기
        
        Args:
            stock_code: 종목 코드
            days: 데이터 일수
            
        Returns:
            주가 데이터 DataFrame
        """
        # 실제 API 호출로 대체 필요
        # 예시: 공공 API, 증권사 API 등을 사용
        
        # 지금은 예시로 시뮬레이션 데이터 반환
        raise NotImplementedError("실제 주식 데이터 API 연결이 구현되지 않았습니다")
    
    def _generate_simulation_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        시뮬레이션 주식 데이터 생성
        
        Args:
            stock_code: 종목 코드
            days: 데이터 일수
            
        Returns:
            시뮬레이션 주가 데이터 DataFrame
        """
        # 종목별로 다른 초기 가격 설정
        seed = sum(ord(c) for c in stock_code)
        random.seed(seed)
        
        # 시작 가격 설정 (종목별로 다르게)
        if stock_code in ["005930", "000660"]:  # 삼성전자, SK하이닉스 등 고가 주식
            base_price = random.randint(50000, 80000)
        elif stock_code in ["051910", "096770"]:  # LG화학, SK이노베이션 등 중가 주식
            base_price = random.randint(20000, 50000)
        else:  # 저가 주식
            base_price = random.randint(5000, 20000)
        
        # 기본 변동성
        volatility = random.uniform(0.01, 0.03)
        
        # 일별 데이터 생성
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
        price = base_price
        prices = []
        volumes = []
        
        # 추세 설정 (상승, 하락, 횡보)
        trend = random.choice(['up', 'down', 'flat'])
        trend_factor = 0.002 if trend == 'up' else -0.002 if trend == 'down' else 0
        
        for i in range(days):
            # 일별 변동성
            daily_volatility = volatility * random.uniform(0.5, 1.5)
            
            # 가격 변동
            change = price * (trend_factor + random.uniform(-daily_volatility, daily_volatility))
            
            # 일중 가격
            open_price = price + random.uniform(-0.5, 0.5) * change
            close_price = price + change
            high_price = max(open_price, close_price) * (1 + random.uniform(0, daily_volatility))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, daily_volatility))
            
            # 거래량 (가격 변동에 따라 변화)
            volume = int(abs(change) * base_price * random.uniform(100, 1000))
            
            prices.append([open_price, high_price, low_price, close_price])
            volumes.append(volume)
            
            # 다음 날의 시작 가격
            price = close_price
            
            # 가끔 추세 변화
            if random.random() < 0.05:
                trend = random.choice(['up', 'down', 'flat'])
                trend_factor = 0.002 if trend == 'up' else -0.002 if trend == 'down' else 0
        
        # DataFrame 생성
        df = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Open': [p[0] for p in prices],
            'High': [p[1] for p in prices],
            'Low': [p[2] for p in prices],
            'Close': [p[3] for p in prices],
            'Volume': volumes
        })
        
        return df
    
    def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        종목 검색
        
        Args:
            query: 검색어
            limit: 검색 결과 최대 개수
            
        Returns:
            검색 결과 목록
        """
        if not query or len(query) < 2:
            return []
        
        # 실제로는 API를 통해 검색해야 함
        # 여기서는 인기 종목 목록에서 검색어가 포함된 종목 반환
        results = []
        for stock in self.popular_stocks:
            if (query.lower() in stock["name"].lower() or 
                query.lower() in stock["code"].lower() or
                query in stock["sector"]):
                results.append(stock)
        
        # 이름순 정렬
        results.sort(key=lambda x: x["name"])
        
        return results[:limit]
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        종목 정보 가져오기
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            종목 정보 또는 None (찾지 못한 경우)
        """
        # 인기 종목 중에서 찾기
        for stock in self.popular_stocks:
            if stock["code"] == stock_code:
                # 기본 정보
                info = stock.copy()
                
                # 현재가와 시가총액은 실제로는 API에서 가져와야 함
                # 여기서는 시뮬레이션 데이터 사용
                df = self.get_stock_price_data(stock_code, days=1, use_real_data=False)
                current_price = df.iloc[-1]['Close']
                
                # 시가총액 계산 (예시 - 실제로는 발행주식수가 필요)
                shares_outstanding = random.randint(100000000, 1000000000)
                market_cap = current_price * shares_outstanding
                
                # 추가 정보
                info.update({
                    "current_price": current_price,
                    "price_change": random.uniform(-3.0, 3.0),
                    "market_cap": market_cap,
                    "per": random.uniform(5.0, 30.0),
                    "eps": current_price / random.uniform(5.0, 30.0),
                    "pbr": random.uniform(0.5, 5.0),
                    "dividend_yield": random.uniform(0.0, 5.0)
                })
                
                return info
        
        # 인기 종목에 없는 경우
        # 실제로는 API를 통해 정보를 가져와야 함
        if stock_code:
            # 임의의 정보 생성
            seed = sum(ord(c) for c in stock_code)
            random.seed(seed)
            
            df = self.get_stock_price_data(stock_code, days=1, use_real_data=False)
            current_price = df.iloc[-1]['Close']
            
            # 종목명 생성 (실제로는 API에서 가져와야 함)
            fake_names = ["테크놀로지", "바이오", "화학", "금융", "에너지", "건설", "소프트웨어", "반도체", "유통", "통신"]
            name_seed = seed % len(fake_names)
            fake_name = f"{fake_names[name_seed]} {stock_code[-2:]}"
            
            # 섹터 설정
            sectors = ["전기전자", "서비스업", "금융업", "운수장비", "화학", "의약품", "건설업", "음식료품", "통신업", "기계"]
            sector = sectors[seed % len(sectors)]
            
            # 시가총액 계산
            shares_outstanding = random.randint(10000000, 500000000)
            market_cap = current_price * shares_outstanding
            
            return {
                "code": stock_code,
                "name": fake_name,
                "sector": sector,
                "current_price": current_price,
                "price_change": random.uniform(-3.0, 3.0),
                "market_cap": market_cap,
                "per": random.uniform(5.0, 30.0),
                "eps": current_price / random.uniform(5.0, 30.0),
                "pbr": random.uniform(0.5, 5.0),
                "dividend_yield": random.uniform(0.0, 5.0)
            }
        
        return None
    
    def get_popular_stocks(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        인기 종목 목록 가져오기
        
        Args:
            limit: 최대 개수
            
        Returns:
            인기 종목 목록
        """
        return self.popular_stocks[:limit] 