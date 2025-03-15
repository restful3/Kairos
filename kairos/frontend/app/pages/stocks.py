import streamlit as st
import pandas as pd
from typing import Dict, Any, List
try:
    from st_aggrid import AgGrid, GridOptionsBuilder
except ImportError:
    def AgGrid(*args, **kwargs):
        st.error("st-aggrid 라이브러리를 설치해야 합니다. 'pip install streamlit-aggrid'를 실행하세요.")
        return {"data": args[0], "selected_rows": []}
    
    class GridOptionsBuilder:
        @staticmethod
        def from_dataframe(df):
            return GridOptionsBuilder()
        
        def configure_selection(self, *args, **kwargs):
            return self
            
        def build(self):
            return {}

from app.api.client import api_client
from app.utils.session import is_logged_in

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
    
    # 검색 필드와 버튼
    search_col1, search_col2 = st.columns([4, 1])
    
    with search_col1:
        query = st.text_input("검색어", placeholder="예: 삼성전자, 005930", label_visibility="collapsed")
    
    with search_col2:
        search_clicked = st.button("검색", key="search_button", use_container_width=True)
    
    # 탭 생성
    tab_names = ["검색 결과", "업종별 종목", "인기 종목"]
    
    # 탭 선택 UI
    selected_tab = st.radio("주식 탭 선택", tab_names, horizontal=True, label_visibility="collapsed")
    
    # 선택된 탭에 따라 내용 표시
    if selected_tab == "검색 결과":
        if query:
            show_search_results(query)
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
        st.dataframe(df, height=400, use_container_width=True, hide_index=True)
        
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
                
                # 투자 지표
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">투자 지표</div>', unsafe_allow_html=True)
                
                indicator_data = {
                    "PER": f"{stock.get('per', 0):.2f}배" if 'per' in stock else '데이터 없음',
                    "PBR": f"{stock.get('pbr', 0):.2f}배" if 'pbr' in stock else '데이터 없음',
                    "ROE": f"{stock.get('roe', 0):.2f}%" if 'roe' in stock else '데이터 없음',
                    "배당수익률": f"{stock.get('dividend_yield', 0):.2f}%" if 'dividend_yield' in stock else '데이터 없음',
                }
                
                # 지표 표시
                st.table(pd.DataFrame(list(indicator_data.items()), columns=['지표', '값']))
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"종목코드 {code}에 해당하는 정보를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"종목 상세 정보 조회 중 오류가 발생했습니다: {str(e)}") 