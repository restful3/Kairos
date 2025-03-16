"""
전략 카드 컴포넌트 모듈입니다.
"""
import streamlit as st
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

def render_strategy_card(
    strategy: Dict[str, Any],
    on_view: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_backtest: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_edit: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_toggle: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_delete: Optional[Callable[[Dict[str, Any]], None]] = None
):
    """전략 카드 렌더링
    
    Args:
        strategy: 전략 정보 딕셔너리
        on_view: 상세 보기 핸들러
        on_backtest: 백테스팅 핸들러
        on_edit: 수정 핸들러
        on_toggle: 활성화/비활성화 토글 핸들러
        on_delete: 삭제 핸들러
    """
    with st.container():
        # 상태 클래스 및 텍스트 설정
        is_active = strategy.get("is_active", False)
        status_class = "active" if is_active else "inactive"
        status_text = "✅ 활성" if is_active else "⏸️ 비활성"
        
        # 생성일/수정일 포맷팅
        created_at = strategy.get("created_at", "")
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = created_dt.strftime("%Y-%m-%d %H:%M")
            except Exception as e:
                logger.warning(f"날짜 파싱 오류: {str(e)}")
        
        # 전략 카드 HTML 생성
        st.markdown(f'''
        <div class="strategy-card">
            <h3>{strategy.get("name", "무제 전략")}</h3>
            <div class="strategy-info">
                <strong>종목:</strong> {strategy.get("stock_name", "")} ({strategy.get("stock_code", "")})
            </div>
            <div class="strategy-info">
                <strong>전략:</strong> {strategy.get("strategy_type", "")}
            </div>
            <div class="strategy-details">
                <div class="strategy-info">
                    <strong>익절:</strong> {strategy.get("take_profit", 0)}%
                </div>
                <div class="strategy-info">
                    <strong>손절:</strong> {strategy.get("stop_loss", 0)}%
                </div>
                <div class="strategy-info">
                    <strong>생성일:</strong> {created_at}
                </div>
            </div>
            <div class="strategy-status {status_class}">
                {status_text}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 버튼 행
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # 상세 보기 버튼
        with col1:
            if st.button("상세보기", key=f"view_{strategy.get('id', '')}", use_container_width=True):
                if on_view:
                    on_view(strategy)
        
        # 백테스트 버튼
        with col2:
            if st.button("백테스트", key=f"backtest_{strategy.get('id', '')}", use_container_width=True):
                if on_backtest:
                    on_backtest(strategy)
        
        # 수정하기 버튼
        with col3:
            if st.button("수정하기", key=f"edit_{strategy.get('id', '')}", use_container_width=True):
                if on_edit:
                    on_edit(strategy)
        
        # 활성화/비활성화 토글 버튼
        with col4:
            toggle_label = "비활성화" if is_active else "활성화"
            if st.button(toggle_label, key=f"toggle_{strategy.get('id', '')}", use_container_width=True):
                if on_toggle:
                    on_toggle(strategy)
        
        # 삭제 버튼
        with col5:
            # 삭제 확인 상태 확인
            delete_confirm_key = f"delete_confirm_{strategy.get('id', '')}"
            delete_confirm = st.session_state.get(delete_confirm_key, False)
            
            # 버튼 레이블 및 스타일 설정
            if delete_confirm:
                button_label = "삭제 확인"
                button_style = "delete-confirm-button"
            else:
                button_label = "삭제"
                button_style = ""
            
            # 삭제 버튼 렌더링
            button_clicked = st.button(
                button_label, 
                key=f"delete_{strategy.get('id', '')}", 
                use_container_width=True,
                type="primary" if delete_confirm else "secondary"
            )
            
            if button_clicked:
                if delete_confirm:
                    # 삭제 확인 상태에서 클릭: 실제 삭제 실행
                    if on_delete:
                        # 삭제 플래그 초기화
                        st.session_state[delete_confirm_key] = False
                        on_delete(strategy)
                else:
                    # 첫 클릭: 확인 상태로 변경
                    st.session_state[delete_confirm_key] = True
                    st.rerun()

def render_strategy_grid(
    strategies: List[Dict[str, Any]],
    on_view: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_backtest: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_edit: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_toggle: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_delete: Optional[Callable[[Dict[str, Any]], None]] = None
):
    """전략 그리드 렌더링
    
    Args:
        strategies: 전략 목록
        on_view: 상세 보기 핸들러
        on_backtest: 백테스팅 핸들러
        on_edit: 수정 핸들러
        on_toggle: 활성화/비활성화 토글 핸들러
        on_delete: 삭제 핸들러
    """
    # CSS 스타일 삽입
    st.markdown("""
    <style>
    .strategy-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        position: relative;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .strategy-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .strategy-card h3 {
        margin-top: 0;
        margin-bottom: 10px;
        color: #1e3a8a;
        font-size: 1.2rem;
    }
    .strategy-info {
        margin-bottom: 5px;
        font-size: 0.9rem;
    }
    .strategy-details {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .strategy-status {
        position: absolute;
        top: 15px;
        right: 15px;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .strategy-status.active {
        background-color: rgba(0, 200, 0, 0.2);
        color: #008800;
    }
    .strategy-status.inactive {
        background-color: rgba(200, 200, 200, 0.3);
        color: #666666;
    }
    /* 삭제 확인 버튼 스타일 */
    button[data-testid="baseButton-primary"] {
        background-color: #ff5252 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 전략이 없는 경우 처리
    if not strategies:
        st.info("표시할 전략이 없습니다.")
        return
    
    # 전략 카드 그리드 렌더링
    for strategy in strategies:
        render_strategy_card(
            strategy=strategy,
            on_view=on_view,
            on_backtest=on_backtest,
            on_edit=on_edit,
            on_toggle=on_toggle,
            on_delete=on_delete
        ) 