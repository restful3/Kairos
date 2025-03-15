import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests

from app.api.client import api_client
from app.utils.session import is_logged_in

# KIS API 엔드포인트 설정 (frontend/app/api/client.py에서 가져온 형식을 따름)
STOCK_DAILY_PRICE_ENDPOINT = "http://localhost:8000/api/stocks"

# 기본 CSS 스타일 정의
def load_css():
    """간소화된 CSS 스타일을 로드합니다"""
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .section-header {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-weight: bold;
        border-bottom: 1px solid #eee;
        padding-bottom: 0.5rem;
    }
    
    .info-card {
        background-color: #f9f9f9;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .positive { color: #e63946; }
    .negative { color: #1d3557; }
    </style>
    """, unsafe_allow_html=True)

def show():
    """종목 검색 페이지 표시"""
    # CSS 스타일 로드
    load_css()
    
    if not is_logged_in():
        st.error("종목 검색을 위해서는 먼저 로그인이 필요합니다.")
        return
    
    st.title("종목 검색")
    
    # 검색 입력 부분
    st.markdown('<div class="section-header">종목명 또는 종목코드로 검색</div>', unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if "stock_tab_index" not in st.session_state:
        st.session_state.stock_tab_index = 0  # 기본 탭은 "검색 결과"(0번 인덱스)
    
    if "search_triggered" not in st.session_state:
        st.session_state.search_triggered = False
    
    # 검색 필드와 버튼
    search_col1, search_col2 = st.columns([4, 1])
    
    with search_col1:
        # 엔터키 처리를 위한 콜백 함수
        def on_search_input_change():
            if st.session_state.search_input and st.session_state.search_input.strip():
                # 검색어가 있으면 "검색 결과" 탭으로 전환
                st.session_state.stock_tab_index = 0
                st.session_state.search_triggered = True
        
        query = st.text_input("검색어", placeholder="예: 삼성전자, 005930", 
                              label_visibility="collapsed",
                             key="search_input",
                             on_change=on_search_input_change)
    
    with search_col2:
        # 검색 버튼 클릭 처리
        def on_search_button_click():
            if query and query.strip():
                # 검색어가 있으면 "검색 결과" 탭으로 전환
                st.session_state.stock_tab_index = 0
                st.session_state.search_triggered = True
                # 페이지 강제 재실행으로 탭 변경 즉시 반영
                st.rerun()
        
        search_clicked = st.button("검색", key="search_button", 
                                 use_container_width=True,
                                 on_click=on_search_button_click)
    
    # 엔터키로 검색 실행 시 탭 전환을 위한 강제 재실행
    if st.session_state.get("search_triggered", False) and st.session_state.stock_tab_index == 0:
        # 검색어가 있고 검색이 트리거되었으면 재실행
        if query and query.strip():
            st.session_state.search_triggered = False  # 플래그 초기화
            st.rerun()  # 페이지 재실행으로 탭 변경 반영
    
    # 탭 생성
    tab_names = ["검색 결과", "업종별 종목", "인기 종목"]
    
    # 탭 선택 UI - 탭 설정 개선
    # key에 값이 바뀌는 session_state를 사용하지 않고 고정 문자열 사용
    selected_tab_index = st.session_state.stock_tab_index
    selected_tab = st.radio(
        "주식 탭 선택", 
        tab_names, 
        index=selected_tab_index,
        horizontal=True, 
        label_visibility="collapsed",
        key="stock_tabs_radio"  # 고정된 key 사용
    )
    
    # 탭 선택이 변경되었는지 확인
    if tab_names.index(selected_tab) != st.session_state.stock_tab_index:
        st.session_state.stock_tab_index = tab_names.index(selected_tab)
        st.rerun()  # 탭 변경 시 재실행하여 UI 즉시 업데이트
    
    # 선택된 탭에 따라 내용 표시
    if selected_tab == "검색 결과":
        if query:
            show_search_results(query)
            # 검색 수행 후 플래그 초기화
            st.session_state.search_triggered = False
        else:
            # 검색어가 없을 때는 인기 종목을 표시하지 않고 검색 안내 메시지만 표시
            st.info("종목명 또는 종목코드를 입력하고 검색 버튼을 클릭하세요.")
    elif selected_tab == "업종별 종목":
        show_sector_stocks()
    elif selected_tab == "인기 종목":
        show_popular_stocks()

def show_search_results(query: str):
    """검색 결과 표시"""
    with st.spinner(f"'{query}' 검색 중..."):
        try:
            results = api_client.search_stocks(query)
            
            if results is None:
                st.warning(f"검색어 '{query}'에 대한 결과를 가져올 수 없습니다.")
                return
                
            if len(results) > 0:
                st.success(f"검색어 '{query}'에 대한 결과 {len(results)}개를 찾았습니다.")
                display_stock_table(results, key_suffix="search", title=f"'{query}' 검색 결과")
            else:
                st.warning(f"검색어 '{query}'에 일치하는 종목이 없습니다.")
                
                try:
                    popular_stocks = api_client.get_popular_stocks()
                    if popular_stocks and len(popular_stocks) > 0:
                        st.info("대신 인기 종목을 추천해 드립니다.")
                        display_stock_table(popular_stocks[:5], key_suffix="recommend", title="추천 인기 종목")
                except Exception as e:
                    st.error(f"인기 종목 조회 중 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            st.error(f"종목 검색 중 오류가 발생했습니다: {str(e)}")

def show_sector_stocks():
    """업종별 종목 표시"""
    # 업종 선택 드롭다운
    sectors = ["전기전자", "화학", "금융업", "운수장비", "의약품", "서비스업", "음식료품"]
    
    st.markdown('<div class="section-header">업종 선택</div>', unsafe_allow_html=True)
    selected_sector = st.selectbox("업종 선택하기", sectors, label_visibility="collapsed")
    
    if selected_sector:
        with st.spinner(f"'{selected_sector}' 업종 종목을 불러오는 중..."):
            try:
                results = api_client.get_stocks_by_sector(selected_sector)
                
                if results is None:
                    st.warning(f"{selected_sector} 업종 정보를 가져올 수 없습니다.")
                    return
                    
                if len(results) > 0:
                    st.success(f"{selected_sector} 업종 종목 {len(results)}개를 불러왔습니다.")
                    display_stock_table(results, key_suffix="sector", title=f"{selected_sector} 업종 종목")
                else:
                    st.warning(f"{selected_sector} 업종에 해당하는 종목이 없습니다.")
            except Exception as e:
                st.error(f"업종별 종목 조회 중 오류가 발생했습니다: {str(e)}")

def show_popular_stocks():
    """인기 종목 표시"""
    with st.spinner("인기 종목을 불러오는 중..."):
        try:
            results = api_client.get_popular_stocks()
            
            if results is None:
                st.warning("인기 종목 정보를 가져올 수 없습니다.")
                return
                
            if len(results) > 0:
                st.success(f"인기 종목 {len(results)}개를 불러왔습니다.")
                display_stock_table(results, key_suffix="popular", title="인기 종목 목록")
            else:
                st.warning("인기 종목 데이터가 없습니다.")
        except Exception as e:
            st.error(f"인기 종목 조회 중 오류가 발생했습니다: {str(e)}")

def display_stock_table(stocks: List[Dict[str, Any]], key_suffix: str = "default", title: str = None):
    """종목 목록을 테이블로 표시"""
    # 제목 표시 (지정된 경우)
    if title:
        st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-header">{key_suffix.capitalize()} 종목 목록</div>', unsafe_allow_html=True)

    # 데이터프레임 생성
    df = pd.DataFrame(stocks)
    
    # 필요한 칼럼만 선택 및 이름 변경
    if 'code' in df.columns and 'name' in df.columns:
        # 필수 칼럼
        columns = ['code', 'name', 'market', 'sector']
        
        # 추가 가능한 칼럼 (있을 경우만)
        additional_columns = [
            'current_price', 'price_change', 'change_rate', 'volume', 'market_cap', 
            'high_52wk', 'low_52wk', 'per', 'pbr'
        ]
        
        for col in additional_columns:
            if col in df.columns:
                columns.append(col)
                
        # 존재하는 칼럼만 선택
        existing_columns = [col for col in columns if col in df.columns]
        df = df[existing_columns]
        
        # 칼럼명 변경
        column_names = {
            'code': '종목코드', 
            'name': '종목명', 
            'market': '시장구분', 
            'sector': '업종',
            'current_price': '현재가',
            'price_change': '전일대비',
            'change_rate': '등락률(%)',
            'volume': '거래량',
            'market_cap': '시가총액',
            'high_52wk': '52주 최고',
            'low_52wk': '52주 최저',
            'per': 'PER',
            'pbr': 'PBR'
        }
        
        # 존재하는 칼럼만 이름 변경
        rename_dict = {k: v for k, v in column_names.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        
        # 가격 관련 컬럼 포맷팅
        if '현재가' in df.columns:
            df['현재가'] = df['현재가'].apply(lambda x: f"{x:,}")
        if '전일대비' in df.columns:
            df['전일대비'] = df['전일대비'].apply(lambda x: f"{x:+,}" if x != 0 else "0")
        if '거래량' in df.columns:
            df['거래량'] = df['거래량'].apply(lambda x: f"{x:,}")
        if '시가총액' in df.columns:
            df['시가총액'] = df['시가총액'].apply(lambda x: f"{x/100000000:,.0f}억")
        
        # 테이블 표시
        # 각 행의 높이를 35픽셀로 계산하고 헤더를 위해 40픽셀 추가
        table_height = min(len(df) * 35 + 40, 600)  # 최대 높이는 600픽셀로 제한
        st.dataframe(df, height=table_height, use_container_width=True, hide_index=True)
        
        # 종목 선택 UI
        st.markdown("<p>👇 종목 선택</p>", unsafe_allow_html=True)
        
        # 종목 선택 드롭다운
        options = [f"{code} - {name}" for code, name in zip(df['종목코드'].tolist(), df['종목명'].tolist())]
        selected_option = st.selectbox("종목 선택하기", ["- 종목을 선택하세요 -"] + options)
        
        # 유효한 종목 선택인지 확인
        if selected_option and selected_option != "- 종목을 선택하세요 -":
            # 종목코드 추출
            selected_code = selected_option.split(" - ")[0]
            
            # 종목 상세 정보 표시
            show_stock_detail(selected_code)
    else:
        st.error("종목 데이터 형식이 올바르지 않습니다.")

def _create_test_chart(code: str, name: str, current_price: float, days: int = 60):
    """
    테스트 데이터를 사용한 주가 차트 생성 (백업용)
    
    Args:
        code: 종목코드
        name: 종목명
        current_price: 현재가
        days: 표시할 기간(일)
        
    Returns:
        plotly 차트 객체
    """
    # 시드 고정으로 같은 종목은 같은 패턴 생성
    np.random.seed(int(code))
    
    # 날짜 생성 (오늘로부터 days일 전까지)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # 영업일만
    
    # 초기 가격 설정 (현재가의 -20% ~ -5% 사이)
    start_price = current_price * (0.8 + np.random.rand() * 0.15)
    
    # 일별 변동률 생성 (약간의 상승추세)
    daily_returns = np.random.normal(0.0005, 0.015, size=len(date_range))
    
    # 주가 시뮬레이션
    prices = [start_price]
    for ret in daily_returns:
        prices.append(prices[-1] * (1 + ret))
    
    # 마지막 값은 현재가로 조정
    adjustment = current_price / prices[-1]
    prices = [p * adjustment for p in prices]
    
    # OHLC 데이터 생성
    high_prices = [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices]
    low_prices = [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices]
    open_prices = [low_p + np.random.rand() * (high_p - low_p) for high_p, low_p in zip(high_prices, low_prices)]
    
    # 거래량 생성
    volumes = np.random.normal(1000000, 300000, size=len(date_range))
    volumes = np.maximum(volumes, 100000)  # 최소 거래량 설정
    
    # 데이터프레임 생성
    df = pd.DataFrame({
        'Date': date_range,
        'Open': open_prices[:-1],  # 하루 차이 조정
        'High': high_prices[:-1],
        'Low': low_prices[:-1],
        'Close': prices[:-1],
        'Volume': volumes
    })
    
    # 마지막 행은 현재가로 설정
    last_row = pd.DataFrame([{
        'Date': end_date,
        'Open': prices[-2],
        'High': max(prices[-2], current_price),
        'Low': min(prices[-2], current_price),
        'Close': current_price,
        'Volume': volumes[-1]
    }])
    
    df = pd.concat([df, last_row], ignore_index=True)
    
    # 이동평균선 계산
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # 차트 생성
    fig = go.Figure()
    
    # 캔들스틱 차트
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='가격',
        increasing_line_color='red',
        decreasing_line_color='blue'
    ))
    
    # 이동평균선 추가
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['MA5'],
        mode='lines',
        name='5일 이동평균',
        line=dict(color='orange', width=1)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['MA20'],
        mode='lines',
        name='20일 이동평균',
        line=dict(color='purple', width=1)
    ))
    
    # 차트 레이아웃 설정
    fig.update_layout(
        title=f"{name} ({code}) 주가 차트 <테스트 데이터>",
        xaxis_title="날짜",
        yaxis_title="가격 (원)",
        xaxis_rangeslider_visible=False,
                height=400,
        template="plotly_white"
    )
    
    # Y축 설정 (콤마 포맷)
    fig.update_yaxes(tickformat=",")
    
    return fig

def get_stock_history(code: str, days: int = 60):
    """
    KIS API를 통해 종목의 일별 가격 히스토리 조회
    
    Args:
        code: 종목코드
        days: 조회 일수
        
    Returns:
        일별 시세 데이터 리스트
    """
    if not api_client.get_token():
        st.error("로그인이 필요합니다.")
        return []
    
    try:
        # 현재 날짜와 시작 날짜 계산
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        # API 호출 - 직접 백엔드 호출
        url = f"{STOCK_DAILY_PRICE_ENDPOINT}/{code}/daily"
        
        # 로그 출력
        print(f"[DEBUG] 종목 일별 시세 조회: {code} | 시작일: {start_date} | 종료일: {end_date}")
        
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_client.get_token()}"},
            params={"start_date": start_date, "end_date": end_date}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] 일별 시세 조회 실패: {response.status_code}")
            print(response.text)
            return []
            
    except Exception as e:
        print(f"[ERROR] 주가 데이터 조회 중 오류 발생: {str(e)}")
        return []

def create_stock_price_chart(code: str, name: str, current_price: float, days: int = 60, chart_type: str = "일봉"):
    """
    주가 차트 생성 (실제 데이터 사용)
    
    Args:
        code: 종목코드
        name: 종목명
        current_price: 현재가
        days: 표시할 기간(일)
        chart_type: 차트 유형 (일봉, 주봉, 월봉)
        
    Returns:
        plotly 차트 객체
    """
    # 실제 주가 데이터 가져오기 시도
    history_data = get_stock_history(code, days)
    
    # 데이터를 가져오지 못했으면 테스트 데이터 사용
    if not history_data:
        st.warning("실제 주가 데이터를 가져올 수 없어 테스트 데이터를 사용합니다.")
        return _create_test_chart(code, name, current_price, days)
    
    try:
        # 데이터 형식 변환
        price_data = []
        for item in history_data:
            # API 응답 포맷에 따라 수정 필요
            date_str = item.get('stck_bsop_date', '') or item.get('date', '')
            if len(date_str) == 8:  # YYYYMMDD 형식이면
                date = datetime.strptime(date_str, '%Y%m%d')
            else:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                
            price_data.append({
                'Date': date,
                'Open': int(item.get('stck_oprc', 0) or item.get('open', 0)),
                'High': int(item.get('stck_hgpr', 0) or item.get('high', 0)),
                'Low': int(item.get('stck_lwpr', 0) or item.get('low', 0)),
                'Close': int(item.get('stck_clpr', 0) or item.get('close', 0)),
                'Volume': int(item.get('acml_vol', 0) or item.get('volume', 0))
            })
        
        # 데이터프레임 생성 및 정렬
        df = pd.DataFrame(price_data)
        if df.empty:
            st.warning("해당 기간에 거래 데이터가 없습니다.")
            return _create_test_chart(code, name, current_price, days)
            
        df = df.sort_values('Date')
        
        # 봉차트 유형에 따라 데이터 리샘플링
        if chart_type == "주봉":
            # 날짜를 인덱스로 설정
            df.set_index('Date', inplace=True)
            
            # 주간 데이터로 리샘플링
            weekly_df = pd.DataFrame()
            weekly_df['Open'] = df['Open'].resample('W-MON').first()  # 주의 첫 시가
            weekly_df['High'] = df['High'].resample('W-MON').max()    # 주 중 최고가
            weekly_df['Low'] = df['Low'].resample('W-MON').min()      # 주 중 최저가
            weekly_df['Close'] = df['Close'].resample('W-MON').last() # 주의 마지막 종가
            weekly_df['Volume'] = df['Volume'].resample('W-MON').sum() # 주간 거래량 합계
            
            # NaN 값 제거
            weekly_df = weekly_df.dropna()
            
            # 인덱스를 다시 컬럼으로 변환
            weekly_df.reset_index(inplace=True)
            df = weekly_df
            
        elif chart_type == "월봉":
            # 날짜를 인덱스로 설정
            df.set_index('Date', inplace=True)
            
            # 월간 데이터로 리샘플링
            monthly_df = pd.DataFrame()
            monthly_df['Open'] = df['Open'].resample('M').first()  # 월의 첫 시가
            monthly_df['High'] = df['High'].resample('M').max()    # 월 중 최고가
            monthly_df['Low'] = df['Low'].resample('M').min()      # 월 중 최저가
            monthly_df['Close'] = df['Close'].resample('M').last() # 월의 마지막 종가
            monthly_df['Volume'] = df['Volume'].resample('M').sum() # 월간 거래량 합계
            
            # NaN 값 제거
            monthly_df = monthly_df.dropna()
            
            # 인덱스를 다시 컬럼으로 변환
            monthly_df.reset_index(inplace=True)
            df = monthly_df
        
        # 이동평균선 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        
        # 차트 생성
        fig = go.Figure()
        
        # 캔들스틱 차트
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='가격',
            increasing_line_color='red',
            decreasing_line_color='blue'
        ))
        
        # 이동평균선 추가
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['MA5'],
            mode='lines',
            name='5일 이동평균',
            line=dict(color='orange', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['MA20'],
            mode='lines',
            name='20일 이동평균',
            line=dict(color='purple', width=1)
        ))
        
        # 차트 레이아웃 설정
        period_text = f"{days}일" if days <= 365 else f"{days//365}년"
        chart_title = f"{name} ({code}) 주가 차트 - {chart_type}/{period_text} - 실제 데이터"
            
        fig.update_layout(
            title=chart_title,
            xaxis_title="날짜",
            yaxis_title="가격 (원)",
            xaxis_rangeslider_visible=False,
            height=400,
            template="plotly_white"
        )
        
        # Y축 설정 (콤마 포맷)
        fig.update_yaxes(tickformat=",")
        
        return fig
        
    except Exception as e:
        st.error(f"차트 생성 중 오류 발생: {str(e)}")
        # 오류 발생 시 테스트 데이터로 대체
        st.warning("오류로 인해 테스트 데이터로 차트를 생성합니다.")
        return _create_test_chart(code, name, current_price, days)

def show_stock_detail(code: str):
    """종목 상세 정보 표시"""
    with st.spinner(f"'{code}' 종목 상세 정보를 불러오는 중..."):
        try:
            stock = api_client.get_stock_detail(code)
            
            if stock is None:
                st.error(f"종목코드 {code}에 해당하는 정보가 없습니다.")
                return
                
            if stock:
                # 상세 정보 카드
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                
                # 종목명과 종목코드
                st.markdown(f"<h2>{stock['name']} ({stock['code']})</h2>", unsafe_allow_html=True)
                
                # 요약 정보
                col1, col2, col3, col4 = st.columns(4)
                
                # 현재가 및 변동 정보
                with col1:
                    if 'current_price' in stock and 'change_rate' in stock:
                        price = stock['current_price']
                        change_rate = stock.get('change_rate', 0)
                        price_change = stock.get('price_change', 0)
                        
                        color_class = "positive" if change_rate > 0 else "negative" if change_rate < 0 else ""
                        
                        st.markdown(f"""
                        <div>
                            <div>현재가</div>
                            <div style="font-weight:bold;">{price:,}원</div>
                            <div class="{color_class}">
                                {price_change:+,}원 ({change_rate:.2f}%)
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div>현재가 데이터 없음</div>", unsafe_allow_html=True)
                
                # 거래량
                with col2:
                    if 'volume' in stock:
                        volume = stock['volume']
                        st.markdown(f"<div>거래량: {volume:,}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div>거래량 데이터 없음</div>", unsafe_allow_html=True)
                
                # 시가총액
                with col3:
                    if 'market_cap' in stock:
                        market_cap = stock['market_cap']
                        st.markdown(f"<div>시가총액: {market_cap/100000000:,.0f}억원</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div>시가총액 데이터 없음</div>", unsafe_allow_html=True)
                
                # 업종 정보
                with col4:
                    sector = stock.get('sector', '데이터 없음')
                    market = stock.get('market', '데이터 없음')
                    st.markdown(f"<div>업종: {sector}<br>시장: {market}</div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 가격 범위 정보
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">가격 정보</div>', unsafe_allow_html=True)
                
                # 주가 차트 (테스트 데이터)
                if 'current_price' in stock:
                    # 차트 생성 및 표시
                    try:
                        fig = create_stock_price_chart(
                            code=stock['code'],
                            name=stock['name'],
                            current_price=stock['current_price']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"차트 생성 중 오류 발생: {str(e)}")
                
                # 가격 정보 행
                col1, col2, col3 = st.columns(3)
                
                # 당일 가격 범위
                with col1:
                    open_price = stock.get('open_price', 0)
                    high_price = stock.get('high_price', 0)
                    low_price = stock.get('low_price', 0)
                    
                    if all([open_price, high_price, low_price]):
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="font-weight: bold;">당일 가격 범위</div>
                            <div>시가: {open_price:,}원</div>
                            <div>고가: {high_price:,}원</div>
                            <div>저가: {low_price:,}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='text-align: center;'>당일 가격 정보 없음</div>", unsafe_allow_html=True)
                
                # 52주 최고/최저
                with col2:
                    high_52wk = stock.get('high_52wk', 0)
                    low_52wk = stock.get('low_52wk', 0)
                    
                    if high_52wk and low_52wk:
                        # 현재가 대비 52주 최고가와의 차이 비율 계산
                        current = stock.get('current_price', 0)
                        from_high = ((current - high_52wk) / high_52wk * 100) if high_52wk else 0
                        from_low = ((current - low_52wk) / low_52wk * 100) if low_52wk else 0
                        
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="font-weight: bold;">52주 가격 범위</div>
                            <div>최고: {high_52wk:,}원</div>
                            <div>최저: {low_52wk:,}원</div>
                            <div style="font-size: 0.9em;">
                                (최고가대비: {from_high:.1f}%, 최저가대비: {from_low:.1f}%)
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='text-align: center;'>52주 가격 정보 없음</div>", unsafe_allow_html=True)
                
                # 주가 변동 지표 (ATR, 변동성 등)
                with col3:
                    prev_close = stock.get('prev_close', 0)
                    current = stock.get('current_price', 0)
                    
                    if prev_close and current:
                        # 전일 종가 대비 변동폭 계산
                        day_range = high_price - low_price if high_price and low_price else 0
                        day_range_ratio = (day_range / prev_close * 100) if prev_close else 0
                        
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="font-weight: bold;">변동성 지표</div>
                            <div>전일종가: {prev_close:,}원</div>
                            <div>당일변동폭: {day_range:,}원</div>
                            <div style="font-size: 0.9em;">
                                (변동성: {day_range_ratio:.1f}%)
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='text-align: center;'>변동성 정보 없음</div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 투자 지표
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">투자 지표</div>', unsafe_allow_html=True)
                
                # 투자 지표 열
                col1, col2 = st.columns(2)
                
                # 기본 투자 지표
                with col1:
                    indicator_data = {
                        "PER (배)": f"{stock.get('per', 0):.2f}" if 'per' in stock else '정보 없음',
                        "PBR (배)": f"{stock.get('pbr', 0):.2f}" if 'pbr' in stock else '정보 없음',
                        "ROE (%)": f"{stock.get('roe', 0):.2f}" if 'roe' in stock else '정보 없음',
                        "배당수익률 (%)": f"{stock.get('dividend_yield', 0):.2f}" if 'dividend_yield' in stock else '정보 없음'
                    }
                    
                    # 기본 지표 표시
                    st.dataframe(
                        pd.DataFrame(list(indicator_data.items()), columns=['지표', '값']),
                        hide_index=True,
                        use_container_width=True
                    )
                
                # 추가 투자 지표
                with col2:
                    additional_data = {
                        "상장주식수": f"{stock.get('listed_shares', 0):,}주" if 'listed_shares' in stock else '정보 없음',
                        "EPS (원)": f"{stock.get('eps', 0):,.0f}" if 'eps' in stock else '정보 없음',
                        "BPS (원)": f"{stock.get('bps', 0):,.0f}" if 'bps' in stock else '정보 없음',
                        "유통주식비율 (%)": f"{stock.get('floating_rate', 0):.2f}" if 'floating_rate' in stock else '정보 없음'
                    }
                    
                    # 추가 지표 표시
                    st.dataframe(
                        pd.DataFrame(list(additional_data.items()), columns=['지표', '값']),
                        hide_index=True,
                        use_container_width=True
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 추가 정보 표시 (주가 차트 등은 향후 구현 예정)
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">추가 정보</div>', unsafe_allow_html=True)
                
                # 탭 생성
                tabs = st.tabs(["종목 설명", "주요 지표", "관련 종목"])
                
                # 종목 설명 탭
                with tabs[0]:
                    company_desc = stock.get('company_description', "상세 정보가 없습니다.")
                    st.markdown(f"<p>{company_desc}</p>", unsafe_allow_html=True)
                
                # 주요 지표 탭
                with tabs[1]:
                    st.info("📊 주요 재무제표 데이터는 향후 업데이트 예정입니다.")
                    
                    # 임시 데이터 표시
                    st.markdown("""
                    <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-weight: bold;">매출액 (억원)</div>
                            <div>연간 데이터 준비 중</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-weight: bold;">영업이익 (억원)</div>
                            <div>연간 데이터 준비 중</div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-weight: bold;">당기순이익 (억원)</div>
                            <div>연간 데이터 준비 중</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 관련 종목 탭
                with tabs[2]:
                    sector = stock.get('sector', '')
                    if sector:
                        st.write(f"'{sector}' 업종의 다른 종목")
                        try:
                            # 동일 업종 종목 최대 5개 표시
                            sector_stocks = api_client.get_stocks_by_sector(sector, 5)
                            
                            # 현재 종목 제외
                            sector_stocks = [s for s in sector_stocks if s.get('code') != code]
                            
                            if sector_stocks:
                                # 간단한 정보만 표시
                                df = pd.DataFrame(sector_stocks)
                                if 'code' in df.columns and 'name' in df.columns:
                                    df = df[['code', 'name', 'current_price', 'change_rate']]
                                    df.columns = ['종목코드', '종목명', '현재가', '등락률(%)']
                                    
                                    # 현재가 포맷팅
                                    if '현재가' in df.columns:
                                        df['현재가'] = df['현재가'].apply(lambda x: f"{x:,}")
                                    
                                    st.dataframe(df, hide_index=True, use_container_width=True)
                                else:
                                    st.warning("관련 종목 정보가 올바르지 않습니다.")
                            else:
                                st.info("관련 종목이 없습니다.")
                        except Exception as e:
                            st.error(f"관련 종목 조회 중 오류 발생: {str(e)}")
                    else:
                        st.info("업종 정보가 없어 관련 종목을 표시할 수 없습니다.")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"종목코드 {code}에 해당하는 정보를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"종목 상세 정보 조회 중 오류가 발생했습니다: {str(e)}")