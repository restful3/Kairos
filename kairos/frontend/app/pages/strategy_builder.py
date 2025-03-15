import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import random  # 임시 데이터 생성용
import time

from app.api.client import api_client
from app.utils.session import is_logged_in
from app.utils.styles import load_common_styles  # 공통 스타일을 별도 모듈로 임포트
from app.utils.backtest_utils import run_backtest_simulation  # 백테스팅 유틸리티 임포트

# 전략 저장/로드 경로 설정
STRATEGIES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "strategies")
os.makedirs(STRATEGIES_DIR, exist_ok=True)

# 전략 저장 및 로드 함수
def save_strategies(user_id="default"):
    """전략 데이터를 JSON 파일로 저장"""
    filename = os.path.join(STRATEGIES_DIR, f"{user_id}_strategies.json")
    
    # 타임스탬프 추가하여 저장 (마지막 저장 시간)
    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "strategies": st.session_state.saved_strategies
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"전략 데이터 저장 완료: {filename}")
    return filename

def load_strategies(user_id="default"):
    """JSON 파일에서 전략 데이터 로드"""
    filename = os.path.join(STRATEGIES_DIR, f"{user_id}_strategies.json")
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("strategies", [])
        except Exception as e:
            print(f"전략 데이터 로드 오류: {str(e)}")
            return []
    
    return []

# 세션 상태 초기화 함수
def initialize_session_state():
    """세션 상태 초기화"""
    # 로그인 확인
    if not is_logged_in():
        st.warning("매매 전략 생성을 위해서는 로그인이 필요합니다. 로그인 후 전략 저장 및 백테스팅이 가능합니다.")
    
    # 전략 데이터 로드 (세션에 없는 경우)
    if "saved_strategies" not in st.session_state:
        user_id = st.session_state.get("user_id", "default")
        st.session_state.saved_strategies = load_strategies(user_id)
        st.info(f"저장된 전략 {len(st.session_state.saved_strategies)}개를 불러왔습니다.")
    
    # 탭 상태 초기화
    if "strategy_tab" not in st.session_state:
        st.session_state.strategy_tab = 0
        
    # 백테스팅 모달 상태 초기화
    if "show_backtest_modal" not in st.session_state:
        st.session_state.show_backtest_modal = False
    
    # 간략 백테스팅 결과 상태 초기화
    if "show_simplified_result" not in st.session_state:
        st.session_state.show_simplified_result = False
    
    # 삭제 확인 대화상자 상태 초기화
    if "delete_confirm" not in st.session_state:
        st.session_state.delete_confirm = False
    
    # 실제 데이터 사용 여부 초기화
    if "use_real_data_for_simplified" not in st.session_state:
        st.session_state.use_real_data_for_simplified = True
    
    # 페이지 타이틀 설정
    st.title("매매 전략 생성")

