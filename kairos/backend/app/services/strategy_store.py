import json
import os
from typing import List, Optional, Dict, Any
from ..models.strategy import Strategy
from pathlib import Path

class StrategyStore:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.file_path = self.data_dir / "strategies.json"
        if not self.file_path.exists():
            self._save_data({})

    def _load_data(self) -> Dict[str, Dict[str, Any]]:
        try:
            if not self.file_path.exists():
                return {}
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:  # 파일이 비어있는 경우
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            # JSON 파싱 오류 시 파일을 초기화
            self._save_data({})
            return {}
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return {}

    def _save_data(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json_data = {}
                for k, v in data.items():
                    if isinstance(v, Strategy):
                        json_data[k] = v.dict(by_alias=True)
                    else:
                        json_data[k] = v
                json.dump(json_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def get_all(self) -> List[Strategy]:
        data = self._load_data()
        strategies = []
        for strategy_data in data.values():
            try:
                strategies.append(Strategy(**strategy_data))
            except Exception as e:
                print(f"Error parsing strategy: {str(e)}")
        return strategies

    def create(self, strategy: Strategy) -> Strategy:
        data = self._load_data()
        data[strategy.id] = strategy.dict(by_alias=True)
        self._save_data(data)
        return strategy

    def get(self, strategy_id: str) -> Optional[Strategy]:
        data = self._load_data()
        if strategy_id not in data:
            return None
        try:
            return Strategy(**data[strategy_id])
        except Exception as e:
            print(f"Error getting strategy {strategy_id}: {str(e)}")
            return None

    def update(self, strategy_id: str, strategy: Strategy) -> Optional[Strategy]:
        data = self._load_data()
        if strategy_id not in data:
            return None
        data[strategy_id] = strategy.dict(by_alias=True)
        self._save_data(data)
        return strategy

    def delete(self, strategy_id: str) -> bool:
        data = self._load_data()
        if strategy_id not in data:
            return False
        del data[strategy_id]
        self._save_data(data)
        return True 