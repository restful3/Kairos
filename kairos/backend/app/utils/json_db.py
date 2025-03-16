import json
import os
from typing import List, Dict, Any
from datetime import datetime
import uuid

class JsonDB:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """파일이 없으면 생성합니다."""
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path))
        
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({"strategies": []}, f, ensure_ascii=False, indent=2)

    def read_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """JSON 파일에서 데이터를 읽어옵니다."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def write_data(self, data: Dict[str, List[Dict[str, Any]]]):
        """JSON 파일에 데이터를 씁니다."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all(self) -> List[Dict[str, Any]]:
        """모든 전략을 가져옵니다."""
        data = self.read_data()
        return data["strategies"]

    def get_by_id(self, strategy_id: str) -> Dict[str, Any]:
        """ID로 전략을 찾습니다."""
        data = self.read_data()
        for strategy in data["strategies"]:
            if strategy["id"] == strategy_id:
                return strategy
        return None

    def create(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """새로운 전략을 생성합니다."""
        data = self.read_data()
        strategy_data["id"] = str(uuid.uuid4())
        strategy_data["created_at"] = datetime.utcnow().isoformat()
        strategy_data["updated_at"] = datetime.utcnow().isoformat()
        data["strategies"].append(strategy_data)
        self.write_data(data)
        return strategy_data

    def update(self, strategy_id: str, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """전략을 업데이트합니다."""
        data = self.read_data()
        for i, strategy in enumerate(data["strategies"]):
            if strategy["id"] == strategy_id:
                strategy_data["id"] = strategy_id
                strategy_data["created_at"] = strategy["created_at"]
                strategy_data["updated_at"] = datetime.utcnow().isoformat()
                data["strategies"][i] = strategy_data
                self.write_data(data)
                return strategy_data
        return None

    def delete(self, strategy_id: str) -> bool:
        """전략을 삭제합니다."""
        data = self.read_data()
        initial_length = len(data["strategies"])
        data["strategies"] = [s for s in data["strategies"] if s["id"] != strategy_id]
        if len(data["strategies"]) != initial_length:
            self.write_data(data)
            return True
        return False

# JSON 파일 경로 설정
DB_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "strategies.json")
json_db = JsonDB(DB_FILE_PATH) 