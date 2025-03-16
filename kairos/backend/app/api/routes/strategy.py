from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..models import (
    Strategy,
    StrategyCreate,
    StrategyUpdate,
    BacktestResult
)
from ...database.strategy_store import StrategyStore

router = APIRouter()
store = StrategyStore()

@router.post("/strategies", response_model=str)
async def create_strategy(strategy: StrategyCreate):
    """새로운 전략 생성"""
    try:
        strategy_id = store.create_strategy(strategy.dict())
        return strategy_id
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies", response_model=List[Strategy])
async def get_strategies(active_only: bool = Query(False, description="활성화된 전략만 조회")):
    """전략 목록 조회"""
    try:
        if active_only:
            return store.get_active_strategies()
        return store.get_all_strategies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: str):
    """전략 상세 조회"""
    strategy = store.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    return strategy

@router.put("/strategies/{strategy_id}", response_model=bool)
async def update_strategy(strategy_id: str, strategy: StrategyUpdate):
    """전략 업데이트"""
    try:
        success = store.update_strategy(strategy_id, strategy.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
        return True
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/strategies/{strategy_id}", response_model=bool)
async def delete_strategy(strategy_id: str):
    """전략 삭제"""
    success = store.delete_strategy(strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    return True

@router.post("/strategies/{strategy_id}/backtest", response_model=bool)
async def add_backtest_result(strategy_id: str, result: BacktestResult):
    """백테스트 결과 추가"""
    success = store.add_backtest_result(strategy_id, result.dict())
    if not success:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    return True

@router.get("/strategies/{strategy_id}/backtest", response_model=List[BacktestResult])
async def get_backtest_history(
    strategy_id: str,
    limit: Optional[int] = Query(10, description="조회할 결과 개수")
):
    """백테스트 히스토리 조회"""
    strategy = store.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    
    history = strategy.get("backtest_history", [])
    return history[-limit:] if limit else history 