import sqlite3
import json
import os
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path=None):
        """
        데이터베이스 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로 (기본값: kairos.db)
        """
        if db_path is None:
            # 기본 디렉토리 및 파일 경로 설정
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            db_dir = base_dir / "data"
            db_dir.mkdir(exist_ok=True)
            self.db_path = db_dir / "kairos.db"
        else:
            self.db_path = Path(db_path)
        
        logger.info(f"데이터베이스 경로: {self.db_path}")
        
        # 데이터베이스 연결 및 테이블 생성
        self._initialize_db()
    
    def _initialize_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 백테스트 결과 테이블 생성
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS backtest_results (
            id TEXT PRIMARY KEY,
            strategy_id TEXT NOT NULL,
            date TEXT NOT NULL,
            params TEXT NOT NULL,
            metrics TEXT NOT NULL,
            trades TEXT,
            portfolio_values TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("데이터베이스 초기화 완료")
    
    def _get_connection(self):
        """데이터베이스 연결 객체 반환"""
        return sqlite3.connect(self.db_path)
    
    def insert_backtest_result(self, result):
        """
        백테스트 결과 저장
        
        Args:
            result: 백테스트 결과 데이터
            
        Returns:
            저장된 백테스트 ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # JSON으로 직렬화
        params_json = json.dumps(result.get('backtest_params', {}))
        metrics_json = json.dumps(result.get('metrics', {}))
        trades_json = json.dumps(result.get('trades', []))
        portfolio_values_json = json.dumps(result.get('portfolio_values', []))
        
        # 날짜 처리
        date = result.get('date')
        if isinstance(date, datetime):
            date_str = date.isoformat()
        else:
            date_str = str(date)
        
        try:
            cursor.execute('''
            INSERT INTO backtest_results (id, strategy_id, date, params, metrics, trades, portfolio_values)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.get('id'),
                result.get('strategy_id'),
                date_str,
                params_json,
                metrics_json,
                trades_json,
                portfolio_values_json
            ))
            
            conn.commit()
            logger.info(f"백테스트 결과 저장 완료: {result.get('id')}")
            return result.get('id')
        except Exception as e:
            logger.error(f"백테스트 결과 저장 실패: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_backtest_result(self, backtest_id):
        """
        백테스트 결과 조회
        
        Args:
            backtest_id: 백테스트 ID
            
        Returns:
            백테스트 결과 또는 None
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하도록 설정
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM backtest_results WHERE id = ?', (backtest_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # JSON 역직렬화하여 결과 반환
            return {
                'id': row['id'],
                'strategy_id': row['strategy_id'],
                'date': row['date'],
                'backtest_params': json.loads(row['params']),
                'metrics': json.loads(row['metrics']),
                'trades': json.loads(row['trades']),
                'portfolio_values': json.loads(row['portfolio_values'])
            }
        except Exception as e:
            logger.error(f"백테스트 결과 조회 실패: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_backtest_results_by_strategy(self, strategy_id):
        """
        전략 ID로 백테스트 결과 목록 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            백테스트 결과 목록
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM backtest_results WHERE strategy_id = ? ORDER BY date DESC', (strategy_id,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'strategy_id': row['strategy_id'],
                    'date': row['date'],
                    'backtest_params': json.loads(row['params']),
                    'metrics': json.loads(row['metrics'])
                    # 리스트에서는 trades와 portfolio_values 데이터는 제외하여 메모리 절약
                })
            
            return results
        except Exception as e:
            logger.error(f"백테스트 결과 목록 조회 실패: {str(e)}")
            raise
        finally:
            conn.close()

# 데이터베이스 인스턴스 생성
db = Database() 