# 기본 CSS 스타일 정의
def load_css():
    """전략 생성 페이지용 CSS 스타일을 로드합니다"""
    # 공통 스타일 로드
    load_common_styles()
    
    # 페이지 전용 추가 스타일
    st.markdown("""
    <style>
    .strategy-card {
        background-color: #f0f7ff;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #1d3557;
        height: 100%;
        position: relative;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .strategy-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .strategy-card h3 {
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 1.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .strategy-info {
        margin-bottom: 10px;
    }
    
    .strategy-status {
        font-size: 0.9rem;
        padding: 3px 8px;
        border-radius: 10px;
        background-color: #f0f0f0;
        display: inline-block;
        margin-top: 8px;
    }
    
    .strategy-status.active {
        background-color: #d1ffd1;
        color: #008800;
    }
    
    .strategy-status.inactive {
        background-color: #f0f0f0;
        color: #666;
    }
    
    .backtest-summary {
        margin-top: 10px;
        font-size: 0.9rem;
        padding: 5px;
        background-color: #f8f8f8;
        border-radius: 5px;
    }
    
    .backtest-result {
        font-weight: bold;
    }
    
    .backtest-result.positive {
        color: #e63946;
    }
    
    .backtest-result.negative {
        color: #1d3557;
    }
    
    .parameter-section {
        background-color: #fcfcfc;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    .filter-bar {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 간략 백테스팅 함수 추가
def run_simplified_backtest(strategy):
    """간략 백테스팅 실행"""
    try:
        from app.utils.backtest_utils import run_backtest_simulation
        
        # 실제 데이터 사용 여부 확인
        use_real_data = st.session_state.get("use_real_data_for_simplified", True)
        
        # 30일 기간, 1천만원 초기 자본금, 0.15% 수수료로 백테스트 실행
        result = run_backtest_simulation(
            strategy=strategy,
            days=30,  # 간략 백테스팅은 30일로 고정
            initial_capital=10000000,
            fee_rate=0.0015,  # 0.15%
            simplified=True,  # 간략 백테스팅임을 표시
            use_real_data=use_real_data
        )
        
        # 백테스팅 결과 저장
        st.session_state.simplified_backtest_result = result
        
        # 백테스트 이력 저장
        if "backtest_history" not in strategy:
            strategy["backtest_history"] = []
            
        # 백테스트 이력에 결과 추가
        strategy["backtest_history"].append({
            "date": result["date"],
            "return": result["metrics"]["total_return"],
            "win_rate": result["metrics"]["win_rate"],
            "max_drawdown": result["metrics"]["max_drawdown"],
            "simplified": True,
            "days": 30,
            "use_real_data": use_real_data
        })
        
        # 업데이트된 전략 세션 상태에 저장
        user_id = st.session_state.get("user_id", "default")
        update_strategy_in_saved_list(strategy)
        save_strategies(user_id)
        
        return result
    except Exception as e:
        st.error(f"백테스팅 실행 중 오류가 발생했습니다: {str(e)}")
        return None

def show_simplified_backtest_result(result):
    """간략한 백테스팅 결과 표시"""
    strategy = result["strategy"]
    metrics = result["metrics"]
    portfolio_values = result["portfolio_values"]
    stock_data = result["stock_data"]
    
    st.markdown(f"### '{strategy['name']}' 백테스팅 결과")
    
    # 요약 지표
    col1, col2, col3 = st.columns(3)
    
    with col1:
        return_color = "positive" if metrics["total_return"] > 0 else "negative"
        st.markdown(f'''
        <div style="text-align: center; padding: 10px; background-color: #f0f7ff; border-radius: 5px;">
            <div style="font-size: 0.9rem;">총 수익률</div>
            <div style="font-size: 1.4rem;" class="{return_color}">{metrics["total_return"]}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div style="text-align: center; padding: 10px; background-color: #f0f7ff; border-radius: 5px;">
            <div style="font-size: 0.9rem;">승률</div>
            <div style="font-size: 1.4rem;">{metrics["win_rate"]}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div style="text-align: center; padding: 10px; background-color: #f0f7ff; border-radius: 5px;">
            <div style="font-size: 0.9rem;">최대 낙폭</div>
            <div style="font-size: 1.4rem; color: #1d3557;">{metrics["max_drawdown"]}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # 백테스팅 기간
    if portfolio_values:
        start_date = portfolio_values[0]['date'].strftime("%Y-%m-%d")
        end_date = portfolio_values[-1]['date'].strftime("%Y-%m-%d")
        st.markdown(f"**백테스팅 기간:** {start_date} ~ {end_date}")
    
    # 차트 (예시)
    portfolio_df = pd.DataFrame(portfolio_values)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio_df['date'],
        y=portfolio_df['total_value'],
        mode='lines',
        name='포트폴리오 가치'
    ))
    
    # 기준선 (100%) 추가
    fig.add_hline(y=result['backtest_params']['initial_capital'], line_dash="dash", line_color="#999")
    
    fig.update_layout(
        title="백테스팅 자산 가치 추이",
        xaxis_title="날짜",
        yaxis_title="자산 가치 (원)",
        height=300,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 거래 내역 (최대 5개만 표시)
    trades = result["trades"]
    if trades:
        st.markdown("#### 주요 거래 내역")
        trades_df = pd.DataFrame(trades[:5])
        st.dataframe(trades_df, use_container_width=True)
    
    # 전체 결과 보기 버튼
    if st.button("전체 백테스팅 결과 보기", use_container_width=True, key="show_full_backtest_result"):
        st.session_state.backtest_full_result = result
        st.success("백테스팅 페이지로 이동합니다. '백테스팅' 메뉴를 선택하세요.")
        
    # 결과 닫기 버튼 추가
    if st.button("결과 닫기", use_container_width=True, key="close_simplified_result"):
        st.session_state.show_simplified_result = False
        st.rerun()

def show():
    """전략 생성 및 관리 페이지 표시"""
    # 세션 상태 초기화
    initialize_session_state()
    
    # CSS 스타일 로드
    load_css()
    
    # 전략 탭 선택 (radio 버튼으로 구현)
    tab_names = ["내 전략 목록", "새 전략 만들기"]
    selected_tab = st.radio(
        "전략 탭 선택",
        tab_names,
        index=st.session_state.strategy_tab,
        horizontal=True,
        label_visibility="collapsed",
        key="strategy_tabs_radio"
    )
    
    # 선택된 탭 인덱스 저장
    st.session_state.strategy_tab = tab_names.index(selected_tab)
    
    # 선택된 탭에 따라 다른 내용 표시
    if selected_tab == "내 전략 목록":
        show_strategy_list()
    elif selected_tab == "새 전략 만들기":
        create_new_strategy()
    
    # 백테스팅 모달 창 표시
    if st.session_state.show_backtest_modal:
        show_backtest_modal()
    
    # 간략 백테스팅 결과 표시
    if st.session_state.show_simplified_result and hasattr(st.session_state, 'simplified_backtest_result'):
        show_simplified_backtest_result(st.session_state.simplified_backtest_result)

def show_strategy_list():
    """사용자의 저장된 전략 목록 표시"""
    st.markdown('<div class="section-header">저장된 전략 목록</div>', unsafe_allow_html=True)
    
    # 세션 상태에서 저장된 전략 목록 가져오기
    if "saved_strategies" not in st.session_state:
        st.session_state.saved_strategies = []
    
    if not st.session_state.saved_strategies:
        st.info("저장된 전략이 없습니다. '새 전략 만들기' 탭에서 전략을 생성해 보세요.")
        return
    
    # 필터 및 정렬 옵션
    with st.expander("전략 필터 및 정렬 옵션", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # 상태 필터링
            status_options = ["활성", "비활성"]
            filter_status = st.multiselect(
                "상태 필터링",
                options=status_options,
                default=status_options
            )
            
            # 전략 유형 필터링
            strategy_types = list(set(s["strategy_type"] for s in st.session_state.saved_strategies))
            filter_type = st.multiselect(
                "전략 유형",
                options=strategy_types,
                default=strategy_types
            )
        
        with col2:
            # 정렬 기준
            sort_by = st.selectbox(
                "정렬 기준",
                options=["생성일", "전략명", "종목명"],
                index=0
            )
            
            # 정렬 순서
            sort_order = st.radio(
                "정렬 순서",
                options=["내림차순", "오름차순"],
                index=0,
                horizontal=True
            )
    
    # 필터 및 정렬 적용
    filtered_strategies = st.session_state.saved_strategies.copy()
    
    # 상태 필터 적용
    if "활성" in filter_status and "비활성" in filter_status:
        pass  # 모든 전략 표시
    elif "활성" in filter_status:
        filtered_strategies = [s for s in filtered_strategies if s.get("is_active", False)]
    elif "비활성" in filter_status:
        filtered_strategies = [s for s in filtered_strategies if not s.get("is_active", False)]
    
    # 전략 유형 필터 적용
    if filter_type:
        filtered_strategies = [s for s in filtered_strategies if s["strategy_type"] in filter_type]
    
    # 정렬 적용
    if sort_by == "생성일":
        filtered_strategies.sort(key=lambda x: x.get("created_at", ""), reverse=(sort_order == "내림차순"))
    elif sort_by == "전략명":
        filtered_strategies.sort(key=lambda x: x.get("name", ""), reverse=(sort_order == "내림차순"))
    elif sort_by == "종목명":
        filtered_strategies.sort(key=lambda x: x.get("stock_name", ""), reverse=(sort_order == "내림차순"))
    
    # 그리드 레이아웃으로 전략 카드 표시
    col_count = 2  # 한 행에 표시할 전략 카드 수
    
    # 필터링된 전략이 없는 경우
    if not filtered_strategies:
        st.warning("필터 조건에 맞는 전략이 없습니다. 필터를 변경해 보세요.")
        return
    
    # 전략 카드 그리드로 표시
    rows = [filtered_strategies[i:i+col_count] for i in range(0, len(filtered_strategies), col_count)]
    
    for row_idx, row in enumerate(rows):
        cols = st.columns(col_count)
        
        for col_idx, strategy in enumerate(row):
            if col_idx < len(cols):
                with cols[col_idx]:
                    with st.container():
                        # 인덱스 계산
                        strategy_idx = row_idx * col_count + col_idx
                        original_idx = st.session_state.saved_strategies.index(strategy)
                        
                        # 전략 카드 HTML
                        status_class = "active" if strategy.get("is_active", False) else "inactive"
                        status_text = "✅ 활성" if strategy.get("is_active", False) else "⏸️ 비활성"
                        
                        st.markdown(f'''
                        <div class="strategy-card">
                            <h3>{strategy["name"]}</h3>
                            <div class="strategy-info"><strong>종목:</strong> {strategy["stock_name"]} ({strategy["stock_code"]})</div>
                            <div class="strategy-info"><strong>전략:</strong> {strategy["strategy_type"]}</div>
                            <div class="strategy-info"><strong>생성일:</strong> {strategy.get("created_at", "N/A")}</div>
                            <div class="strategy-status {status_class}">{status_text}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # 백테스팅 결과가 있으면 표시
                        if 'backtest_history' in strategy and strategy['backtest_history']:
                            last_backtest = strategy['backtest_history'][-1]
                            result_class = "positive" if last_backtest['return'] > 0 else "negative"
                            
                            st.markdown(f'''
                            <div class="backtest-summary">
                                <div>최근 백테스팅: {last_backtest['date']}</div>
                                <div class="backtest-result {result_class}">
                                    수익률: {last_backtest['return']:.2f}%
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        # 액션 버튼
                        b1, b2, b3 = st.columns(3)
                        with b1:
                            if st.button("상세 보기", key=f"view_{original_idx}", use_container_width=True):
                                st.session_state.view_strategy = strategy
                                st.session_state.view_strategy_index = original_idx
                                st.rerun()
                        
                        with b2:
                            if st.button("백테스팅", key=f"backtest_{original_idx}", use_container_width=True):
                                st.session_state.backtest_strategy = strategy
                                st.session_state.show_backtest_modal = True
                                st.rerun()
                        
                        with b3:
                            is_active = strategy.get("is_active", False)
                            if st.button(
                                "비활성화" if is_active else "활성화", 
                                key=f"toggle_{original_idx}",
                                use_container_width=True
                            ):
                                st.session_state.saved_strategies[original_idx]["is_active"] = not is_active
                                status = "활성화" if not is_active else "비활성화"
                                
                                # 전략 상태 변경 후 저장
                                user_id = st.session_state.get("user_id", "default")
                                save_strategies(user_id)
                                
                                st.success(f"'{strategy['name']}' 전략이 {status}되었습니다.")
                                st.rerun()

def show_backtest_modal():
    """백테스팅 모달 표시"""
    # 대화상자 대신 컨테이너 사용
    with st.container():
        st.subheader("백테스팅 옵션")
        
        # 배경색을 넣어 모달처럼 보이도록 스타일 적용
        st.markdown("""
        <style>
        .backtest-modal {
            background-color: #f9f9f9;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        </style>
        <div class="backtest-modal">
        """, unsafe_allow_html=True)
        
        # 선택된 전략 정보 표시
        if not hasattr(st.session_state, 'backtest_strategy'):
            st.warning("선택된 전략이 없습니다. 전략 목록으로 돌아가 전략을 선택해주세요.")
            
            if st.button("닫기", use_container_width=True, key="backtest_modal_close"):
                st.session_state.show_backtest_modal = False
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)
            return
            
        strategy = st.session_state.backtest_strategy
        st.markdown(f"**선택된 전략:** {strategy['name']} ({strategy['stock_name']})")
        
        # 개발 중 안내 메시지
        st.info("현재는 개발 단계로, 시뮬레이션 데이터만 사용 가능합니다.")
        
        # 백테스팅 옵션 선택
        backtest_option = st.radio(
            "백테스팅 옵션",
            ["백테스팅 페이지로 이동", "간략 백테스팅 실행"],
            index=0,
            key="backtest_modal_option"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("확인", use_container_width=True, key="backtest_modal_confirm"):
                if backtest_option == "백테스팅 페이지로 이동":
                    # 백테스팅 파라미터 설정
                    st.session_state.backtest_params = {
                        "period": "최근 3개월",
                        "initial_capital": 10000000,
                        "fee_rate": 0.015
                    }
                    
                    # 페이지 이동
                    st.session_state.page = "백테스팅"  # 한글 페이지 이름으로 변경
                    st.session_state.menu_index = 3  # 백테스팅 메뉴 인덱스 (main.py에서 메뉴 인덱스 사용)
                    
                    # 모달 닫기
                    st.session_state.show_backtest_modal = False
                    st.rerun()
                
                elif backtest_option == "간략 백테스팅 실행":
                    # 간략 백테스팅 실행
                    with st.spinner("간략 백테스팅을 실행 중입니다..."):
                        # 실제 백테스팅 실행 함수 호출
                        result = run_simplified_backtest(strategy)
                        
                        if result:
                            # 백테스팅 결과 표시 상태 설정
                            st.session_state.show_simplified_result = True
                            st.session_state.simplified_backtest_result = result
                            
                            # 모달 닫기 처리
                            st.session_state.show_backtest_modal = False
                            st.rerun()
                        else:
                            st.error("백테스팅 실행 중 오류가 발생했습니다.")
                            st.session_state.show_backtest_modal = False
                            st.rerun()
            
            with col2:
                if st.button("취소", use_container_width=True, key="backtest_modal_cancel"):
                    st.session_state.show_backtest_modal = False
                    del st.session_state.backtest_strategy
                    st.rerun()
                
        # 모달 스타일 닫기 태그
        st.markdown("</div>", unsafe_allow_html=True)

def create_new_strategy():
    """새로운 자동 매매 전략 생성 UI"""
    st.markdown('<div class="section-header">새 전략 만들기</div>', unsafe_allow_html=True)
    
    # 편집 모드인지 확인
    is_edit_mode = hasattr(st.session_state, 'edit_strategy')
    
    # 변수 초기화
    stock_search = ""
    
    # 전략 기본 정보 입력
    with st.container():
        st.markdown("### 기본 정보")
        
        if is_edit_mode:
            strategy = st.session_state.edit_strategy
            strategy_name = st.text_input("전략 이름", value=strategy["name"])
        else:
            strategy_name = st.text_input("전략 이름", value="나의 자동 매매 전략")
        
        # 종목 검색 및 선택
        st.markdown("### 종목 선택")
        
        # 사용 안내 메시지
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px; border-left: 3px solid #4CAF50;">
        <small>종목명이나 코드로 검색하여 전략에 사용할 종목을 선택하세요. 예: 삼성전자, 005930</small>
        </div>
        """, unsafe_allow_html=True)
        
        # 검색어가 없을 때 인기 종목 표시
        if not stock_search and not is_edit_mode:
            try:
                # 인기 종목 가져오기
                popular_stocks = api_client.get_popular_stocks(limit=5)
                
                if popular_stocks and len(popular_stocks) > 0:
                    st.info("인기 종목 바로 선택하기")
                    
                    # 인기 종목 그리드 표시
                    cols = st.columns(len(popular_stocks))
                    
                    for i, stock in enumerate(popular_stocks):
                        with cols[i]:
                            stock_name = stock.get('name', '종목명')
                            stock_code = stock.get('code', '000000')
                            current_price = stock.get('current_price', 'N/A')
                            
                            # 가격 변동률 표시 (있을 경우)
                            change_text = ""
                            if 'change_percent' in stock:
                                change = stock['change_percent']
                                color = 'red' if change > 0 else 'blue'
                                change_text = f"<span style='color:{color};'>({change:+.2f}%)</span>"
                            
                            html = f"""
                            <div style="text-align: center; padding: 10px; background-color: #f8f9fa; 
                                 border-radius: 5px; cursor: pointer; height: 100%;"
                                 onclick="this.style.backgroundColor='#e2e6ea'">
                                <div style="font-weight: bold;">{stock_name}</div>
                                <div style="font-size: 0.8rem; color: #666;">{stock_code}</div>
                                <div>{current_price:,}원 {change_text}</div>
                            </div>
                            """
                            
                            st.markdown(html, unsafe_allow_html=True)
                            
                            # 버튼 클릭 시 해당 종목 선택
                            if st.button(f"선택", key=f"select_{stock_code}", use_container_width=True):
                                stock_search = stock_name
                                # 세션 상태에 검색어 저장
                                st.session_state.stock_search = stock_name
                                st.rerun()
            except Exception as e:
                st.warning(f"인기 종목을 가져오는 중 오류가 발생했습니다: {str(e)}")
        
        # 세션에서 검색어 가져오기 (인기 종목 선택 시)
        if hasattr(st.session_state, 'stock_search'):
            stock_search = st.session_state.stock_search
            # 사용 후 세션에서 제거
            del st.session_state.stock_search
        
        stock_search = st.text_input(
            "종목명 또는 코드 검색", 
            value=stock_search if stock_search else (strategy["stock_name"] if is_edit_mode else ""),
            placeholder="예: 삼성전자, 005930",
            key="stock_search_input"
        )
        
        # 검색 기록 관리
        if "search_history" not in st.session_state:
            st.session_state.search_history = []
        
        # 검색어가 있고 검색 기록에 없으면 기록에 추가
        if stock_search and stock_search not in st.session_state.search_history:
            st.session_state.search_history.insert(0, stock_search)
            # 최대 5개까지만 유지
            if len(st.session_state.search_history) > 5:
                st.session_state.search_history = st.session_state.search_history[:5]
        
        # 최근 검색어 표시 (검색창에 입력 중이 아닐 때)
        if not stock_search and st.session_state.search_history:
            with st.container():
                st.caption("최근 검색어")
                cols = st.columns(len(st.session_state.search_history))
                
                for i, term in enumerate(st.session_state.search_history):
                    with cols[i]:
                        if st.button(term, key=f"history_{i}", use_container_width=True):
                            # 세션 상태에 검색어 저장
                            st.session_state.stock_search = term
                            st.rerun()
        
        if stock_search:
            # 검색 중 상태 표시
            search_spinner = st.empty()
            with search_spinner.container():
                # 디버깅을 위한 API 상태 메시지
                st.info("API 서버에 연결 중... 로그인 상태를 확인합니다.")
                
                # 로그인 확인
                if not is_logged_in():
                    st.error("API 호출을 위해 로그인이 필요합니다.")
                    search_results = []
                else:
                    with st.spinner(f"'{stock_search}' 검색 중..."):
                        try:
                            # API를 호출하여 종목 검색
                            st.info(f"API 서버에 '{stock_search}' 검색 요청을 보냅니다.")
                            search_results = api_client.search_stocks(query=stock_search, limit=10)
                            st.success(f"검색 결과: {len(search_results)}개 종목 발견")
                        except Exception as e:
                            st.error(f"종목 검색 중 오류가 발생했습니다: {str(e)}")
                            # 백엔드 연결 문제 디버깅
                            st.error("API 서버 연결 상태를 확인해 주세요.")
                            search_results = []
            
            # 검색 스피너 제거
            search_spinner.empty()
            
            try:
                if search_results and len(search_results) > 0:
                    # 검색 결과 표시 및 선택
                    options = [f"{item['code']} - {item['name']}" for item in search_results]
                    selected_stock = st.selectbox(
                        "종목 선택", 
                        options, 
                        key="stock_select"
                    )
                    
                    if selected_stock:
                        selected_code = selected_stock.split(" - ")[0]
                        selected_name = selected_stock.split(" - ")[1]
                        
                        # 선택된 종목 강조 표시
                        st.success(f"'{selected_name}' 종목을 선택했습니다.")
                        
                        # 종목 상세 정보 가져오기 (로딩 표시와 함께)
                        detail_spinner = st.empty()
                        with detail_spinner.container():
                            with st.spinner(f"종목 상세 정보를 가져오는 중..."):
                                try:
                                    stock_detail = api_client.get_stock_detail(selected_code)
                                except Exception as e:
                                    st.warning(f"종목 상세 정보를 가져오는 중 오류가 발생했습니다: {str(e)}")
                                    stock_detail = {"code": selected_code, "name": selected_name}
                        
                        # 로딩 스피너 제거
                        detail_spinner.empty()
                        
                        # 선택된 종목 정보 표시
                        with st.container():
                            st.markdown('<div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; margin-top: 10px;">', unsafe_allow_html=True)
                            
                            # 기본 정보 표시
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**종목코드:** {selected_code}")
                                st.markdown(f"**종목명:** {selected_name}")
                                
                                # 업종 정보가 있으면 표시
                                if 'sector' in stock_detail:
                                    st.markdown(f"**업종:** {stock_detail.get('sector', 'N/A')}")
                                    
                            with col2:
                                if 'current_price' in stock_detail:
                                    current_price = stock_detail.get('current_price', 'N/A')
                                    change_percent = stock_detail.get('change_percent', None)
                                    
                                    price_text = f"**현재가:** {current_price:,}원"
                                    if change_percent is not None:
                                        color = 'red' if change_percent > 0 else 'blue'
                                        price_text += f" <span style='color:{color};'>({change_percent:+.2f}%)</span>"
                                    
                                    st.markdown(price_text, unsafe_allow_html=True)
                                
                                # 시가총액 정보가 있으면 표시
                                if 'market_cap' in stock_detail:
                                    market_cap = stock_detail.get('market_cap', 0)
                                    market_cap_text = f"{market_cap:,}원"
                                    if market_cap > 1000000000000:  # 1조 이상
                                        market_cap_text = f"{market_cap/1000000000000:.2f}조원"
                                    elif market_cap > 100000000:  # 1억 이상
                                        market_cap_text = f"{market_cap/100000000:.2f}억원"
                                    
                                    st.markdown(f"**시가총액:** {market_cap_text}")
                                
                                # PER, PBR 정보가 있으면 표시
                                if 'per' in stock_detail:
                                    st.markdown(f"**PER:** {stock_detail.get('per', 'N/A')}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # 검색 결과가 없는 경우 수동 입력 UI 표시
                    st.warning("API 검색 결과가 없습니다. 종목 정보를 수동으로 입력하세요.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        manual_code = st.text_input("종목코드 직접 입력", placeholder="예: 005930", key="manual_stock_code")
                    with col2:
                        manual_name = st.text_input("종목명 직접 입력", placeholder="예: 삼성전자", key="manual_stock_name")
                    
                    if manual_code and manual_name:
                        selected_code = manual_code
                        selected_name = manual_name
                        st.success(f"직접 입력한 종목: {selected_name} ({selected_code})")
                    else:
                        selected_code = ""
                        selected_name = ""
            except Exception as e:
                st.error(f"종목 검색 중 오류가 발생했습니다: {str(e)}")
                selected_code = ""
                selected_name = ""
        else:
            if is_edit_mode:
                selected_code = strategy["stock_code"]
                selected_name = strategy["stock_name"]
            else:
                selected_code = ""
                selected_name = ""
        
        # 전략 유형 선택
        st.markdown("### 전략 유형 선택")
        
        strategy_types = [
            "이동평균선 교차 전략",
            "RSI 과매수/과매도 전략",
            "가격 돌파 전략"
        ]
        
        if is_edit_mode:
            default_index = strategy_types.index(strategy["strategy_type"]) if strategy["strategy_type"] in strategy_types else 0
            selected_strategy = st.radio(
                "전략 유형",
                strategy_types,
                index=default_index
            )
        else:
            selected_strategy = st.radio(
                "전략 유형",
                strategy_types
            )
        
        # 선택된 전략에 따른 파라미터 설정
        st.markdown("### 전략 파라미터 설정")
        
        strategy_params = {}
        
        if selected_strategy == "이동평균선 교차 전략":
            with st.container():
                st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
                st.markdown("**이동평균선 파라미터**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if is_edit_mode and strategy["strategy_type"] == selected_strategy:
                        short_period = st.slider(
                            "단기 이동평균 기간", 
                            min_value=5, 
                            max_value=30, 
                            value=strategy["params"].get("short_period", 5),
                            step=1
                        )
                    else:
                        short_period = st.slider(
                            "단기 이동평균 기간", 
                            min_value=5, 
                            max_value=30, 
                            value=5,
                            step=1
                        )
                
                with col2:
                    if is_edit_mode and strategy["strategy_type"] == selected_strategy:
                        long_period = st.slider(
                            "장기 이동평균 기간", 
                            min_value=20, 
                            max_value=120, 
                            value=strategy["params"].get("long_period", 20),
                            step=5
                        )
                    else:
                        long_period = st.slider(
                            "장기 이동평균 기간", 
                            min_value=20, 
                            max_value=120, 
                            value=20,
                            step=5
                        )
                
                st.markdown("**신호 조건**")
                st.info(f"{short_period}일 이동평균선이 {long_period}일 이동평균선을 상향 돌파할 때 매수 신호가 발생합니다.")
                st.info(f"{short_period}일 이동평균선이 {long_period}일 이동평균선을 하향 돌파할 때 매도 신호가 발생합니다.")
                
                strategy_params = {
                    "short_period": short_period,
                    "long_period": long_period
                }
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        elif selected_strategy == "RSI 과매수/과매도 전략":
            with st.container():
                st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
                st.markdown("**RSI 파라미터**")
                
                if is_edit_mode and strategy["strategy_type"] == selected_strategy:
                    rsi_period = st.slider(
                        "RSI 계산 기간", 
                        min_value=5, 
                        max_value=30, 
                        value=strategy["params"].get("rsi_period", 14),
                        step=1
                    )
                    
                    oversold = st.slider(
                        "과매도 기준", 
                        min_value=10, 
                        max_value=40, 
                        value=strategy["params"].get("oversold", 30),
                        step=1
                    )
                    
                    overbought = st.slider(
                        "과매수 기준", 
                        min_value=60, 
                        max_value=90, 
                        value=strategy["params"].get("overbought", 70),
                        step=1
                    )
                else:
                    rsi_period = st.slider(
                        "RSI 계산 기간", 
                        min_value=5, 
                        max_value=30, 
                        value=14,
                        step=1
                    )
                    
                    oversold = st.slider(
                        "과매도 기준", 
                        min_value=10, 
                        max_value=40, 
                        value=30,
                        step=1
                    )
                    
                    overbought = st.slider(
                        "과매수 기준", 
                        min_value=60, 
                        max_value=90, 
                        value=70,
                        step=1
                    )
                
                st.markdown("**신호 조건**")
                st.info(f"RSI({rsi_period}일)가 {oversold} 이하로 떨어진 후 반등할 때 매수 신호가 발생합니다.")
                st.info(f"RSI({rsi_period}일)가 {overbought} 이상으로 올라간 후 하락할 때 매도 신호가 발생합니다.")
                
                strategy_params = {
                    "rsi_period": rsi_period,
                    "oversold": oversold,
                    "overbought": overbought
                }
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        elif selected_strategy == "가격 돌파 전략":
            with st.container():
                st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
                st.markdown("**가격 돌파 파라미터**")
                
                # 기준 가격 설정
                if is_edit_mode and strategy["strategy_type"] == selected_strategy:
                    target_price = st.number_input(
                        "기준 가격(원)", 
                        min_value=0, 
                        value=int(strategy["params"].get("target_price", 50000)),
                        step=1000
                    )
                    
                    direction = st.radio(
                        "돌파 방향",
                        ["상향 돌파", "하향 돌파"],
                        index=0 if strategy["params"].get("direction", "상향 돌파") == "상향 돌파" else 1
                    )
                else:
                    target_price = st.number_input(
                        "기준 가격(원)", 
                        min_value=0, 
                        value=50000,
                        step=1000
                    )
                    
                    direction = st.radio(
                        "돌파 방향",
                        ["상향 돌파", "하향 돌파"]
                    )
                
                st.markdown("**신호 조건**")
                if direction == "상향 돌파":
                    st.info(f"가격이 {target_price:,}원을 상향 돌파할 때 매수 신호가 발생합니다.")
                else:
                    st.info(f"가격이 {target_price:,}원을 하향 돌파할 때 매도 신호가 발생합니다.")
                
                strategy_params = {
                    "target_price": target_price,
                    "direction": direction
                }
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 매도 조건 설정
        st.markdown("### 매도 조건 설정")
        
        with st.container():
            st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit_mode:
                    take_profit = st.slider(
                        "목표 수익률(%)", 
                        min_value=1.0, 
                        max_value=30.0, 
                        value=float(strategy.get("take_profit", 5.0)),
                        step=0.5
                    )
                else:
                    take_profit = st.slider(
                        "목표 수익률(%)", 
                        min_value=1.0, 
                        max_value=30.0, 
                        value=5.0,
                        step=0.5
                    )
            
            with col2:
                if is_edit_mode:
                    stop_loss = st.slider(
                        "손절 손실률(%)", 
                        min_value=-30.0, 
                        max_value=-1.0, 
                        value=float(strategy.get("stop_loss", -5.0)),
                        step=0.5
                    )
                else:
                    stop_loss = st.slider(
                        "손절 손실률(%)", 
                        min_value=-30.0, 
                        max_value=-1.0, 
                        value=-5.0,
                        step=0.5
                    )
            
            st.info(f"매수 가격 대비 {take_profit}% 이상 상승하면 자동으로 매도합니다.")
            st.info(f"매수 가격 대비 {abs(stop_loss)}% 이상 하락하면 자동으로 손절합니다.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 투자 금액 설정
        st.markdown("### 투자 설정")
        
        with st.container():
            st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
            
            if is_edit_mode:
                investment_amount = st.number_input(
                    "1회 투자금액(원)", 
                    min_value=10000, 
                    max_value=10000000, 
                    value=int(strategy.get("investment_amount", 100000)),
                    step=10000
                )
            else:
                investment_amount = st.number_input(
                    "1회 투자금액(원)", 
                    min_value=10000, 
                    max_value=10000000, 
                    value=100000,
                    step=10000
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 저장 버튼 - 항상 표시 (조건 없음)
        if is_edit_mode:
            save_button = st.button("전략 수정 저장", use_container_width=True, key="save_strategy_edit")
        else:
            save_button = st.button("전략 저장", use_container_width=True, key="save_strategy_new")
        
        if save_button:
            if not selected_code or not selected_name:
                st.error("전략을 저장하기 전에 반드시 종목을 선택해주세요.")
                return
            
            # 새 전략 객체 생성
            new_strategy = {
                "name": strategy_name,
                "stock_code": selected_code,
                "stock_name": selected_name,
                "strategy_type": selected_strategy,
                "params": strategy_params,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "investment_amount": investment_amount,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            if is_edit_mode:
                # 기존 전략 업데이트
                st.session_state.saved_strategies[st.session_state.edit_strategy_index] = new_strategy
                
                # 업데이트 후 저장
                user_id = st.session_state.get("user_id", "default")
                save_path = save_strategies(user_id)
                
                # 수정된 전략 정보 저장
                st.session_state.last_saved_strategy = new_strategy
                
                # 편집 모드 종료
                del st.session_state.edit_strategy
                del st.session_state.edit_strategy_index
                
                # 저장 완료 메시지 및 선택 옵션 제공
                st.success(f"전략 '{strategy_name}'이(가) 수정되었습니다.")
                
                # 옵션 제공
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("전략 목록으로 이동", use_container_width=True, key="goto_strategy_list_edit"):
                        st.session_state.strategy_tab = 0
                        st.rerun()
                
                with col2:
                    if st.button("바로 백테스팅 실행", use_container_width=True, key="run_backtest_after_edit"):
                        st.session_state.backtest_strategy = new_strategy
                        st.session_state.page = "백테스팅"  # 페이지 값 설정
                        st.session_state.backtest_params = {
                            "period": "최근 3개월",  # 기본 백테스팅 기간
                            "initial_capital": 10000000,  # 기본 초기 자본금
                            "fee_rate": 0.015  # 기본 수수료율
                        }
                        st.rerun()
                
                # 이후 코드는 실행되지 않도록 return 추가
                return
            else:
                # 새 전략 저장
                if "saved_strategies" not in st.session_state:
                    st.session_state.saved_strategies = []
                
                st.session_state.saved_strategies.append(new_strategy)
                
                # 새 전략 추가 후 저장
                user_id = st.session_state.get("user_id", "default")
                save_path = save_strategies(user_id)
                
                # 새 전략에 대한 세션 정보 저장
                st.session_state.last_saved_strategy = new_strategy
                
                # 저장 완료 메시지 및 선택 옵션 제공
                st.success(f"전략 '{strategy_name}'이(가) 저장되었습니다.")
                
                # 옵션 제공
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("전략 목록으로 이동", use_container_width=True, key="goto_strategy_list_new"):
                        st.session_state.strategy_tab = 0
                        st.rerun()
                
                with col2:
                    if st.button("바로 백테스팅 실행", use_container_width=True, key="run_backtest_after_new"):
                        st.session_state.backtest_strategy = new_strategy
                        st.session_state.page = "백테스팅"  # 페이지 값 설정
                        st.session_state.backtest_params = {
                            "period": "최근 3개월",  # 기본 백테스팅 기간
                            "initial_capital": 10000000,  # 기본 초기 자본금
                            "fee_rate": 0.015  # 기본 수수료율
                        }
                        st.rerun()
                
                # 이후 코드는 실행되지 않도록 return 추가
                return

# 상세 보기가 선택된 경우
if hasattr(st.session_state, 'view_strategy'):
    strategy = st.session_state.view_strategy
    st.markdown('<div class="section-header">전략 상세 정보</div>', unsafe_allow_html=True)
    
    # 상세 정보 카드
    st.markdown(f'''
    <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #1d3557;">
        <h2 style="margin-top: 0; color: #1d3557;">{strategy['name']}</h2>
        <div style="display: flex; margin-bottom: 15px;">
            <div style="flex: 1;">
                <p><strong>적용 종목:</strong> {strategy['stock_name']} ({strategy['stock_code']})</p>
                <p><strong>전략 유형:</strong> {strategy['strategy_type']}</p>
                <p><strong>생성일:</strong> {strategy.get('created_at', 'N/A')}</p>
                <p><strong>상태:</strong> <span style="padding: 3px 8px; border-radius: 10px; background-color: {strategy.get('is_active', False) and '#d1ffd1' or '#f0f0f0'}; color: {strategy.get('is_active', False) and '#008800' or '#666'};">{"활성" if strategy.get("is_active", False) else "비활성"}</span></p>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 전략 파라미터 및 설정
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 전략 파라미터")
        with st.container():
            st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
            
            # 전략 유형별 파라미터 표시
            if strategy['strategy_type'] == "이동평균선 교차 전략":
                st.markdown(f"**단기 이동평균:** {strategy['params'].get('short_period', 'N/A')}일")
                st.markdown(f"**장기 이동평균:** {strategy['params'].get('long_period', 'N/A')}일")
                
                # 시각화 예시 (실제 구현에서는 실제 데이터 사용)
                st.markdown("##### 전략 시각화")
                dates = pd.date_range(end=datetime.now(), periods=50)
                short_ma = np.cumsum(np.random.normal(0, 1, 50)) + 100
                long_ma = np.cumsum(np.random.normal(0, 0.5, 50)) + 100
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=short_ma, mode='lines', name=f'{strategy["params"].get("short_period", "N/A")}일 이평선'))
                fig.add_trace(go.Scatter(x=dates, y=long_ma, mode='lines', name=f'{strategy["params"].get("long_period", "N/A")}일 이평선'))
                
                fig.update_layout(
                    height=200,
                    margin=dict(l=0, r=0, t=0, b=0),
                    yaxis=dict(range=[0, 100])
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            elif strategy['strategy_type'] == "RSI 과매수/과매도 전략":
                st.markdown(f"**RSI 기간:** {strategy['params'].get('rsi_period', 'N/A')}일")
                st.markdown(f"**과매수 기준:** {strategy['params'].get('overbought', 'N/A')}")
                st.markdown(f"**과매도 기준:** {strategy['params'].get('oversold', 'N/A')}")
                
                # RSI 시각화 예시
                st.markdown("##### 전략 시각화")
                dates = pd.date_range(end=datetime.now(), periods=50)
                rsi_values = np.random.uniform(20, 80, 50)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=rsi_values, mode='lines', name='RSI'))
                
                # 과매수/과매도 레벨 추가
                fig.add_hline(y=strategy['params'].get('overbought', 70), line_dash="dash", line_color="red", annotation_text="과매수")
                fig.add_hline(y=strategy['params'].get('oversold', 30), line_dash="dash", line_color="green", annotation_text="과매도")
                
                fig.update_layout(
                    height=200,
                    margin=dict(l=0, r=0, t=0, b=0),
                    yaxis=dict(range=[0, 100])
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            elif strategy['strategy_type'] == "가격 돌파 전략":
                st.markdown(f"**기준 가격:** {strategy['params'].get('target_price', 'N/A'):,}원")
                st.markdown(f"**돌파 방향:** {strategy['params'].get('direction', 'N/A')}")
                
                # 가격 돌파 시각화 예시
                st.markdown("##### 전략 시각화")
                dates = pd.date_range(end=datetime.now(), periods=50)
                prices = np.cumsum(np.random.normal(0, 1, 50)) + float(strategy['params'].get('target_price', 50000))
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='가격'))
                
                # 돌파 기준선 추가
                fig.add_hline(y=float(strategy['params'].get('target_price', 50000)), line_dash="dash", line_color="blue", annotation_text="돌파 기준")
                
                fig.update_layout(
                    height=200,
                    margin=dict(l=0, r=0, t=0, b=0),
                    yaxis=dict(range=[0, 100])
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 매매 조건")
        with st.container():
            st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
            
            # 매매 조건 시각화
            take_profit = strategy.get('take_profit', 5)
            stop_loss = strategy.get('stop_loss', -5)
            
            st.markdown(f"**목표 수익률:** {take_profit}%")
            st.markdown(f"**손절 손실률:** {stop_loss}%")
            
            # 시각화
            st.markdown("##### 매매 조건 시각화")
            
            # 매수가 기준 차트
            buy_price = 100
            take_profit_price = buy_price * (1 + take_profit/100)
            stop_loss_price = buy_price * (1 + stop_loss/100)
            
            fig = go.Figure()
            
            # 매수가 선
            fig.add_hline(y=buy_price, line_color="black", annotation_text="매수가")
            
            # 목표가 선
            fig.add_hline(y=take_profit_price, line_color="red", line_dash="dash", annotation_text="목표가")
            
            # 손절가 선
            fig.add_hline(y=stop_loss_price, line_color="blue", line_dash="dash", annotation_text="손절가")
            
            # 대시보드 스타일 설정
            fig.update_layout(
                height=200,
                margin=dict(l=0, r=0, t=0, b=0),
                yaxis=dict(range=[buy_price * (1 + stop_loss/100 - 2), buy_price * (1 + take_profit/100 + 2)]))
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"**투자 금액:** {strategy.get('investment_amount', 'N/A'):,}원")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 백테스팅 히스토리 표시
        if 'backtest_history' in strategy and strategy['backtest_history']:
            st.markdown("#### 백테스팅 히스토리")
            with st.container():
                st.markdown('<div class="parameter-section">', unsafe_allow_html=True)
                
                # 백테스팅 히스토리 테이블
                history_df = pd.DataFrame(strategy['backtest_history'])
                
                # 포맷팅
                if not history_df.empty:
                    history_df.columns = ['날짜', '수익률 (%)', '승률 (%)', '최대낙폭 (%)']
                    
                    # 형식 지정 및 정렬
                    history_df = history_df.sort_values('날짜', ascending=False)
                    
                    st.dataframe(history_df, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 전략 액션 버튼
        st.markdown("#### 전략 관리")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("전략 수정", use_container_width=True, key="edit_detail"):
                st.session_state.edit_strategy = strategy
                st.session_state.edit_strategy_index = st.session_state.view_strategy_index
                st.rerun()
        
        with col2:
            if st.button("백테스팅 실행", use_container_width=True, key="backtest_detail"):
                st.session_state.backtest_strategy = strategy
                st.session_state.show_backtest_modal = True
                st.rerun()
        
        with col3:
            if st.button("전략 삭제", use_container_width=True, key="delete_detail"):
                st.session_state.delete_confirm = True
                st.rerun()
        
        # 삭제 확인 대화상자
        if st.session_state.get("delete_confirm", False):
            st.warning(f"'{strategy['name']}' 전략을 정말 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("예, 삭제합니다", use_container_width=True, key="confirm_delete"):
                    st.session_state.saved_strategies.pop(st.session_state.view_strategy_index)
                    
                    # 전략 삭제 후 저장
                    user_id = st.session_state.get("user_id", "default")
                    save_strategies(user_id)
                    
                    del st.session_state.view_strategy
                    del st.session_state.view_strategy_index
                    if "delete_confirm" in st.session_state:
                        del st.session_state.delete_confirm
                    
                    st.success("전략이 삭제되었습니다.")
                    st.rerun()
            
            with col2:
                if st.button("아니오, 취소합니다", use_container_width=True, key="cancel_delete"):
                    if "delete_confirm" in st.session_state:
                        del st.session_state.delete_confirm
                    st.rerun()

# 프로그램 시작 시 초기화
if __name__ == "__main__":
    # 백테스팅 모달 상태 초기화
    if "show_backtest_modal" not in st.session_state:
        st.session_state.show_backtest_modal = False
    
    # 간략 백테스팅 결과 상태 초기화
    if "show_simplified_result" not in st.session_state:
        st.session_state.show_simplified_result = False
    
    # 삭제 확인 대화상자 상태 초기화
    if "delete_confirm" not in st.session_state:
        st.session_state.delete_confirm = False
    
    show() 

# 전략 목록에서 해당 전략 업데이트
def update_strategy_in_saved_list(strategy):
    """저장된 전략 목록에서 특정 전략을 업데이트합니다."""
    for i, s in enumerate(st.session_state.saved_strategies):
        if s["name"] == strategy["name"] and s["stock_code"] == strategy["stock_code"]:
            st.session_state.saved_strategies[i] = strategy
            return True
    return False 