"""
종목 검색 컴포넌트 모듈입니다.
"""
import streamlit as st
from typing import Dict, List, Any, Callable, Optional

from ..controllers.stock_controller import StockController

def render_stock_search(
    on_select: Callable[[Dict[str, str]], None],
    controller: Optional[StockController] = None,
    show_popular: bool = True
) -> None:
    """
    종목 검색 컴포넌트 렌더링
    
    Args:
        on_select: 종목 선택 시 호출될 콜백 함수
        controller: 종목 컨트롤러 (없으면 새로 생성)
        show_popular: 인기 종목 표시 여부
    """
    # 컨트롤러가 없으면 새로 생성
    if controller is None:
        controller = StockController()
    
    # 검색어 입력
    query = st.text_input(
        "종목 검색",
        placeholder="종목 코드나 이름을 입력하세요",
        help="종목 코드 또는 종목명의 일부를 입력하면 관련 종목이 검색됩니다."
    )
    
    if query:
        # 검색 결과 표시
        with st.spinner("종목 검색 중..."):
            results = controller.search_stocks(query)
            
            if results:
                st.write("검색 결과:")
                
                # 검색 결과를 버튼으로 표시
                cols = st.columns(2)
                for i, stock in enumerate(results):
                    with cols[i % 2]:
                        if st.button(
                            f"{stock['name']} ({stock['code']})",
                            key=f"stock_search_{stock['code']}",
                            use_container_width=True
                        ):
                            on_select(stock)
            else:
                st.info("검색 결과가 없습니다.")
    
    # 인기 종목 표시
    elif show_popular:
        popular_stocks = controller.get_popular_stocks()
        if popular_stocks:
            st.write("인기 종목:")
            
            # 인기 종목을 버튼으로 표시
            cols = st.columns(2)
            for i, stock in enumerate(popular_stocks):
                with cols[i % 2]:
                    if st.button(
                        f"{stock['name']} ({stock['code']})",
                        key=f"stock_popular_{stock['code']}",
                        use_container_width=True
                    ):
                        on_select(stock)
                        
    # 선택된 종목이 있으면 상세 정보 표시
    if "selected_stock" in st.session_state:
        stock = st.session_state.selected_stock
        with st.expander("선택된 종목 상세 정보", expanded=True):
            # 기본 정보
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**종목코드:** {stock['code']}")
                st.write(f"**종목명:** {stock['name']}")
            
            # 상세 정보 조회
            detail = controller.get_stock_detail(stock['code'])
            if detail:
                with col2:
                    if 'current_price' in detail:
                        st.write(f"**현재가:** {detail['current_price']:,}원")
                    if 'change_percent' in detail:
                        color = 'red' if detail['change_percent'] > 0 else 'blue'
                        st.markdown(f"**등락률:** <span style='color:{color};'>{detail['change_percent']:+.2f}%</span>", unsafe_allow_html=True)
                
                # 추가 정보
                if 'sector' in detail:
                    st.write(f"**업종:** {detail['sector']}")
                if 'market_cap' in detail:
                    market_cap = detail['market_cap']
                    if market_cap >= 1000000000000:
                        st.write(f"**시가총액:** {market_cap/1000000000000:.1f}조원")
                    else:
                        st.write(f"**시가총액:** {market_cap/100000000:.0f}억원") 