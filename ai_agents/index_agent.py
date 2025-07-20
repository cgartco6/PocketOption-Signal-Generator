import yfinance as yf
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta

def generate_signal(symbol):
    """Generate trading signals for market indices using macro and technical analysis"""
    try:
        # Get data - multiple timeframes
        end_date = datetime.now()
        data_daily = yf.download(symbol, start=end_date - timedelta(days=365), end=end_date)
        data_4h = yf.download(symbol, period='60d', interval='60m')
        
        if len(data_daily) < 200 or len(data_4h) < 100:
            return "HOLD (Insufficient Data)"
        
        # Calculate technical indicators (Daily)
        data_daily['SMA_100'] = talib.SMA(data_daily['Close'], timeperiod=100)
        data_daily['SMA_200'] = talib.SMA(data_daily['Close'], timeperiod=200)
        data_daily['RSI'] = talib.RSI(data_daily['Close'], timeperiod=14)
        
        # Calculate technical indicators (4H)
        data_4h['MACD'], data_4h['MACD_signal'], _ = talib.MACD(data_4h['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        data_4h['Stoch_%K'], data_4h['Stoch_%D'] = talib.STOCH(data_4h['High'], data_4h['Low'], data_4h['Close'])
        
        # Get latest values
        last_close = data_4h['Close'].iloc[-1]
        sma100 = data_daily['SMA_100'].iloc[-1]
        sma200 = data_daily['SMA_200'].iloc[-1]
        rsi = data_daily['RSI'].iloc[-1]
        macd = data_4h['MACD'].iloc[-1]
        macd_signal = data_4h['MACD_signal'].iloc[-1]
        stoch_k = data_4h['Stoch_%K'].iloc[-1]
        stoch_d = data_4h['Stoch_%D'].iloc[-1]
        
        # Trend analysis
        major_trend = "BULL" if last_close > sma200 else "BEAR"
        intermediate_trend = "BULL" if last_close > sma100 else "BEAR"
        
        # Market breadth (simulated)
        breadth = "STRONG" if rsi > 60 and last_close > sma100 else "WEAK"
        
        # AI Decision Matrix
        buy_signals = 0
        sell_signals = 0
        
        # Major trend alignment
        if major_trend == "BULL":
            buy_signals += 1
        else:
            sell_signals += 1
            
        # MACD crossover
        if macd > macd_signal and data_4h['MACD'].iloc[-2] < data_4h['MACD_signal'].iloc[-2]:
            buy_signals += 1
        elif macd < macd_signal and data_4h['MACD'].iloc[-2] > data_4h['MACD_signal'].iloc[-2]:
            sell_signals += 1
            
        # Stochastic crossover
        if stoch_k > stoch_d and data_4h['Stoch_%K'].iloc[-2] < data_4h['Stoch_%D'].iloc[-2]:
            buy_signals += 1
        elif stoch_k < stoch_d and data_4h['Stoch_%K'].iloc[-2] > data_4h['Stoch_%D'].iloc[-2]:
            sell_signals += 1
            
        # RSI analysis
        if rsi < 40:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 1
            
        # Generate final signal
        if major_trend == "BULL":
            if buy_signals >= 3:
                return f"STRONG BUY (Trend: {major_trend}, Breadth: {breadth})"
            elif buy_signals >= 2:
                return f"BUY (Trend: {major_trend}, Breadth: {breadth})"
            else:
                return f"HOLD (Bull Market Correction)"
        else:  # BEAR market
            if sell_signals >= 3:
                return f"STRONG SELL (Trend: {major_trend}, Breadth: {breadth})"
            elif sell_signals >= 2:
                return f"SELL (Trend: {major_trend}, Breadth: {breadth})"
            else:
                return f"HOLD (Bear Market Rally)"
                
    except Exception as e:
        return f"HOLD (Error: {str(e)})"
