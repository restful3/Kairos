import json
from datetime import datetime
from pathlib import Path
import uuid
from typing import List, Dict, Any, Optional
import threading
import logging
import os

logger = logging.getLogger(__name__)

class StrategyStore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            # 백엔드 루트 디렉토리 기준으로 data 디렉토리 생성
            self.data_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data"
            self.data_dir.mkdir(exist_ok=True)
            self.file_path = self.data_dir / "strategies.json"
            logger.info(f"전략 데이터 파일 경로: {self.file_path}")
            self._ensure_file_exists()
            self.initialized = True

    def _ensure_file_exists(self):
        """JSON 파일이 없으면 생성"""
        try:
            if not self.file_path.exists():
                initial_data = {
                    "strategies": [],
                    "last_updated": self._now_iso()
                }
                self._save_data(initial_data)
                logger.info(f"새로운 전략 데이터 파일 생성: {self.file_path}")
        except Exception as e:
            logger.error(f"전략 데이터 파일 생성 실패: {e}")
            raise

    def _load_data(self) -> dict:
        """JSON 파일 읽기 (thread-safe)"""
        with self._lock:
            try:
                if not self.file_path.exists():
                    return {"strategies": [], "last_updated": self._now_iso()}
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:  # 파일이 비어있는 경우
                        return {"strategies": [], "last_updated": self._now_iso()}
                    data = json.loads(content)
                    logger.debug(f"전략 데이터 로드 완료: {len(data.get('strategies', [])}개")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파일 읽기 오류: {e}")
                return {"strategies": [], "last_updated": self._now_iso()}
            except Exception as e:
                logger.error(f"파일 읽기 오류: {e}")
                return {"strategies": [], "last_updated": self._now_iso()}

    def _save_data(self, data: dict):
        """JSON 파일 저장 (thread-safe)"""
        with self._lock:
            try:
                # 임시 파일에 먼저 저장
                temp_file = self.file_path.with_suffix('.tmp')
                with open(temp_file, "w", encoding="utf-8") as f:
                    data["last_updated"] = self._now_iso()
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 임시 파일을 실제 파일로 이동 (atomic operation)
                temp_file.replace(self.file_path)
                logger.debug(f"전략 데이터 저장 완료: {len(data.get('strategies', [])}개")
            except Exception as e:
                logger.error(f"JSON 파일 저장 오류: {e}")
                if temp_file.exists():
                    temp_file.unlink()  # 임시 파일 삭제
                raise

    def _now_iso(self) -> str:
        """현재 시간을 ISO 형식 문자열로 반환"""
        return datetime.utcnow().isoformat()

    def _generate_id(self) -> str:
        """고유한 전략 ID 생성"""
        return str(uuid.uuid4())

    def create_strategy(self, strategy_data: dict) -> str:
        """새로운 전략 생성"""
        try:
            data = self._load_data()
            
            # 전략 이름 중복 체크
            if any(s["name"] == strategy_data["name"] for s in data["strategies"]):
                raise ValueError(f"이미 존재하는 전략 이름입니다: {strategy_data['name']}")
            
            strategy_id = self._generate_id()
            strategy = {
                "id": strategy_id,
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
                    "created_at": self._now_iso(),
                    "last_updated": self._now_iso()
                },
                "versions": [{
                    "version": 1,
                    "date": self._now_iso(),
                    "params": strategy_data["params"].copy()
                }],
                "backtest_history": []
            }
            
            data["strategies"].append(strategy)
            self._save_data(data)
            logger.info(f"전략 생성 성공 - ID: {strategy_id}, 이름: {strategy['name']}")
            
            return strategy_id
            
        except Exception as e:
            logger.error(f"전략 생성 실패: {str(e)}")
            raise

    def get_strategy(self, strategy_id: str) -> Optional[dict]:
        """전략 조회"""
        try:
            data = self._load_data()
            return next(
                (s for s in data["strategies"] if s["id"] == strategy_id),
                None
            )
        except Exception as e:
            logger.error(f"전략 조회 실패: {str(e)}")
            return None

    def get_all_strategies(self) -> List[dict]:
        """모든 전략 조회"""
        try:
            return self._load_data()["strategies"]
        except Exception as e:
            logger.error(f"전략 목록 조회 실패: {str(e)}")
            return []

    def update_strategy(self, strategy_id: str, update_data: dict) -> bool:
        """전략 업데이트"""
        try:
            data = self._load_data()
            strategy = next(
                (s for s in data["strategies"] if s["id"] == strategy_id),
                None
            )
            
            if not strategy:
                return False
                
            # 이름 변경 시 중복 체크
            if "name" in update_data and update_data["name"] != strategy["name"]:
                if any(s["name"] == update_data["name"] for s in data["strategies"] if s["id"] != strategy_id):
                    raise ValueError(f"이미 존재하는 전략 이름입니다: {update_data['name']}")
                strategy["name"] = update_data["name"]
            
            # 주식 정보 업데이트
            if "stock_code" in update_data:
                strategy["stock"].update({
                    "code": update_data["stock_code"],
                    "name": update_data["stock_name"]
                })
            
            # 전략 유형 업데이트
            if "strategy_type" in update_data:
                strategy["type"] = update_data["strategy_type"]
            
            # 파라미터 변경 시 새 버전 추가
            if "params" in update_data and update_data["params"] != strategy["params"]:
                strategy["params"] = update_data["params"].copy()
                strategy["versions"].append({
                    "version": len(strategy["versions"]) + 1,
                    "date": self._now_iso(),
                    "params": update_data["params"].copy()
                })
            
            # 리스크 관리 설정 업데이트
            if any(key in update_data for key in ["take_profit", "stop_loss", "investment_amount"]):
                strategy["risk_management"].update({
                    "take_profit": float(update_data.get("take_profit", strategy["risk_management"]["take_profit"])),
                    "stop_loss": float(update_data.get("stop_loss", strategy["risk_management"]["stop_loss"])),
                    "investment_amount": int(update_data.get("investment_amount", strategy["risk_management"]["investment_amount"]))
                })
            
            # 상태 업데이트
            if "is_active" in update_data:
                strategy["status"]["is_active"] = update_data["is_active"]
            strategy["status"]["last_updated"] = self._now_iso()
            
            self._save_data(data)
            return True
            
        except Exception as e:
            logger.error(f"전략 업데이트 실패: {str(e)}")
            return False

    def delete_strategy(self, strategy_id: str) -> bool:
        """전략 삭제"""
        try:
            data = self._load_data()
            original_length = len(data["strategies"])
            data["strategies"] = [s for s in data["strategies"] if s["id"] != strategy_id]
            
            if len(data["strategies"]) < original_length:
                self._save_data(data)
                return True
            return False
        except Exception as e:
            logger.error(f"전략 삭제 실패: {str(e)}")
            return False

    def add_backtest_result(self, strategy_id: str, result: dict) -> bool:
        """백테스트 결과 추가"""
        try:
            data = self._load_data()
            strategy = next(
                (s for s in data["strategies"] if s["id"] == strategy_id),
                None
            )
            
            if not strategy:
                return False
                
            result["date"] = self._now_iso()
            strategy["backtest_history"].append(result)
            
            # 최근 100개 결과만 유지
            if len(strategy["backtest_history"]) > 100:
                strategy["backtest_history"] = strategy["backtest_history"][-100:]
                
            self._save_data(data)
            return True
        except Exception as e:
            logger.error(f"백테스트 결과 추가 실패: {str(e)}")
            return False

    def get_active_strategies(self) -> List[dict]:
        """활성화된 전략만 조회"""
        try:
            data = self._load_data()
            return [s for s in data["strategies"] if s["status"]["is_active"]]
        except Exception as e:
            logger.error(f"활성 전략 조회 실패: {str(e)}")
            return []

    def get_strategy_by_name(self, name: str) -> Optional[dict]:
        """전략 이름으로 조회"""
        try:
            data = self._load_data()
            return next(
                (s for s in data["strategies"] if s["name"] == name),
                None
            )
        except Exception as e:
            logger.error(f"전략 이름 조회 실패: {str(e)}")
            return None 