"""
전략 템플릿 모델 모듈입니다.
"""
from typing import Dict, Any, List

class StrategyTemplate:
    """전략 템플릿 클래스"""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        strategy_type: str,
        default_params: Dict[str, Any],
        default_take_profit: float = 5.0,
        default_stop_loss: float = -5.0
    ):
        """
        전략 템플릿 초기화
        
        Args:
            id: 템플릿 ID
            name: 템플릿 이름
            description: 템플릿 설명
            strategy_type: 전략 유형
            default_params: 기본 매개변수
            default_take_profit: 기본 이익실현 비율
            default_stop_loss: 기본 손절매 비율
        """
        self.id = id
        self.name = name
        self.description = description
        self.strategy_type = strategy_type
        self.default_params = default_params
        self.default_take_profit = default_take_profit
        self.default_stop_loss = default_stop_loss
    
    def to_dict(self) -> Dict[str, Any]:
        """
        템플릿을 딕셔너리로 변환
        
        Returns:
            템플릿 정보가 담긴 딕셔너리
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type,
            "params": self.default_params,
            "take_profit": self.default_take_profit,
            "stop_loss": self.default_stop_loss
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyTemplate':
        """
        딕셔너리에서 템플릿 객체 생성
        
        Args:
            data: 템플릿 정보가 담긴 딕셔너리
            
        Returns:
            생성된 템플릿 객체
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            strategy_type=data["strategy_type"],
            default_params=data["default_params"],
            default_take_profit=data.get("default_take_profit", 5.0),
            default_stop_loss=data.get("default_stop_loss", -5.0)
        )

# 기본 제공 템플릿 정의
_template_list = [
    StrategyTemplate(
        id="ma_cross",
        name="이동평균선 교차 전략",
        description="단기 이동평균선이 장기 이동평균선을 상향 돌파할 때 매수, 하향 돌파할 때 매도하는 전략입니다.",
        strategy_type="이동평균 교차",
        default_params={
            "short_period": 5,
            "long_period": 20
        },
        default_take_profit=10.0,
        default_stop_loss=-5.0
    ),
    StrategyTemplate(
        id="rsi",
        name="RSI 과매수/과매도 전략",
        description="RSI 지표가 과매수 구간에 진입하면 매도, 과매도 구간에 진입하면 매수하는 전략입니다.",
        strategy_type="RSI 과매수/과매도",
        default_params={
            "period": 14,
            "overbought": 70,
            "oversold": 30
        },
        default_take_profit=15.0,
        default_stop_loss=-7.0
    ),
    StrategyTemplate(
        id="breakout",
        name="가격 돌파 전략",
        description="일정 기간 동안의 최고가를 돌파하면 매수, 최저가를 하향 돌파하면 매도하는 전략입니다.",
        strategy_type="가격 돌파",
        default_params={
            "lookback_days": 20,
            "threshold_pct": 2.0
        },
        default_take_profit=20.0,
        default_stop_loss=-10.0
    )
] 

# 리스트에서 딕셔너리로 변환 (템플릿 이름을 키로 사용)
DEFAULT_TEMPLATES = {template.name: template.to_dict() for template in _template_list} 