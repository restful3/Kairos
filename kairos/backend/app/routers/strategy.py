from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..models.strategy import Strategy
from ..services.strategy_store import StrategyStore

router = APIRouter(tags=["strategies"])

strategy_store = StrategyStore()

@router.get("/strategies", response_model=List[Strategy])
async def get_strategies():
    return strategy_store.get_all()

@router.post("/strategies", response_model=Strategy)
async def create_strategy(strategy: Strategy):
    return strategy_store.create(strategy)

@router.get("/strategies/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: str):
    strategy = strategy_store.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy

@router.put("/strategies/{strategy_id}", response_model=Strategy)
async def update_strategy(strategy_id: str, strategy: Strategy):
    updated_strategy = strategy_store.update(strategy_id, strategy)
    if not updated_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return updated_strategy

@router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    if not strategy_store.delete(strategy_id):
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"message": "Strategy deleted"} 