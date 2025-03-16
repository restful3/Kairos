from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..services.backtest_service import BacktestService
from ..services.strategy_service import StrategyService

router = APIRouter(prefix="/backtest", tags=["backtest"])
backtest_service = BacktestService()
strategy_service = StrategyService()

class BacktestRequest(BaseModel):
    strategy_id: str = Field(..., description="전략 ID")
    days: int = Field(90, description="백테스팅 기간(일)")
    initial_capital: float = Field(10000000, description="초기 자본금")
    fee_rate: float = Field(0.00015, description="거래 수수료율")
    use_real_data: bool = Field(True, description="실제 데이터 사용 여부")

class BacktestResponse(BaseModel):
    id: str = Field(..., description="백테스트 ID")
    strategy_id: str = Field(..., description="전략 ID")
    strategy_name: str = Field(..., description="전략 이름")
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str = Field(..., description="종목 이름")
    metrics: Dict[str, Any] = Field(..., description="성과 지표")
    backtest_params: Dict[str, Any] = Field(..., description="백테스트 파라미터")
    portfolio_values: List[Dict[str, Any]] = Field([], description="포트폴리오 가치 추적")
    trades: List[Dict[str, Any]] = Field([], description="거래 내역")
    date: str = Field(..., description="백테스트 실행 날짜")

@router.post("", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    백테스팅 실행 API
    
    전략을 백테스팅하고 결과를 반환합니다.
    """
    try:
        # 파라미터 객체 생성
        params = {
            "days": request.days,
            "initial_capital": request.initial_capital,
            "fee_rate": request.fee_rate,
            "use_real_data": request.use_real_data
        }
        
        # 백테스팅 실행
        result = backtest_service.run_backtest(
            strategy_id=request.strategy_id,
            params=params
        )
        
        # 응답 형식으로 변환
        strategy = result.get("strategy", {})
        return {
            "id": result.get("id", ""),
            "strategy_id": request.strategy_id,
            "strategy_name": strategy.get("name", ""),
            "stock_code": strategy.get("stock_code", ""),
            "stock_name": strategy.get("stock", {}).get("name", ""),
            "metrics": result.get("metrics", {}),
            "backtest_params": result.get("backtest_params", {}),
            "portfolio_values": result.get("portfolio_values", []),
            "trades": result.get("trades", []),
            "date": result.get("date", datetime.now().isoformat())
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백테스팅 실행 중 오류 발생: {str(e)}")

@router.get("/{backtest_id}", response_model=Dict[str, Any])
async def get_backtest_result(backtest_id: str):
    """
    백테스트 결과 조회 API
    
    특정 백테스트의 상세 결과를 반환합니다.
    """
    try:
        result = backtest_service.get_backtest_result(backtest_id)
        if not result:
            raise HTTPException(status_code=404, detail="백테스트 결과를 찾을 수 없습니다")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/{strategy_id}", response_model=List[Dict[str, Any]])
async def get_strategy_backtests(strategy_id: str):
    """
    전략 백테스트 목록 조회 API
    
    특정 전략의 모든 백테스트 결과를 반환합니다.
    """
    try:
        strategy = strategy_service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
            
        # 전략에서 백테스트 이력 추출
        backtest_history = strategy.get("backtest_history", [])
        return backtest_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 