"""
전략 생성/수정 폼 컴포넌트 모듈입니다.
"""
import streamlit as st
from typing import Dict, Any, Optional, Callable, Tuple
import logging

from ...models.strategy_template import DEFAULT_TEMPLATES
from ..stock_search import render_stock_search

logger = logging.getLogger(__name__)

def render_strategy_form(
    is_edit_mode: bool = False,
    strategy: Optional[Dict[str, Any]] = None,
    on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None,
    controller: Optional[Any] = None
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """전략 생성/편집 폼 렌더링
    
    Args:
        is_edit_mode: 편집 모드 여부
        strategy: 편집할 전략 데이터 (편집 모드인 경우)
        on_save: 저장 버튼 클릭 시 콜백 함수
        on_cancel: 취소 버튼 클릭 시 콜백 함수
        controller: 폼에서 사용할 컨트롤러
        
    Returns:
        (저장 여부, 전략 데이터)
    """
    # 폼 데이터 초기화
    if "form_data" not in st.session_state:
        st.session_state.form_data = {
            "name": "",
            "stock_code": "",
            "stock_name": "",
            "strategy_type": "이동평균 교차",
            "params": {},
            "take_profit": 5.0,
            "stop_loss": -5.0,
            "investment_amount": 1000000,
            "is_active": False
        }
    
    # 편집 모드인 경우 기존 데이터로 초기화
    if is_edit_mode and strategy and not st.session_state.get("form_initialized", False):
        st.session_state.form_data = strategy.copy()
        st.session_state.form_initialized = True
    
    # 템플릿 선택 (새로 생성하는 경우만)
    if not is_edit_mode:
        st.subheader("템플릿 선택")
        template_names = ["직접 입력"] + list(DEFAULT_TEMPLATES.keys())
        template_index = template_names.index(st.session_state.get("selected_template", "직접 입력"))
        selected_template = st.selectbox(
            "전략 템플릿",
            template_names,
            index=template_index,
            help="미리 정의된 템플릿을 선택하여 빠르게 전략을 생성할 수 있습니다."
        )
        
        # 템플릿이 변경되었을 때만 처리
        if selected_template != st.session_state.get("selected_template") and selected_template != "직접 입력":
            template = DEFAULT_TEMPLATES[selected_template]
            # 폼 데이터 업데이트
            st.session_state.form_data.update({
                "name": template["name"],
                "strategy_type": template["strategy_type"],
                "params": template["params"].copy(),
                "take_profit": template["take_profit"],
                "stop_loss": template["stop_loss"]
            })
            # 상태 업데이트
            st.session_state.selected_template = selected_template
            st.rerun()
        
        # 템플릿이 직접 입력으로 변경된 경우
        if selected_template == "직접 입력" and st.session_state.get("selected_template") != "직접 입력":
            st.session_state.selected_template = "직접 입력"
    
    # 기본 정보 입력
    st.subheader("기본 정보")
    st.session_state.form_data["name"] = st.text_input(
        "전략 이름 *",
        value=st.session_state.form_data.get("name", ""),
        max_chars=50,
        help="고유한 전략 이름을 입력하세요. (최대 50자)"
    )
    
    # 종목 선택
    st.subheader("종목 선택")
    
    # 이미 선택된 종목이 있는 경우
    if st.session_state.form_data.get("stock_code") and st.session_state.form_data.get("stock_name"):
        st.info(f"선택된 종목: {st.session_state.form_data['stock_name']} ({st.session_state.form_data['stock_code']})")
        if st.button("종목 변경하기"):
            st.session_state.form_data["stock_code"] = ""
            st.session_state.form_data["stock_name"] = ""
            st.rerun()
    else:
        # 종목 검색 컴포넌트
        render_stock_search(
            on_select=_handle_stock_select,
            controller=controller if controller else None
        )
    
    # 전략 유형 선택
    st.subheader("전략 설정")
    
    # 전략 유형 선택
    strategy_types = [
        "이동평균 교차", "골든/데드 크로스", "볼린저 밴드", 
        "RSI 과매수/과매도", "MACD 시그널", "가격 돌파", "그물망 매매"
    ]
    
    selected_type = st.selectbox(
        "전략 유형 *",
        strategy_types,
        index=strategy_types.index(st.session_state.form_data.get("strategy_type", "이동평균 교차")),
        help="매매 신호를 생성할 전략 유형을 선택하세요."
    )
    
    # 전략 유형이 변경된 경우
    if selected_type != st.session_state.form_data.get("strategy_type"):
        # 전략 파라미터 초기화
        st.session_state.form_data["strategy_type"] = selected_type
        st.session_state.form_data["params"] = {}
        st.rerun()
    
    # 전략 세부 파라미터
    st.session_state.form_data["params"] = _render_strategy_params(
        st.session_state.form_data.get("strategy_type", "이동평균 교차"),
        st.session_state.form_data.get("params", {})
    )
    
    # 리스크 관리 설정
    st.subheader("리스크 관리")
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.form_data["take_profit"] = st.slider(
            "목표 수익률 (%) *",
            min_value=0.5,
            max_value=50.0,
            value=st.session_state.form_data.get("take_profit", 5.0),
            step=0.5,
            help="이 수익률에 도달하면 자동으로 매도합니다."
        )
    
    with col2:
        st.session_state.form_data["stop_loss"] = st.slider(
            "손절 손실률 (%) *",
            min_value=-50.0,
            max_value=-0.5,
            value=st.session_state.form_data.get("stop_loss", -5.0),
            step=0.5,
            help="이 손실률에 도달하면 자동으로 매도합니다."
        )
    
    # 투자 설정
    st.subheader("투자 설정")
    
    # 투자 금액 변수 가져오기 및 타입 변환
    current_amount = st.session_state.form_data.get("investment_amount", 1000000)
    if isinstance(current_amount, float):
        current_amount = int(current_amount)  # float을 int로 변환
    
    st.session_state.form_data["investment_amount"] = st.number_input(
        "1회 투자금액 (원) *",
        min_value=10000,
        max_value=100000000,
        value=current_amount,
        step=10000,
        help="한 번의 매매에 사용할 금액입니다."
    )
    
    # 활성화 여부 (편집 모드에서만)
    if is_edit_mode:
        st.session_state.form_data["is_active"] = st.checkbox(
            "전략 활성화",
            value=st.session_state.form_data.get("is_active", False),
            help="활성화하면 실제 매매에 사용됩니다. (자동 매매가 설정된 경우)"
        )
    
    # 필수 필드 검증
    is_valid = (
        st.session_state.form_data.get("name") and
        st.session_state.form_data.get("stock_code") and
        st.session_state.form_data.get("stock_name") and
        st.session_state.form_data.get("strategy_type")
    )
    
    # 버튼 영역
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if on_cancel:  # 취소 버튼
            if st.button("취소", use_container_width=True):
                on_cancel()
                return False, None
    
    with col2:
        save_label = "저장하기" if is_edit_mode else "전략 생성하기"
        save_disabled = not is_valid
        
        if save_disabled:
            st.info("모든 필수 항목(*)을 입력해야 합니다.")
        
        save_clicked = st.button(
            save_label,
            disabled=save_disabled,
            use_container_width=True
        )
        
        if save_clicked and is_valid:
            if on_save:
                on_save(st.session_state.form_data)
            st.session_state.form_initialized = False
            return True, st.session_state.form_data
    
    return False, None

def _handle_stock_select(stock: Dict[str, Any]) -> None:
    """종목 선택 콜백 함수
    
    Args:
        stock: 선택된 종목 정보
    """
    # 폼 데이터 업데이트
    st.session_state.form_data["stock_code"] = stock["code"]
    st.session_state.form_data["stock_name"] = stock["name"]
    # 재실행하여 UI 업데이트
    st.rerun()

def _render_strategy_params(strategy_type: str, current_params: Dict[str, Any]) -> Dict[str, Any]:
    """전략 유형에 따른 파라미터 입력 UI 렌더링
    
    Args:
        strategy_type: 전략 유형
        current_params: 현재 파라미터 값
        
    Returns:
        업데이트된 파라미터 값
    """
    params = current_params.copy()
    
    if strategy_type == "이동평균 교차":
        col1, col2 = st.columns(2)
        with col1:
            params["short_period"] = st.slider(
                "단기 이동평균선 기간",
                min_value=3,
                max_value=30,
                value=params.get("short_period", 5),
                help="더 짧은 기간의 이동평균선입니다."
            )
        with col2:
            params["long_period"] = st.slider(
                "장기 이동평균선 기간",
                min_value=10,
                max_value=200,
                value=params.get("long_period", 20),
                help="더 긴 기간의 이동평균선입니다."
            )
            
    elif strategy_type == "골든/데드 크로스":
        col1, col2 = st.columns(2)
        with col1:
            params["ma5_period"] = st.slider(
                "단기 이동평균선 기간",
                min_value=5,
                max_value=5,
                value=5,
                disabled=True,
                help="5일 이동평균선입니다."
            )
        with col2:
            params["ma20_period"] = st.slider(
                "장기 이동평균선 기간",
                min_value=20,
                max_value=20,
                value=20,
                disabled=True,
                help="20일 이동평균선입니다."
            )
        
        params["signal_type"] = st.radio(
            "신호 유형",
            ["골든 크로스만", "데드 크로스만", "모두"],
            index=["골든 크로스만", "데드 크로스만", "모두"].index(params.get("signal_type", "골든 크로스만")),
            help="골든 크로스: 5일선이 20일선 위로 / 데드 크로스: 5일선이 20일선 아래로"
        )
            
    elif strategy_type == "볼린저 밴드":
        col1, col2 = st.columns(2)
        with col1:
            params["period"] = st.slider(
                "기간",
                min_value=10,
                max_value=50,
                value=params.get("period", 20),
                help="이동평균을 계산할 기간입니다."
            )
        with col2:
            params["std_dev"] = st.slider(
                "표준편차",
                min_value=1.0,
                max_value=3.0,
                value=params.get("std_dev", 2.0),
                step=0.1,
                help="밴드의 폭을 결정하는 표준편차 계수입니다."
            )
            
        params["signal_type"] = st.radio(
            "신호 유형",
            ["하단 돌파 매수", "상단 돌파 매도", "모두"],
            index=["하단 돌파 매수", "상단 돌파 매도", "모두"].index(params.get("signal_type", "하단 돌파 매수")),
            help="밴드 상/하단 돌파 시 발생하는 신호 유형을 선택합니다."
        )
            
    elif strategy_type == "RSI 과매수/과매도":
        col1, col2, col3 = st.columns(3)
        with col1:
            params["period"] = st.slider(
                "RSI 기간",
                min_value=5,
                max_value=30,
                value=params.get("period", 14),
                help="RSI 계산에 사용할 기간입니다."
            )
        with col2:
            params["oversold"] = st.slider(
                "과매도 기준",
                min_value=10,
                max_value=40,
                value=params.get("oversold", 30),
                help="이 값 이하면 과매도로 판단합니다."
            )
        with col3:
            params["overbought"] = st.slider(
                "과매수 기준",
                min_value=60,
                max_value=90,
                value=params.get("overbought", 70),
                help="이 값 이상이면 과매수로 판단합니다."
            )
            
        params["signal_type"] = st.radio(
            "신호 유형",
            ["과매도 매수만", "과매수 매도만", "모두"],
            index=["과매도 매수만", "과매수 매도만", "모두"].index(params.get("signal_type", "과매도 매수만")),
            help="어떤 신호를 사용할지 선택합니다."
        )
            
    elif strategy_type == "MACD 시그널":
        col1, col2, col3 = st.columns(3)
        with col1:
            params["fast_period"] = st.slider(
                "빠른 EMA 기간",
                min_value=5,
                max_value=20,
                value=params.get("fast_period", 12),
                help="MACD 계산에 사용하는 짧은 기간 EMA입니다."
            )
        with col2:
            params["slow_period"] = st.slider(
                "느린 EMA 기간",
                min_value=10,
                max_value=40,
                value=params.get("slow_period", 26),
                help="MACD 계산에 사용하는 긴 기간 EMA입니다."
            )
        with col3:
            params["signal_period"] = st.slider(
                "시그널 기간",
                min_value=5,
                max_value=15,
                value=params.get("signal_period", 9),
                help="MACD 시그널 라인의 기간입니다."
            )
            
        params["signal_type"] = st.radio(
            "신호 유형",
            ["골든 크로스만", "데드 크로스만", "모두"],
            index=["골든 크로스만", "데드 크로스만", "모두"].index(params.get("signal_type", "골든 크로스만")),
            help="MACD가 시그널 라인을 상향/하향 돌파할 때의 신호입니다."
        )
            
    elif strategy_type == "가격 돌파":
        col1, col2 = st.columns(2)
        with col1:
            params["lookback_days"] = st.slider(
                "기준 기간 (일)",
                min_value=5,
                max_value=120,
                value=params.get("lookback_days", 20),
                help="고점/저점을 계산할 기간입니다."
            )
        
        with col2:
            params["threshold_pct"] = st.slider(
                "돌파 임계값 (%)",
                min_value=0.5,
                max_value=10.0,
                value=params.get("threshold_pct", 2.0),
                step=0.5,
                help="돌파로 간주할 최소 퍼센트입니다."
            )
        
        params["signal_type"] = st.radio(
            "신호 유형",
            ["저점 돌파 매수", "고점 돌파 매도", "모두"],
            index=["저점 돌파 매수", "고점 돌파 매도", "모두"].index(params.get("signal_type", "저점 돌파 매수")),
            help="가격이 고점/저점을 돌파할 때의 신호입니다."
        )
            
    elif strategy_type == "그물망 매매":
        col1, col2 = st.columns(2)
        with col1:
            params["grid_levels"] = st.slider(
                "그물망 단계",
                min_value=3,
                max_value=10,
                value=params.get("grid_levels", 5),
                help="몇 단계로 그물망을 구성할지 설정합니다."
            )
        
        with col2:
            params["grid_spacing_pct"] = st.slider(
                "단계 간격 (%)",
                min_value=1.0,
                max_value=10.0,
                value=params.get("grid_spacing_pct", 3.0),
                step=0.5,
                help="각 단계 사이의 가격 간격입니다."
            )
        
        params["base_amount_pct"] = st.slider(
            "기준 투자 비율 (%)",
            min_value=10,
            max_value=100,
            value=params.get("base_amount_pct", 50),
            help="첫 단계에서 사용할 자본 비율입니다."
        )
        
        params["increase_factor"] = st.slider(
            "단계별 투자금 증가율",
            min_value=1.0,
            max_value=2.0,
            value=params.get("increase_factor", 1.5),
            step=0.1,
            help="다음 단계로 넘어갈 때 투자금의 증가 비율입니다."
        )
            
    # 추가적인 전략 유형에 대한 처리 추가 가능
    
    return params 