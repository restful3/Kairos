"""
전략 필터 컴포넌트 모듈입니다.
"""
import streamlit as st
import logging
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger(__name__)

def render_strategy_filters(
    filter_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    전략 필터 컴포넌트를 렌더링합니다.
    
    Args:
        filter_callback: 필터 변경 시 호출할 콜백 함수
        
    Returns:
        필터 옵션 딕셔너리
    """
    # 세션 상태에서 필터 가져오기
    if "strategy_filters" not in st.session_state:
        st.session_state.strategy_filters = {
            "show_active_only": False,
            "strategy_type": "모두",
            "sort_by": "생성일",
            "sort_order": "내림차순"
        }
    
    filters = st.session_state.strategy_filters
    
    # 필터 섹션 시작
    with st.expander("전략 필터", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # 활성화 필터
            show_active_only = st.checkbox(
                "활성화된 전략만 표시",
                value=filters.get("show_active_only", False),
                key="filter_active_only"
            )
            
            # 전략 유형 필터
            strategy_types = [
                "모두", "이동평균 교차", "골든/데드 크로스", 
                "볼린저 밴드", "RSI 과매수/과매도", "MACD 시그널", 
                "가격 돌파", "그물망 매매"
            ]
            
            strategy_type = st.selectbox(
                "전략 유형",
                options=strategy_types,
                index=strategy_types.index(filters.get("strategy_type", "모두")),
                key="filter_strategy_type"
            )
        
        with col2:
            # 정렬 옵션
            sort_options = [
                "생성일", "수정일", "이름", "종목", "수익률"
            ]
            
            sort_by = st.selectbox(
                "정렬 기준",
                options=sort_options,
                index=sort_options.index(filters.get("sort_by", "생성일")),
                key="filter_sort_by"
            )
            
            # 정렬 방향
            sort_orders = ["오름차순", "내림차순"]
            sort_order = st.selectbox(
                "정렬 방향",
                options=sort_orders,
                index=sort_orders.index(filters.get("sort_order", "내림차순")),
                key="filter_sort_order"
            )
        
        # 필터 적용 버튼
        if st.button("필터 적용", use_container_width=True):
            # 필터 값 업데이트
            filters.update({
                "show_active_only": show_active_only,
                "strategy_type": strategy_type,
                "sort_by": sort_by,
                "sort_order": sort_order
            })
            
            # 세션 상태 업데이트
            st.session_state.strategy_filters = filters
            
            # 콜백 호출
            if filter_callback:
                filter_callback(filters)
                
            st.rerun()
    
    return filters

def filter_strategies(
    strategies: List[Dict[str, Any]], 
    filters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    필터에 따라 전략 목록을 필터링합니다.
    
    Args:
        strategies: 원본 전략 목록
        filters: 필터 옵션 딕셔너리
        
    Returns:
        필터링된 전략 목록
    """
    result = strategies.copy()
    
    # 활성화 필터 적용
    if filters.get("show_active_only", False):
        result = [s for s in result if s.get("is_active", False)]
    
    # 전략 유형 필터 적용
    strategy_type = filters.get("strategy_type", "모두")
    if strategy_type != "모두":
        result = [s for s in result if s.get("strategy_type", "") == strategy_type]
    
    # 정렬 적용
    sort_by = filters.get("sort_by", "생성일")
    sort_order = filters.get("sort_order", "내림차순")
    reverse = (sort_order == "내림차순")
    
    # 정렬 키 함수 설정
    if sort_by == "생성일":
        key_func = lambda s: s.get("created_at", "")
    elif sort_by == "수정일":
        key_func = lambda s: s.get("updated_at", s.get("created_at", ""))
    elif sort_by == "이름":
        key_func = lambda s: s.get("name", "").lower()
    elif sort_by == "종목":
        key_func = lambda s: s.get("stock_name", "").lower()
    elif sort_by == "수익률":
        # 가장 최근 백테스트 결과 기준 수익률
        key_func = lambda s: (s.get("backtest_history", [{}])[-1].get("metrics", {}).get("total_return", 0) 
                             if s.get("backtest_history") else 0)
    else:
        key_func = lambda s: s.get("created_at", "")
    
    # 정렬 실행
    result.sort(key=key_func, reverse=reverse)
    
    return result 