import streamlit as st
from ...api.client import api_client
from ...components.strategy.form import render_strategy_form
from ...components.backtest.results import render_backtest_results
import logging

logger = logging.getLogger(__name__)

def render():
    """전략 상세 페이지"""
    if not st.session_state.get("current_strategy"):
        st.error("전략 정보를 찾을 수 없습니다.")
        st.session_state.strategy_view_mode = "list"
        st.rerun()
        
    try:
        # 전략 정보
        strategy = st.session_state.current_strategy
        
        st.title(f"📝 전략 상세: {strategy['name']}")
        
        # 상단 버튼
        col1, col2, col3, col4 = st.columns([2, 2, 2, 6])
        
        with col1:
            if st.button("← 목록으로", use_container_width=True):
                st.session_state.strategy_view_mode = "list"
                st.rerun()
                
        with col2:
            if st.button("백테스트", use_container_width=True):
                st.session_state.backtest_strategy = strategy
                st.session_state.current_page = "backtest"
                st.rerun()
                
        with col3:
            is_active = strategy.get("is_active", False)
            status = "비활성화" if is_active else "활성화"
            if st.button(status, use_container_width=True):
                try:
                    success = api_client.update_strategy(
                        strategy["id"],
                        {"is_active": not is_active}
                    )
                    if success:
                        # 로컬 객체도 업데이트
                        strategy["is_active"] = not is_active
                        st.session_state.current_strategy = strategy
                        st.success(f"전략이 {status}되었습니다.")
                        # 세션 상태 강제 리프레시 트리거
                        st.session_state.force_refresh = True
                        st.rerun()
                except Exception as e:
                    logger.error(f"전략 상태 변경 실패: {str(e)}")
                    st.error(f"전략 상태 변경 중 오류가 발생했습니다: {str(e)}")
                    
        # 전략 정보 표시
        st.subheader("기본 정보")
        col1, col2 = st.columns(2)
        
        with col1:
            stock_name = strategy.get('stock_name', '알 수 없음')
            stock_code = strategy.get('stock_code', '알 수 없음')
            st.markdown(f"**종목**: {stock_name} ({stock_code})")
            st.markdown(f"**전략 유형**: {strategy.get('strategy_type', '알 수 없음')}")
            
        with col2:
            is_active = strategy.get("is_active", False)
            status_text = "활성" if is_active else "비활성"
            status_color = "green" if is_active else "red"
            st.markdown(f"**상태**: <span style='color:{status_color}'>{status_text}</span>", unsafe_allow_html=True)
            created_at = strategy.get('created_at', '알 수 없음')
            st.markdown(f"**생성일**: {created_at[:10] if isinstance(created_at, str) and len(created_at) > 10 else created_at}")
            
        # 리스크 관리 설정
        st.subheader("리스크 관리")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            take_profit = strategy.get('take_profit', 0)
            st.metric("익절", f"{take_profit}%")
        with col2:
            stop_loss = strategy.get('stop_loss', 0)
            st.metric("손절", f"{stop_loss}%")
        with col3:
            investment_amount = strategy.get('investment_amount', 0)
            st.metric("투자금", f"{investment_amount:,}원")
            
        # 전략 파라미터
        st.subheader("전략 파라미터")
        params = strategy.get('params', {})
        st.json(params)
        
        # 백테스트 히스토리
        st.subheader("백테스트 히스토리")
        backtest_history = strategy.get('backtest_history', [])
        if backtest_history:
            render_backtest_results(backtest_history)
        else:
            st.info("아직 백테스트 결과가 없습니다.")
            
        # 전략 수정
        with st.expander("전략 수정", expanded=False):
            st.warning("전략을 수정하면 새로운 버전이 생성됩니다.")
            save_clicked, updated_data = render_strategy_form(
                is_edit_mode=True, 
                strategy=strategy,
                on_save=lambda data: _handle_update_strategy(strategy["id"], data),
                on_cancel=lambda: None
            )
                    
    except Exception as e:
        logger.error(f"전략 정보 표시 실패: {str(e)}")
        st.error(f"전략 정보를 표시하는 중 오류가 발생했습니다: {str(e)}")

def _handle_update_strategy(strategy_id, updated_data):
    """전략 수정 처리"""
    try:
        success = api_client.update_strategy(strategy_id, updated_data)
        if success:
            # 성공 처리
            st.success("전략이 수정되었습니다.")
            
            # 전략 정보 다시 조회
            updated_strategy = api_client.get_strategy(strategy_id)
            st.session_state.current_strategy = updated_strategy
            
            # 세션 상태 초기화
            st.session_state.force_refresh = True
            st.rerun()
        else:
            st.error("전략 수정에 실패했습니다.")
    except Exception as e:
        logger.error(f"전략 수정 실패: {str(e)}")
        st.error(f"전략 수정 중 오류가 발생했습니다: {str(e)}") 