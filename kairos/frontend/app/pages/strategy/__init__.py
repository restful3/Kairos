"""
전략 관리 페이지 패키지 초기화 모듈입니다.
이 모듈은 전략 목록, 생성, 수정, 상세보기 등의 기능을 제공합니다.
"""
import streamlit as st
import logging

from .list import render as render_list
from .create import render as render_create
from .detail import render as render_detail
from .edit import render as render_edit

logger = logging.getLogger(__name__)

def render():
    """전략 페이지 렌더링 - 세션 상태에 따라 적절한 하위 페이지 표시"""
    
    # 전략 뷰 모드 초기화 (없는 경우)
    if 'strategy_view_mode' not in st.session_state:
        st.session_state.strategy_view_mode = 'list'
    
    # 현재 전략 초기화 (없는 경우)
    if 'current_strategy' not in st.session_state:
        st.session_state.current_strategy = None
    
    # 현재 뷰 모드에 따라 적절한 페이지 렌더링
    view_mode = st.session_state.strategy_view_mode
    
    if view_mode == 'list':
        render_list()
    elif view_mode == 'create':
        render_create()
    elif view_mode == 'edit':
        if st.session_state.current_strategy:
            render_edit()
        else:
            # 수정할 전략이 없는 경우 목록으로 리다이렉트
            st.session_state.strategy_view_mode = 'list'
            render_list()
    elif view_mode == 'detail':
        if st.session_state.current_strategy:
            render_detail()
        else:
            # 현재 전략이 없는 경우 목록으로 리다이렉트
            st.session_state.strategy_view_mode = 'list'
            render_list()
    else:
        # 알 수 없는 뷰 모드인 경우 목록으로 리다이렉트
        logger.error(f"알 수 없는 전략 뷰 모드: {view_mode}")
        st.session_state.strategy_view_mode = 'list'
        render_list() 