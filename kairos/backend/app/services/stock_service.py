"""
주식 데이터 관련 서비스 모듈입니다.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import re

import pandas as pd
import numpy as np

from ..database.database import db

logger = logging.getLogger(__name__)

class StockService:
    """주식 데이터 관리 서비스 클래스"""
    
    def __init__(self, data_dir: str = None, cache_expiry: int = 24):
        """
        주식 데이터 서비스 초기화
        
        Args:
            data_dir: 데이터 캐시 디렉토리 경로 (기본값: None, 자동 생성)
            cache_expiry: 캐시 만료 시간 (시간 단위, 기본값: 24시간)
        """
        # 데이터 캐시 디렉토리 설정
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.data_dir = os.path.join(base_dir, 'data', 'stock_data')
        else:
            self.data_dir = data_dir
        
        # 캐시 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.cache_expiry = cache_expiry
        
        # 인기 종목 목록 (예시)
        self.popular_stocks = [
            {"code": "005930", "name": "삼성전자", "sector": "전기전자"},
            {"code": "000660", "name": "SK하이닉스", "sector": "전기전자"},
            {"code": "035720", "name": "카카오", "sector": "서비스업"},
            {"code": "005380", "name": "현대자동차", "sector": "운수장비"},
            {"code": "051910", "name": "LG화학", "sector": "화학"}
        ]
    
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
                    df = pd.read_csv(cache_file, parse_dates=['date'])
                    logger.info(f"{stock_code} 캐시 데이터 로드 성공 ({days}일)")
                    return df
                except Exception as e:
                    logger.warning(f"{stock_code} 캐시 데이터 로드 실패: {e}")
        
        # 캐시가 없거나 만료됐으면 새로 데이터 가져오기
        if use_real_data:
            try:
                df = self._fetch_real_stock_data(stock_code, days)
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
    
    def _fetch_real_stock_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        실제 주식 데이터 API에서 가져오기
        
        Args:
            stock_code: 종목 코드
            days: 데이터 일수
            
        Returns:
            주가 데이터 DataFrame
        """
        # 현재 날짜와 시작 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 날짜 형식 변환
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        try:
            # KIS API를 통해 데이터 가져오기
            from ..services.kis_service import KisService
            kis = KisService()
            
            # 실제 KIS API 연동
            daily_prices = kis.get_daily_price(stock_code, start_date_str, end_date_str)
            
            # API 호출 실패시 빈 데이터프레임 반환
            if not daily_prices:
                logger.warning(f"종목 {stock_code} 일별 시세 조회 실패")
                return pd.DataFrame()
            
            # API 응답 데이터를 DataFrame으로 변환
            df = pd.DataFrame(daily_prices)
            
            # 컬럼명 변경
            df = df.rename(columns={
                'stck_bsop_date': 'date',
                'stck_oprc': 'open',
                'stck_hgpr': 'high',
                'stck_lwpr': 'low',
                'stck_clpr': 'close',
                'acml_vol': 'volume'
            })
            
            # 날짜 형식 변환
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            
            # 정렬
            df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            logger.error(f"실제 데이터 가져오기 실패: {e}")
            raise
    
    def _generate_simulation_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        시뮬레이션 주가 데이터 생성
        
        Args:
            stock_code: 종목 코드
            days: 데이터 일수
            
        Returns:
            시뮬레이션 주가 데이터 DataFrame
        """
        # 시뮬레이션 데이터 생성
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 영업일만 포함하도록 조정 (주말 제외 - 간단히 70%로 가정)
        business_days = int(days * 0.7)
        
        dates = pd.date_range(start=start_date, periods=business_days, freq='B')
        
        # 시드 고정으로 같은 종목은 같은 패턴 생성
        try:
            # 종목코드의 마지막 두 자리를 시드로 사용 (숫자가 아닌 경우 대체 방법 사용)
            seed = int(stock_code[-2:]) if stock_code[-2:].isdigit() else sum(ord(c) for c in stock_code)
            np.random.seed(seed)
        except Exception as e:
            logger.warning(f"시드 설정 중 오류 발생, 기본 시드 사용: {str(e)}")
            np.random.seed(42)  # 기본 시드
        
        # 초기 가격 설정 (종목코드에 따라 다르게)
        try:
            seed_value = int(stock_code[-2:]) if stock_code[-2:].isdigit() else sum(ord(c) for c in stock_code) % 100
            start_price = 50000 + seed_value * 1000
        except Exception:
            start_price = 50000  # 기본값
        
        # 추세 성분 (약간의 상승세)
        trend = np.linspace(0, days * 0.1, business_days)
        
        # 랜덤 워크 성분
        random_walk = np.random.normal(0, 1, business_days).cumsum() * (start_price * 0.02)
        
        # 계절성 성분 (주기적 패턴)
        seasonality = np.sin(np.linspace(0, 5 * np.pi, business_days)) * (start_price * 0.1)
        
        # 가격 데이터 생성
        close_prices = start_price + trend + random_walk + seasonality
        close_prices = np.maximum(close_prices, start_price * 0.5)  # 최소가격 보장
        
        # 일별 변동성으로 OHLC 데이터 생성
        daily_volatility = start_price * 0.015
        
        data = []
        for i, date in enumerate(dates):
            close = close_prices[i]
            high = close + abs(np.random.normal(0, daily_volatility))
            low = close - abs(np.random.normal(0, daily_volatility))
            open_price = low + (high - low) * np.random.random()
            
            # 거래량 - 가격 변동에 비례하게
            price_change = abs(close - close_prices[i-1] if i > 0 else 0)
            volume = int(np.random.normal(500000, 200000) + price_change * 100)
            volume = max(volume, 10000)
            
            data.append({
                'date': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        # 데이터프레임으로 변환
        df = pd.DataFrame(data)
        
        return df
    
    def get_popular_stocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        인기 종목 목록 가져오기
        
        Args:
            limit: 최대 결과 수
            
        Returns:
            인기 종목 목록
        """
        return self.popular_stocks[:limit]
    
    def search_stocks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        종목 검색
        
        Args:
            query: 검색어 (종목명 또는 코드)
            limit: 최대 결과 수
            
        Returns:
            검색 결과 종목 목록
        """
        # 전체 종목 목록 (실제로는 더 많은 종목이 있음)
        all_stocks = [
            {"code": "005930", "name": "삼성전자", "sector": "전기전자"},
            {"code": "000660", "name": "SK하이닉스", "sector": "전기전자"},
            {"code": "035720", "name": "카카오", "sector": "서비스업"},
            {"code": "005380", "name": "현대자동차", "sector": "운수장비"},
            {"code": "051910", "name": "LG화학", "sector": "화학"},
            {"code": "035420", "name": "NAVER", "sector": "서비스업"},
            {"code": "068270", "name": "셀트리온", "sector": "의약품"},
            {"code": "207940", "name": "삼성바이오로직스", "sector": "의약품"},
            {"code": "035720", "name": "카카오", "sector": "서비스업"},
            {"code": "000270", "name": "기아", "sector": "운수장비"},
            {"code": "005490", "name": "POSCO홀딩스", "sector": "철강금속"},
            {"code": "055550", "name": "신한지주", "sector": "금융업"},
            {"code": "105560", "name": "KB금융", "sector": "금융업"},
            {"code": "373220", "name": "LG에너지솔루션", "sector": "전기전자"},
            {"code": "006400", "name": "삼성SDI", "sector": "전기전자"},
            {"code": "051900", "name": "LG생활건강", "sector": "화학"},
            {"code": "028260", "name": "삼성물산", "sector": "유통업"},
            {"code": "036570", "name": "엔씨소프트", "sector": "서비스업"},
            {"code": "012330", "name": "현대모비스", "sector": "운수장비"},
            {"code": "018260", "name": "삼성에스디에스", "sector": "서비스업"}
        ]
        
        if not query:
            # 검색어가 없으면 인기 종목 또는 전체 종목 일부 반환
            return self.get_popular_stocks(limit)
        
        # 검색어로 필터링
        results = []
        for stock in all_stocks:
            if (query.lower() in stock["name"].lower() or 
                query.lower() in stock["code"].lower()):
                results.append(stock)
        
        return results[:limit]
    
    def get_stock_daily_prices(self, code: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        종목 일별 시세 조회
        
        Args:
            code: 종목 코드
            start_date: 조회 시작일(YYYYMMDD)
            end_date: 조회 종료일(YYYYMMDD)
            
        Returns:
            일별 시세 데이터 목록
        """
        try:
            # 날짜 범위로 days 계산
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, '%Y%m%d')
                end_dt = datetime.strptime(end_date, '%Y%m%d')
                days = (end_dt - start_dt).days + 1
            else:
                days = 90  # 기본값
            
            # 주가 데이터 가져오기
            df = self.get_stock_price_data(code, days, use_real_data=True)
            
            # 날짜 필터링
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y%m%d')
                df = df[df['date'] >= start_dt]
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y%m%d')
                df = df[df['date'] <= end_dt]
            
            # 딕셔너리 목록으로 변환
            result = []
            for _, row in df.iterrows():
                result.append({
                    'stck_bsop_date': row['date'].strftime('%Y%m%d'),
                    'stck_oprc': int(row['open']),
                    'stck_hgpr': int(row['high']),
                    'stck_lwpr': int(row['low']),
                    'stck_clpr': int(row['close']),
                    'acml_vol': int(row['volume'])
                })
            
            return result
            
        except Exception as e:
            logger.error(f"일별 시세 조회 중 오류: {str(e)}")
            # 오류 발생시 빈 목록 반환
            return []
    
    def get_stock_by_code(self, code: str) -> Dict[str, Any]:
        """
        종목 코드로 상세 정보 조회
        
        Args:
            code: 종목 코드
            
        Returns:
            종목 상세 정보 (없으면 None)
        """
        logger.info(f"종목 코드 {code}에 대한 상세 정보 조회")
        
        try:
            # 종목 기본정보 찾기
            stock = None
            
            # 전체 종목 목록에서 찾기 (임시 데이터)
            all_stocks = [
                {"code": "005930", "name": "삼성전자", "sector": "전기전자"},
                {"code": "000660", "name": "SK하이닉스", "sector": "전기전자"},
                {"code": "035720", "name": "카카오", "sector": "서비스업"},
                {"code": "005380", "name": "현대자동차", "sector": "운수장비"},
                {"code": "051910", "name": "LG화학", "sector": "화학"},
                {"code": "035420", "name": "NAVER", "sector": "서비스업"},
                {"code": "068270", "name": "셀트리온", "sector": "의약품"},
                {"code": "207940", "name": "삼성바이오로직스", "sector": "의약품"},
                {"code": "000270", "name": "기아", "sector": "운수장비"},
                {"code": "005490", "name": "POSCO홀딩스", "sector": "철강금속"}
            ]
            
            for s in all_stocks:
                if s["code"] == code:
                    stock = s.copy()
                    break
            
            if not stock:
                logger.warning(f"종목 코드 {code}에 해당하는 종목을 찾을 수 없습니다.")
                return None
            
            # KIS API를 통한 상세 정보 조회 시도
            try:
                # KIS API 연결 및 종목 현재가 조회
                from ..services.kis_service import KisService
                kis = KisService()
                
                # 최근 가격 데이터 가져오기
                price_data = self.get_stock_price_data(code, days=30)
                if not price_data.empty:
                    latest_price = price_data.iloc[-1]
                    
                    # 기본 정보에 가격 정보 추가
                    stock.update({
                        "current_price": int(latest_price["close"]),
                        "price_change": int(latest_price["close"] - latest_price["open"]),
                        "change_rate": float(((latest_price["close"] - latest_price["open"]) / latest_price["open"]) * 100),
                        "high_price": int(latest_price["high"]),
                        "low_price": int(latest_price["low"]),
                        "volume": int(latest_price["volume"]),
                        "date": latest_price["date"].strftime("%Y-%m-%d")
                    })
                
                # 차트 데이터 추가
                stock["chart_data"] = self._prepare_chart_data(price_data)
                
                # 재무 정보 추가 (임의 데이터)
                stock["financials"] = {
                    "eps": 5789,
                    "per": 13.2,
                    "pbr": 1.4,
                    "dividend_yield": 2.1,
                    "market_cap": 4821500000000  # 시가총액 (단위: 원)
                }
                
                logger.info(f"종목 {code} 상세 정보 조회 성공")
                return stock
                
            except Exception as e:
                logger.error(f"KIS API를 통한 종목 상세 정보 조회 중 오류: {str(e)}")
                
                # API 조회 실패해도 기본 정보는 반환
                stock["error"] = f"상세 정보 조회 실패: {str(e)}"
                return stock
                
        except Exception as e:
            logger.error(f"종목 상세 정보 조회 중 오류 발생: {str(e)}")
            return None
    
    def _prepare_chart_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        차트 데이터 준비
        
        Args:
            price_data: 주가 데이터 DataFrame
            
        Returns:
            차트 데이터 (날짜, 시가, 종가, 고가, 저가, 거래량)
        """
        if price_data.empty:
            return {
                "dates": [],
                "prices": {
                    "close": [],
                    "open": [],
                    "high": [],
                    "low": []
                },
                "volumes": []
            }
        
        # 날짜 형식 변환
        dates = price_data['date'].dt.strftime('%Y-%m-%d').tolist()
        
        # 가격 및 거래량 데이터 추출
        result = {
            "dates": dates,
            "prices": {
                "close": price_data['close'].tolist(),
                "open": price_data['open'].tolist(),
                "high": price_data['high'].tolist(),
                "low": price_data['low'].tolist()
            },
            "volumes": price_data['volume'].tolist()
        }
        
        return result
    
    def get_stocks_by_sector(self, sector: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        특정 업종에 속하는 종목 목록 조회
        
        Args:
            sector: 업종명
            limit: 최대 결과 수
            
        Returns:
            해당 업종 종목 목록
        """
        logger.info(f"업종 '{sector}'에 속하는 종목 목록 조회")
        
        # 전체 종목 목록 (실제로는 더 많은 종목이 있음)
        all_stocks = [
            {"code": "005930", "name": "삼성전자", "sector": "전기전자"},
            {"code": "000660", "name": "SK하이닉스", "sector": "전기전자"},
            {"code": "035720", "name": "카카오", "sector": "서비스업"},
            {"code": "005380", "name": "현대자동차", "sector": "운수장비"},
            {"code": "051910", "name": "LG화학", "sector": "화학"},
            {"code": "035420", "name": "NAVER", "sector": "서비스업"},
            {"code": "068270", "name": "셀트리온", "sector": "의약품"},
            {"code": "207940", "name": "삼성바이오로직스", "sector": "의약품"},
            {"code": "035720", "name": "카카오", "sector": "서비스업"},
            {"code": "000270", "name": "기아", "sector": "운수장비"},
            {"code": "005490", "name": "POSCO홀딩스", "sector": "철강금속"},
            {"code": "055550", "name": "신한지주", "sector": "금융업"},
            {"code": "105560", "name": "KB금융", "sector": "금융업"},
            {"code": "373220", "name": "LG에너지솔루션", "sector": "전기전자"},
            {"code": "006400", "name": "삼성SDI", "sector": "전기전자"},
            {"code": "051900", "name": "LG생활건강", "sector": "화학"},
            {"code": "028260", "name": "삼성물산", "sector": "유통업"},
            {"code": "036570", "name": "엔씨소프트", "sector": "서비스업"},
            {"code": "012330", "name": "현대모비스", "sector": "운수장비"},
            {"code": "018260", "name": "삼성에스디에스", "sector": "서비스업"}
        ]
        
        # 업종으로 필터링
        results = []
        for stock in all_stocks:
            if stock["sector"].lower() == sector.lower():
                results.append(stock)
        
        logger.info(f"업종 '{sector}'에 속하는 종목 {len(results)}개 찾음")
        return results[:limit] 