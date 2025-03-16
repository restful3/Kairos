import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import logging
from app.api.client import api_client  # API 클라이언트 임포트

# 로깅 설정
logger = logging.getLogger("backtest_utils")

def run_backtest_simulation(strategy, days=90, initial_capital=10000000, fee_rate=0.0015, simplified=False, use_real_data=True):
    """
    백테스팅 시뮬레이션을 실행합니다.
    
    Args:
        strategy (dict): 백테스팅할 전략 정보
        days (int): 백테스팅 기간(일)
        initial_capital (int): 초기 자본금
        fee_rate (float): 거래 수수료율
        simplified (bool): 간략한 백테스팅 여부
        use_real_data (bool): 실제 API 데이터 사용 여부
        
    Returns:
        dict: 백테스팅 결과
    """
    # 종목 코드 유효성 검사
    stock_code = strategy.get('stock_code', '')
    if not stock_code or not stock_code.strip():
        raise ValueError("종목 코드가 비어있습니다. 유효한 종목 코드를 설정해주세요.")
    
    # 주가 데이터 가져오기
    stock_data = generate_stock_data(stock_code, days, use_real_data)
    
    # 전략 유형에 따른 매매 신호 생성
    signals = generate_trade_signals(stock_data, strategy)
    
    # 매매 시뮬레이션
    trades, portfolio_values = simulate_trades(
        stock_data=stock_data,
        signals=signals,
        initial_capital=initial_capital,
        fee_rate=fee_rate,
        strategy=strategy
    )
    
    # 성과 지표 계산
    metrics = calculate_performance_metrics(
        stock_data=stock_data,
        portfolio_values=portfolio_values,
        trades=trades,
        initial_capital=initial_capital
    )
    
    # 결과 반환
    result = {
        "strategy": strategy,
        "stock_data": stock_data,
        "signals": signals,
        "trades": trades,
        "portfolio_values": portfolio_values,
        "metrics": metrics,
        "backtest_params": {
            "days": days,
            "initial_capital": initial_capital,
            "fee_rate": fee_rate,
            "use_real_data": use_real_data
        },
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 전략에 백테스팅 히스토리 추가 (없으면 생성)
    if not simplified:
        if "backtest_history" not in strategy:
            strategy["backtest_history"] = []
        
        strategy["backtest_history"].append({
            "date": result["date"],
            "return": metrics["total_return"],
            "win_rate": metrics["win_rate"],
            "max_drawdown": metrics["max_drawdown"],
            "days": days,
            "use_real_data": use_real_data
        })
    
    return result


def generate_stock_data(stock_code, days, use_real_data=True):
    """
    주가 데이터 생성 (실제 API 또는 임시 데이터)
    
    Args:
        stock_code (str): 종목코드
        days (int): 조회 기간(일)
        use_real_data (bool): 실제 API 데이터 사용 여부
        
    Returns:
        pd.DataFrame: 주가 데이터
    """
    # 종목 코드 유효성 검사
    if not stock_code or not isinstance(stock_code, str) or not stock_code.strip():
        logger.error("유효하지 않은 종목 코드입니다: '%s'", stock_code)
        raise ValueError(f"유효하지 않은 종목 코드입니다: '{stock_code}'")
    
    # 종목 코드에서 공백 제거
    stock_code = stock_code.strip()
    
    if use_real_data:
        try:
            logger.info(f"종목코드 {stock_code}의 {days}일간 실제 데이터를 가져옵니다.")
            # API 클라이언트를 통해 실제 데이터 호출
            stock_history = api_client.get_stock_history(stock_code, days)
            
            if stock_history and len(stock_history) > 0:
                # API 응답 형식에 따라 데이터 변환
                data = []
                for item in stock_history:
                    try:
                        # 날짜 형식 변환 (YYYYMMDD -> datetime)
                        date_str = item.get('stck_bsop_date', '')
                        if not date_str:
                            continue
                            
                        if len(date_str) == 8:
                            date = datetime.strptime(date_str, '%Y%m%d')
                        else:
                            date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # 숫자 필드 변환 시 정수 형변환 오류 방지
                        open_price = int(item.get('stck_oprc', 0) or 0)
                        high_price = int(item.get('stck_hgpr', 0) or 0)
                        low_price = int(item.get('stck_lwpr', 0) or 0)
                        close_price = int(item.get('stck_clpr', 0) or 0)
                        volume = int(item.get('acml_vol', 0) or 0)
                        
                        data.append({
                            'date': date,
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume
                        })
                    except Exception as e:
                        logger.warning(f"데이터 항목 처리 중 오류 발생: {str(e)}")
                        continue
                
                # 데이터프레임으로 변환 및 날짜순 정렬
                if data:
                    df = pd.DataFrame(data)
                    df = df.sort_values('date')
                    
                    logger.info(f"실제 데이터 로드 완료: {len(df)}개의 주가 데이터")
                    
                    # 충분한 데이터가 있는지 확인
                    if len(df) >= 10:  # 최소 10일치 데이터 필요
                        return df
                    else:
                        logger.warning("가져온 데이터가 충분하지 않아 시뮬레이션 데이터로 대체합니다.")
                else:
                    logger.warning("API에서 데이터를 가져왔으나 처리 가능한 항목이 없습니다.")
        except Exception as e:
            logger.error(f"실제 데이터 로딩 중 오류 발생: {str(e)}")
            logger.info("시뮬레이션 데이터로 대체합니다.")
    
    # 실제 데이터를 가져오지 못했거나 시뮬레이션 데이터를 요청한 경우
    logger.info(f"종목코드 {stock_code}의 {days}일간 시뮬레이션 데이터를 생성합니다.")
    
    # 시뮬레이션 데이터 생성
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 영업일만 포함하도록 조정 (주말 제외 - 간단히 70%로 가정)
    business_days = int(days * 0.7)
    
    dates = pd.date_range(start=start_date, periods=business_days, freq='B')
    
    # 시드 고정으로 같은 종목은 같은 패턴 생성
    try:
        # 종목코드의 마지막 두 자리를 시드로 사용 (숫자가 아닌 경우 대체 방법 사용)
        seed = int(stock_code[-2:]) if stock_code[-2:].isdigit() else sum(ord(c) for c in stock_code)
        np.random.seed(seed)
    except Exception as e:
        logger.warning(f"시드 설정 중 오류 발생, 기본 시드 사용: {str(e)}")
        np.random.seed(42)  # 기본 시드
    
    # 초기 가격 설정 (종목코드에 따라 다르게)
    try:
        seed_value = int(stock_code[-2:]) if stock_code[-2:].isdigit() else sum(ord(c) for c in stock_code) % 100
        start_price = 50000 + seed_value * 1000
    except Exception:
        start_price = 50000  # 기본값
    
    # 추세 성분 (약간의 상승세)
    trend = np.linspace(0, days * 0.1, business_days)
    
    # 랜덤 워크 성분
    random_walk = np.random.normal(0, 1, business_days).cumsum() * (start_price * 0.02)
    
    # 계절성 성분 (주기적 패턴)
    seasonality = np.sin(np.linspace(0, 5 * np.pi, business_days)) * (start_price * 0.1)
    
    # 가격 데이터 생성
    close_prices = start_price + trend + random_walk + seasonality
    close_prices = np.maximum(close_prices, start_price * 0.5)  # 최소가격 보장
    
    # 일별 변동성으로 OHLC 데이터 생성
    daily_volatility = start_price * 0.015
    
    data = []
    for i, date in enumerate(dates):
        close = close_prices[i]
        high = close + abs(np.random.normal(0, daily_volatility))
        low = close - abs(np.random.normal(0, daily_volatility))
        open_price = low + (high - low) * np.random.random()
        
        # 거래량 - 가격 변동에 비례하게
        price_change = abs(close - close_prices[i-1] if i > 0 else 0)
        volume = int(np.random.normal(500000, 200000) + price_change * 100)
        volume = max(volume, 10000)
        
        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    # 데이터프레임으로 변환
    df = pd.DataFrame(data)
    
    logger.info(f"임시 데이터 생성 완료: {len(df)}개의 주가 데이터")
    return df


def generate_trade_signals(stock_data, strategy):
    """전략에 따른 매매 신호 생성"""
    df = stock_data.copy()
    
    # 신호 초기화
    df['signal'] = 0  # 0: 포지션 없음, 1: 매수, -1: 매도
    
    # 전략 유형에 따른 신호 생성
    if strategy['strategy_type'] == "이동평균선 교차 전략":
        # 이동평균선 계산
        short_period = strategy['params']['short_period']
        long_period = strategy['params']['long_period']
        
        df['ma_short'] = df['close'].rolling(window=short_period).mean()
        df['ma_long'] = df['close'].rolling(window=long_period).mean()
        
        # 골든 크로스 (단기선이 장기선 상향 돌파) - 매수 신호
        df.loc[(df['ma_short'] > df['ma_long']) & 
               (df['ma_short'].shift(1) <= df['ma_long'].shift(1)), 'signal'] = 1
        
        # 데드 크로스 (단기선이 장기선 하향 돌파) - 매도 신호
        df.loc[(df['ma_short'] < df['ma_long']) & 
               (df['ma_short'].shift(1) >= df['ma_long'].shift(1)), 'signal'] = -1
        
    elif strategy['strategy_type'] == "RSI 과매수/과매도 전략":
        # RSI 계산
        rsi_period = strategy['params']['rsi_period']
        oversold = strategy['params']['oversold']
        overbought = strategy['params']['overbought']
        
        # 가격 변화
        delta = df['close'].diff()
        
        # 상승/하락 구분
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        
        # 평균 상승/하락 계산
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        
        # RS 및 RSI 계산
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 과매도 상태에서 RSI 상승 시작 - 매수 신호
        df.loc[(df['rsi'] < oversold) & (df['rsi'].shift(1) < df['rsi']), 'signal'] = 1
        
        # 과매수 상태에서 RSI 하락 시작 - 매도 신호
        df.loc[(df['rsi'] > overbought) & (df['rsi'].shift(1) > df['rsi']), 'signal'] = -1
        
    elif strategy['strategy_type'] == "가격 돌파 전략":
        # 파라미터 가져오기
        target_price = strategy['params']['target_price']
        direction = strategy['params']['direction']
        
        if direction == "상향 돌파":
            # 가격이 목표가 상향 돌파 - 매수 신호
            df.loc[(df['close'] > target_price) & (df['close'].shift(1) <= target_price), 'signal'] = 1
            
            # 가격이 목표가 하향 이탈 - 매도 신호
            df.loc[(df['close'] < target_price) & (df['close'].shift(1) >= target_price), 'signal'] = -1
        else:  # 하향 돌파
            # 가격이 목표가 하향 돌파 - 매수 신호 (숏 전략을 가정)
            df.loc[(df['close'] < target_price) & (df['close'].shift(1) >= target_price), 'signal'] = 1
            
            # 가격이 목표가 상향 이탈 - 매도 신호
            df.loc[(df['close'] > target_price) & (df['close'].shift(1) <= target_price), 'signal'] = -1
    
    # 초기 데이터 NaN 처리
    df['signal'] = df['signal'].fillna(0)
    
    return df


def calculate_profit_pct(current_price, buy_price):
    """매수 가격 대비 현재 가격의 수익률(%) 계산"""
    return ((current_price - buy_price) / buy_price) * 100


def simulate_trades(stock_data, signals, initial_capital, fee_rate, strategy):
    """매매 시뮬레이션"""
    df = signals.copy()
    
    # 포지션 및 자산 트래킹
    position = 0  # 보유 주식 수
    cash = initial_capital  # 보유 현금
    trades = []  # 거래 내역
    
    portfolio_values = []  # 포트폴리오 가치 추적
    
    for i, row in df.iterrows():
        date = row['date']
        price = row['close']
        signal = row['signal']
        
        # 매수 신호 처리
        if signal == 1 and position == 0:  # 매수 신호 & 미보유 상태
            # 매수 가능 수량 계산 (수수료 고려)
            amount = cash * (1 - fee_rate)
            shares = int(amount / price)
            
            if shares > 0:
                # 매수 실행
                cost = shares * price
                fee = cost * fee_rate
                cash -= (cost + fee)
                position = shares
                
                # 거래 기록
                trades.append({
                    'date': date,
                    'type': 'buy',
                    'price': price,
                    'shares': shares,
                    'cost': cost,
                    'fee': fee,
                    'cash_after': cash
                })
        
        # 매도 신호 처리
        elif position > 0 and (signal == -1 or
            # 목표 수익률 도달 시 매도
            (len(trades) > 0 and trades[-1]['type'] == 'buy' and 
             calculate_profit_pct(price, trades[-1]['price']) >= strategy.get('take_profit', 10)) or
            # 손절 손실률 도달 시 매도
            (len(trades) > 0 and trades[-1]['type'] == 'buy' and 
             calculate_profit_pct(price, trades[-1]['price']) <= strategy.get('stop_loss', -5))):
            
            # 매도 실행
            revenue = position * price
            fee = revenue * fee_rate
            cash += (revenue - fee)
            
            # 수익률 계산
            buy_price = next((t['price'] for t in reversed(trades) if t['type'] == 'buy'), 0)
            profit_pct = calculate_profit_pct(price, buy_price)
            
            # 거래 기록
            trades.append({
                'date': date,
                'type': 'sell',
                'price': price,
                'shares': position,
                'revenue': revenue,
                'fee': fee,
                'cash_after': cash,
                'profit_pct': profit_pct
            })
            
            position = 0
        
        # 포트폴리오 가치 계산
        portfolio_value = cash + (position * price)
        portfolio_values.append({
            'date': date,
            'cash': cash,
            'stock_value': position * price,
            'total_value': portfolio_value,
            'position': position
        })
    
    # 마지막 날 포지션이 남아있으면 청산
    if position > 0:
        last_row = df.iloc[-1]
        date = last_row['date']
        price = last_row['close']
        
        revenue = position * price
        fee = revenue * fee_rate
        cash += (revenue - fee)
        
        # 수익률 계산
        buy_price = next((t['price'] for t in reversed(trades) if t['type'] == 'buy'), 0)
        profit_pct = calculate_profit_pct(price, buy_price)
        
        # 거래 기록
        trades.append({
            'date': date,
            'type': 'sell (청산)',
            'price': price,
            'shares': position,
            'revenue': revenue,
            'fee': fee,
            'cash_after': cash,
            'profit_pct': profit_pct
        })
        
        # 마지막 포트폴리오 가치 업데이트
        portfolio_values[-1]['cash'] = cash
        portfolio_values[-1]['stock_value'] = 0
        portfolio_values[-1]['total_value'] = cash
        portfolio_values[-1]['position'] = 0
    
    return trades, portfolio_values


def calculate_performance_metrics(stock_data, portfolio_values, trades, initial_capital):
    """백테스팅 성과 지표 계산"""
    if not portfolio_values:
        return {
            "total_return": 0,
            "annualized_return": 0,
            "win_rate": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "volatility": 0
        }
    
    # 데이터프레임으로 변환
    portfolio_df = pd.DataFrame(portfolio_values)
    
    # 초기값과 최종값
    initial_value = initial_capital
    final_value = portfolio_df.iloc[-1]['total_value']
    
    # 총 수익률 (%)
    total_return = ((final_value - initial_value) / initial_value) * 100
    
    # 연간화 수익률 (단위: %)
    days = (portfolio_df.iloc[-1]['date'] - portfolio_df.iloc[0]['date']).days
    if days > 0:
        annualized_return = (((final_value / initial_value) ** (365 / days)) - 1) * 100
    else:
        annualized_return = 0
    
    # 승률 (매도 거래 중 수익 거래 비율)
    sell_trades = [t for t in trades if t['type'] == 'sell' or t['type'] == 'sell (청산)']
    win_trades = [t for t in sell_trades if t.get('profit_pct', 0) > 0]
    
    win_rate = (len(win_trades) / len(sell_trades)) * 100 if sell_trades else 0
    
    # 최대 낙폭 (MDD)
    portfolio_df['previous_peak'] = portfolio_df['total_value'].cummax()
    portfolio_df['drawdown'] = ((portfolio_df['total_value'] - portfolio_df['previous_peak']) / portfolio_df['previous_peak']) * 100
    max_drawdown = portfolio_df['drawdown'].min()
    
    # 일별 수익률 계산
    portfolio_df['daily_return'] = portfolio_df['total_value'].pct_change() * 100
    
    # 변동성 (일별 수익률의 표준편차, 연간화)
    volatility = portfolio_df['daily_return'].std() * (252 ** 0.5)
    
    # 샤프 지수 (무위험 이자율 0% 가정)
    risk_free_rate = 0
    if volatility > 0:
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility
    else:
        sharpe_ratio = 0
    
    return {
        "total_return": round(total_return, 2),
        "annualized_return": round(annualized_return, 2),
        "win_rate": round(win_rate, 2),
        "max_drawdown": round(max_drawdown, 2),
        "volatility": round(volatility, 2),
        "sharpe_ratio": round(sharpe_ratio, 2)
    } 