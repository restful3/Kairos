from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from app.services.stock_service import StockService
from app.utils.auth import get_current_user

router = APIRouter()

# StockService 인스턴스 생성
stock_service = StockService()

@router.get("/search")
async def search_stocks(
    query: str = Query(None, description="검색어 (종목명 또는 종목코드)"),
    limit: int = Query(20, description="최대 결과 수"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    종목 검색 API
    
    종목명 또는 종목코드로 주식 종목을 검색합니다.
    검색어를 입력하지 않으면 인기 종목 또는 전체 종목 일부를 반환합니다.
    """
    try:
        results = stock_service.search_stocks(query, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종목 검색 중 오류 발생: {str(e)}")

@router.get("/popular")
async def get_popular_stocks(
    limit: int = Query(20, description="최대 결과 수"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    인기 종목 API
    
    시가총액 상위 종목 등 인기 종목 목록을 반환합니다.
    """
    try:
        results = stock_service.get_popular_stocks(limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인기 종목 조회 중 오류 발생: {str(e)}")

@router.get("/{code}")
async def get_stock_detail(
    code: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    종목 상세 정보 API
    
    종목코드로 해당 종목의 상세 정보를 조회합니다.
    """
    stock = stock_service.get_stock_by_code(code)
    if not stock:
        raise HTTPException(status_code=404, detail=f"종목코드 {code}에 해당하는 종목을 찾을 수 없습니다.")
    return stock

@router.get("/sector/{sector}")
async def get_stocks_by_sector(
    sector: str,
    limit: int = Query(20, description="최대 결과 수"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    업종별 종목 조회 API
    
    특정 업종에 속하는 종목 목록을 조회합니다.
    """
    try:
        results = stock_service.get_stocks_by_sector(sector, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업종별 종목 조회 중 오류 발생: {str(e)}")

@router.get("/{code}/daily")
async def get_stock_daily_prices(
    code: str,
    start_date: str = Query(None, description="조회 시작일(YYYYMMDD)"),
    end_date: str = Query(None, description="조회 종료일(YYYYMMDD)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    종목 일별 시세 조회 API
    
    특정 종목의 일별 가격 데이터를 조회합니다.
    """
    try:
        results = stock_service.get_stock_daily_prices(code, start_date, end_date)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종목 일별 시세 조회 중 오류 발생: {str(e)}") 