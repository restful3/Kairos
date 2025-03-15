from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.schemas.auth import AccountBalance, ErrorResponse
from app.services.kis_service import KisService
from app.core.security import get_current_user

router = APIRouter()

@router.get("/balance", response_model=AccountBalance, responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_account_balance(user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    현재 계좌의 잔고 정보를 조회합니다.
    
    - 예수금
    - 보유종목 목록
    - 총평가금액
    - 총매입금액
    
    Returns:
        계좌 잔고 정보
    """
    try:
        # KIS API 서비스 초기화
        kis_service = KisService()
        
        # 계좌 잔고 조회
        balance_data = kis_service.get_account_balance()
        
        # 에러 처리
        if "error" in balance_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=balance_data.get("error", "계좌 잔고 조회 중 오류가 발생했습니다.")
            )
        
        return balance_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"계좌 잔고 조회 중 오류가 발생했습니다: {str(e)}"
        ) 