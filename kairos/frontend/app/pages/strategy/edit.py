import streamlit as st
from ...api.client import api_client
from ...components.strategy.form import render_strategy_form
from ...controllers.strategy_controller import StrategyController
from typing import Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

def render():
    """전략 수정 페이지"""
    st.title("✏️ 매매 전략 수정")
    
    logger.debug("전략 수정 페이지 렌더링 시작")
    
    # 현재 수정 중인 전략 정보 가져오기
    strategy = st.session_state.current_strategy
    
    # 상단 버튼 (뒤로 가기)
    if st.button("← 전략 목록으로 돌아가기"):
        logger.debug("전략 목록으로 돌아가기 버튼 클릭")
        st.session_state.strategy_view_mode = "list"
        st.rerun()
    
    # 안내 메시지
    st.info(f"'{strategy.get('name', '')}' 전략의 내용을 수정하세요. 모든 필수 항목(*)을 입력해야 합니다.")
    
    # 전략 컨트롤러 초기화
    if "strategy_controller" not in st.session_state:
        logger.debug("전략 컨트롤러 초기화")
        st.session_state.strategy_controller = StrategyController()
    
    # 폼 초기화 상태 초기화 (수정 모드에서는 매번 폼을 초기화해야 함)
    if "form_initialized" in st.session_state:
        del st.session_state.form_initialized
    
    # 전략 폼 렌더링
    logger.debug("전략 폼 렌더링 시작")
    save_clicked, strategy_data = render_strategy_form(
        is_edit_mode=True,
        strategy=strategy,
        on_save=_handle_update_strategy,
        on_cancel=_handle_cancel,
        controller=st.session_state.strategy_controller
    )

def _handle_update_strategy(form_data: Dict[str, Any]):
    """전략 수정 처리"""
    try:
        strategy_id = st.session_state.current_strategy.get('id')
        logger.debug(f"전략 수정 시도: {strategy_id} - {form_data.get('name', '알 수 없음')}")
        
        # 전략 수정 요청
        success = api_client.update_strategy(strategy_id, form_data)
        
        if success:
            logger.info(f"전략 수정 성공 - ID: {strategy_id}")
            
            # 전략 수정 성공 알림
            st.success("전략이 성공적으로 수정되었습니다!")
            
            # 세션 상태 초기화
            st.session_state.force_refresh = True
            
            # 전략 목록 페이지로 이동
            st.session_state.strategy_view_mode = "list"
            st.rerun()
        else:
            logger.error("전략 수정 실패")
            st.error("전략 수정에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"전략 수정 실패: {str(e)}")
        st.error(f"전략 수정 중 오류가 발생했습니다: {str(e)}")

def _handle_cancel():
    """취소 처리"""
    logger.debug("전략 수정 취소")
    st.session_state.strategy_view_mode = "list"
    st.rerun() 