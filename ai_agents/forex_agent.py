import yfinance as yf
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
import pytz

def generate_signal(symbol):
    """Generate trading signals for forex pairs using sentiment and technical analysis"""
    try:
        # Convert symbol to yfinance format
        yf_symbol = f"{symbol}=X"
        
        # Get current time for session awareness
        now = datetime.now(pytz.utc)
        hour = now.hour
        
        # Determine active session
        sessions = {
            "Asian": (22, 8),    # 10PM - 8AM UTC
            "European": (7, 16), # 7AM - 4PM UTC
            "US": (12, 20)       # 12PM - 8PM UTC
        }
        
        current_session = "Asian"
        for session, (start, end) in sessions.items():
            if start <= hour < end:
                current_session = session
                break
        
        # Get data - multiple timeframes
        data_4h = yf.download(yf_symbol, period='30d', interval='60m')
        data_1h = yf.download(yf_symbol, period='7d', interval='60m')
        
        if len(data_4h) < 50 or len(data_1h) < 24:
            return "HOLD (Insufficient Data)"
        
        # Calculate technical indicators (4H)
        data_4h['EMA_20'] = talib.EMA(data_4h['Close'], timeperiod=20)
        data_4h['EMA_50'] = talib.EMA(data_4h['Close'], timeperiod=50)
        data_4h['RSI'] = talib.RSI(data_4h['Close'], timeperiod=14)
        
        # Calculate technical indicators (1H)
        data_1h['MACD'], data_1h['MACD_signal'], _ = talib.MACD(data_1h['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        data_1h['Stoch_%K'], data_1h['Stoch_%D'] = talib.STOCH(data_1h['High'], data_1h['Low'], data_1h['Close'])
        
        # Get latest values
        last_close = data_1h['Close'].iloc[-1]
        ema20_4h = data_4h['EMA_20'].iloc[-1]
        ema50_4h = data_4h['EMA_50'].iloc[-1]
        rsi_4h = data_4h['RSI'].iloc[-1]
        macd_1h = data_1h['MACD'].iloc[-1]
        macd_signal_1h = data_1h['MACD_signal'].iloc[-1]
        stoch_k_1h = data_1h['Stoch_%K'].iloc[-1]
        stoch_d_1h = data_1h['Stoch_%D'].iloc[-1]
        
        # Trend analysis
        trend = "BULLISH" if ema20_4h > ema50_4h else "BEARISH"
        trend_strength = abs(ema20_4h - ema50_4h) / last_close
        
        # AI Decision Matrix
        buy_signals = 0
        sell_signals = 0
        
        # Trend alignment
        if trend == "BULLISH":
            buy_signals += 1
        else:
            sell_signals += 1
            
        # RSI analysis
        if rsi_4h < 40:
            buy_signals += 1
        elif rsi_4h > 70:
            sell_signals += 1
            
        # MACD crossover
        if macd_1h > macd_signal_1h and data_1h['MACD'].iloc[-2] < data_1h['MACD_signal'].iloc[-2]:
            buy_signals += 1
        elif macd_1h < macd_signal_1h and data_1h['MACD'].iloc[-2] > data_1h['MACD_signal'].iloc[-2]:
            sell_signals += 1
            
        # Stochastic crossover
        if stoch_k_1h > stoch_d_1h and data_1h['Stoch_%K'].iloc[-2] < data_1h['Stoch_%D'].iloc[-2]:
            buy_signals += 1
        elif stoch_k_1h < stoch_d_1h and data_1h['Stoch_%K'].iloc[-2] > data_1h['Stoch_%D'].iloc[-2]:
            sell_signals += 1
        
        # Session strength
        if "USD" in symbol:
            session_strength = "STRONG" if current_session == "US" else "NORMAL"
        elif "EUR" in symbol:
            session_strength = "STRONG" if current_session == "European" else "NORMAL"
        elif "JPY" in symbol:
            session_strength = "STRONG" if current_session == "Asian" else "NORMAL"
        else:
            session_strength = "NORMAL"
        
        # Generate final signal
        if buy_signals >= 4:
            return f"STRONG BUY (Trend: {trend}, Session: {current_session})"
        elif buy_signals >= 3:
            return f"BUY (Trend: {trend}, Session: {current_session})"
        elif sell_signals >= 4:
            return f"STRONG SELL (Trend: {trend}, Session: {current_session})"
        elif sell_signals >= 3:
            return f"SELL (Trend: {trend}, Session: {current_session})"
        else:
            return f"HOLD (Consolidation in {current_session} Session)"
            
    except Exception as e:
        return f"HOLD (Error: {str(e)})"
