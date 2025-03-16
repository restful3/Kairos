"""
검색 컴포넌트 모듈입니다.
"""
import streamlit as st
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def render_search_box(
    label: str = "검색", 
    key: Optional[str] = None, 
    placeholder: Optional[str] = None
) -> str:
    """
    검색 입력 박스를 렌더링합니다.
    
    Args:
        label: 검색 레이블
        key: 세션 상태 키 (없으면 자동 생성)
        placeholder: 입력 박스의 안내 텍스트
    
    Returns:
        입력된 검색어
    """
    # 키 생성
    if key is None:
        key = f"search_box_{label.lower().replace(' ', '_')}"
    
    # 기본 플레이스홀더 텍스트
    if placeholder is None:
        placeholder = f"{label}..."
    
    # 이전 검색어 불러오기
    prev_search = st.session_state.get(key, "")
    
    # 검색 입력 박스 표시 - 값 변경 시 세션 상태가 자동으로 업데이트됨
    search_query = st.text_input(
        label,
        value=prev_search,
        placeholder=placeholder,
        key=key
    )
    
    # 주의: 위젯 생성 후에는 해당 키의 세션 상태를 직접 수정하면 안 됨
    # st.session_state[key] = search_query  # 이 부분 제거
    
    return search_query 