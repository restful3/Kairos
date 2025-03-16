import streamlit as st
from ...api.client import api_client
from ...components.strategy.card import render_strategy_grid
from ...components.strategy.filters import render_strategy_filters, filter_strategies
from ...components.search import render_search_box
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def render():
    """전략 목록 페이지 렌더링"""
    st.title("📊 매매 전략 목록")
    
    logger.debug("전략 목록 페이지 렌더링 시작")
    
    # 강제 리프레시 처리
    flush_cache = False
    if st.session_state.get("force_refresh"):
        logger.debug("강제 리프레시 실행")
        if "strategies" in st.session_state:
            del st.session_state.strategies
        st.session_state.force_refresh = False
        flush_cache = True
    
    # 새 전략 생성 버튼
    if st.button("✨ 새 전략 생성", use_container_width=True):
        st.session_state.strategy_view_mode = 'create'
        st.session_state.current_strategy = None
        st.rerun()
    
    # 전략 목록을 항상 새로 불러오기
    try:
        logger.debug("전략 목록 조회 시작")
        strategies = api_client.get_strategies(flush_cache=flush_cache)
        
        # 디버깅 정보 (개발 중에만 사용)
        logger.debug(f"불러온 전략 수: {len(strategies)}")
        
        # 검색 기능
        search_query = render_search_box("전략 이름으로 검색")
        if search_query:
            filtered_strategies = [
                s for s in strategies 
                if search_query.lower() in s["name"].lower()
            ]
            strategies = filtered_strategies
        
        # 전략이 없는 경우 메시지 표시
        if not strategies:
            if search_query:
                st.info(f"'{search_query}' 검색 결과가 없습니다.")
            else:
                st.info("아직 생성된 전략이 없습니다. '새 전략 생성' 버튼을 클릭하여 시작하세요.")
            return
            
        # 전략 카드 그리드 렌더링
        render_strategy_grid(
            strategies=strategies,
            on_view=_handle_view_strategy,
            on_backtest=_handle_backtest_strategy,
            on_edit=_handle_edit_strategy,
            on_toggle=_handle_toggle_strategy,
            on_delete=_handle_delete_strategy
        )
        
    except Exception as e:
        logger.error(f"전략 목록 표시 중 오류: {str(e)}")
        st.error("전략 목록을 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.")

def _handle_view_strategy(strategy):
    """전략 상세 보기 처리"""
    st.session_state.current_strategy = strategy
    st.session_state.strategy_view_mode = 'detail'
    logger.debug(f"전략 상세 보기: {strategy['id']}")
    st.rerun()
    
def _handle_backtest_strategy(strategy):
    """전략 백테스트 처리"""
    st.session_state.backtest_strategy = strategy
    st.session_state.current_page = 'backtest'
    logger.debug(f"전략 백테스트 시작: {strategy['id']}")
    st.rerun()
    
def _handle_edit_strategy(strategy):
    """전략 수정 처리"""
    logger.debug(f"전략 수정 시작: {strategy['id']}")
    
    # 수정할 전략을 세션에 저장
    st.session_state.current_strategy = strategy
    st.session_state.strategy_view_mode = 'edit'
    st.rerun()
    
def _handle_toggle_strategy(strategy):
    """전략 활성화/비활성화 처리"""
    try:
        # 현재 상태 확인 및 반전
        is_active = strategy.get('is_active', False)
        new_status = not is_active
        
        # 업데이트 데이터 생성
        update_data = {
            'is_active': new_status
        }
        
        # 상태가 활성화인 경우 활성화 시간 기록
        if new_status:
            update_data['activated_at'] = str(datetime.now())
        
        # API 호출하여 상태 업데이트
        success = api_client.update_strategy(strategy['id'], update_data)
        
        if success:
            # 성공 처리
            strategy['is_active'] = new_status  # 로컬 객체도 업데이트
            
            if new_status:
                st.success(f"'{strategy['name']}' 전략이 활성화되었습니다.")
            else:
                st.info(f"'{strategy['name']}' 전략이 비활성화되었습니다.")
            
            # 데이터 다시 로드를 위한 플래그 설정
            st.session_state.force_refresh = True
        else:
            st.error("전략 상태 변경에 실패했습니다.")
    
    except Exception as e:
        logger.error(f"전략 상태 변경 실패: {str(e)}")
        st.error(f"전략 상태 변경 중 오류가 발생했습니다: {str(e)}")
        
def _handle_delete_strategy(strategy):
    """전략 삭제 처리"""
    try:
        # API 호출하여 전략 삭제
        success = api_client.delete_strategy(strategy['id'])
        
        if success:
            # 성공 처리
            st.success(f"'{strategy['name']}' 전략이 삭제되었습니다.")
            
            # 데이터 다시 로드를 위한 플래그 설정
            st.session_state.force_refresh = True
            st.rerun()
        else:
            st.error("전략 삭제에 실패했습니다.")
    
    except Exception as e:
        logger.error(f"전략 삭제 실패: {str(e)}")
        st.error(f"전략 삭제 중 오류가 발생했습니다: {str(e)}") 