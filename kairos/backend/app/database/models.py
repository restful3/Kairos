from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

class StrategyDB:
    def __init__(self):
        # MongoDB 연결
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.client = MongoClient(mongo_uri)
        self.db = self.client.kairos
        self.strategies = self.db.strategies

        # 인덱스 생성
        self.create_indexes()

    def create_indexes(self):
        """필요한 인덱스 생성"""
        self.strategies.create_index([("name", 1)], unique=True)
        self.strategies.create_index([("status.is_active", 1)])
        self.strategies.create_index([("stock.code", 1)])

    def create_strategy(self, strategy_data: dict) -> str:
        """새로운 전략 생성"""
        strategy_doc = {
            "name": strategy_data["name"],
            "stock": {
                "code": strategy_data["stock_code"],
                "name": strategy_data["stock_name"]
            },
            "type": strategy_data["strategy_type"],
            "params": strategy_data["params"],
            "risk_management": {
                "take_profit": float(strategy_data["take_profit"]),
                "stop_loss": float(strategy_data["stop_loss"]),
                "investment_amount": int(strategy_data["investment_amount"])
            },
            "status": {
                "is_active": False,
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            },
            "versions": [{
                "version": 1,
                "date": datetime.utcnow(),
                "params": strategy_data["params"]
            }],
            "backtest_history": [],
            "signals": []
        }
        
        result = self.strategies.insert_one(strategy_doc)
        return str(result.inserted_id)

    def update_strategy(self, strategy_id: str, update_data: dict) -> bool:
        """전략 업데이트"""
        strategy_id = ObjectId(strategy_id)
        current = self.strategies.find_one({"_id": strategy_id})
        
        if not current:
            return False

        update_doc = {}
        
        # 기본 정보 업데이트
        if "name" in update_data:
            update_doc["name"] = update_data["name"]
        if "stock_code" in update_data:
            update_doc["stock.code"] = update_data["stock_code"]
            update_doc["stock.name"] = update_data["stock_name"]
        if "strategy_type" in update_data:
            update_doc["type"] = update_data["strategy_type"]
        
        # 파라미터 변경 시 새 버전 추가
        if "params" in update_data and update_data["params"] != current["params"]:
            new_version = {
                "version": len(current["versions"]) + 1,
                "date": datetime.utcnow(),
                "params": update_data["params"]
            }
            update_doc["params"] = update_data["params"]
            update_doc["versions"] = current["versions"] + [new_version]
        
        # 리스크 관리 설정 업데이트
        if any(key in update_data for key in ["take_profit", "stop_loss", "investment_amount"]):
            update_doc["risk_management"] = {
                "take_profit": float(update_data.get("take_profit", current["risk_management"]["take_profit"])),
                "stop_loss": float(update_data.get("stop_loss", current["risk_management"]["stop_loss"])),
                "investment_amount": int(update_data.get("investment_amount", current["risk_management"]["investment_amount"]))
            }
        
        # 상태 업데이트
        if "is_active" in update_data:
            update_doc["status.is_active"] = update_data["is_active"]
        update_doc["status.last_updated"] = datetime.utcnow()
        
        result = self.strategies.update_one(
            {"_id": strategy_id},
            {"$set": update_doc}
        )
        
        return result.modified_count > 0

    def delete_strategy(self, strategy_id: str) -> bool:
        """전략 삭제"""
        result = self.strategies.delete_one({"_id": ObjectId(strategy_id)})
        return result.deleted_count > 0

    def get_strategy(self, strategy_id: str) -> dict:
        """전략 조회"""
        strategy = self.strategies.find_one({"_id": ObjectId(strategy_id)})
        if strategy:
            strategy["_id"] = str(strategy["_id"])
        return strategy

    def get_all_strategies(self) -> list:
        """모든 전략 조회"""
        strategies = list(self.strategies.find())
        for strategy in strategies:
            strategy["_id"] = str(strategy["_id"])
        return strategies

    def get_active_strategies(self) -> list:
        """활성화된 전략만 조회"""
        strategies = list(self.strategies.find({"status.is_active": True}))
        for strategy in strategies:
            strategy["_id"] = str(strategy["_id"])
        return strategies

    def add_backtest_result(self, strategy_id: str, result: dict) -> bool:
        """백테스트 결과 추가"""
        result["date"] = datetime.utcnow()
        update_result = self.strategies.update_one(
            {"_id": ObjectId(strategy_id)},
            {"$push": {"backtest_history": result}}
        )
        return update_result.modified_count > 0

    def add_signal(self, strategy_id: str, signal: dict) -> bool:
        """새로운 시그널 추가"""
        signal["date"] = datetime.utcnow()
        update_result = self.strategies.update_one(
            {"_id": ObjectId(strategy_id)},
            {
                "$push": {
                    "signals": {
                        "$each": [signal],
                        "$slice": -100  # 최근 100개만 유지
                    }
                }
            }
        )
        return update_result.modified_count > 0

    def get_strategy_signals(self, strategy_id: str, limit: int = 100) -> list:
        """전략의 시그널 조회"""
        strategy = self.strategies.find_one(
            {"_id": ObjectId(strategy_id)},
            {"signals": {"$slice": -limit}}
        )
        return strategy.get("signals", []) if strategy else [] 