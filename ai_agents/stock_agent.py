import yfinance as yf
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta

def generate_signal(symbol):
    """Generate trading signals for stocks using fundamental and technical analysis"""
    try:
        # Get data - different timeframes for better analysis
        end_date = datetime.now()
        data_daily = yf.download(symbol, start=end_date - timedelta(days=365), end=end_date)
        data_hourly = yf.download(symbol, period='60d', interval='60m')
        
        if len(data_daily) < 100 or len(data_hourly) < 100:
            return "HOLD (Insufficient Data)"
        
        # Calculate technical indicators (Daily)
        data_daily['SMA_50'] = talib.SMA(data_daily['Close'], timeperiod=50)
        data_daily['SMA_200'] = talib.SMA(data_daily['Close'], timeperiod=200)
        data_daily['RSI'] = talib.RSI(data_daily['Close'], timeperiod=14)
        
        # Calculate technical indicators (Hourly)
        data_hourly['MACD'], data_hourly['MACD_signal'], _ = talib.MACD(data_hourly['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        data_hourly['Stoch_%K'], data_hourly['Stoch_%D'] = talib.STOCH(data_hourly['High'], data_hourly['Low'], data_hourly['Close'])
        
        # Get latest values
        last_close = data_hourly['Close'].iloc[-1]
        sma50 = data_daily['SMA_50'].iloc[-1]
        sma200 = data_daily['SMA_200'].iloc[-1]
        last_rsi = data_daily['RSI'].iloc[-1]
        last_macd = data_hourly['MACD'].iloc[-1]
        last_macd_signal = data_hourly['MACD_signal'].iloc[-1]
        last_stoch_k = data_hourly['Stoch_%K'].iloc[-1]
        last_stoch_d = data_hourly['Stoch_%D'].iloc[-1]
        
        # Sentiment analysis (simulated)
        trend_strength = "BULLISH" if sma50 > sma200 else "BEARISH"
        
        # AI Decision Matrix
        buy_signals = 0
        sell_signals = 0
        
        # Golden/Death Cross
        if data_daily['SMA_50'].iloc[-1] > data_daily['SMA_50'].iloc[-5] and data_daily['SMA_50'].iloc[-1] > data_daily['SMA_200'].iloc[-1]:
            buy_signals += 2
        elif data_daily['SMA_50'].iloc[-1] < data_daily['SMA_50'].iloc[-5] and data_daily['SMA_50'].iloc[-1] < data_daily['SMA_200'].iloc[-1]:
            sell_signals += 2
            
        # RSI analysis
        if last_rsi < 40:
            buy_signals += 1
        elif last_rsi > 70:
            sell_signals += 1
            
        # MACD crossover
        if last_macd > last_macd_signal and data_hourly['MACD'].iloc[-2] < data_hourly['MACD_signal'].iloc[-2]:
            buy_signals += 1
        elif last_macd < last_macd_signal and data_hourly['MACD'].iloc[-2] > data_hourly['MACD_signal'].iloc[-2]:
            sell_signals += 1
            
        # Stochastic crossover
        if last_stoch_k > last_stoch_d and data_hourly['Stoch_%K'].iloc[-2] < data_hourly['Stoch_%D'].iloc[-2]:
            buy_signals += 1
        elif last_stoch_k < last_stoch_d and data_hourly['Stoch_%K'].iloc[-2] > data_hourly['Stoch_%D'].iloc[-2]:
            sell_signals += 1
        
        # Volume analysis
        volume_avg = data_daily['Volume'].mean()
        last_volume = data_daily['Volume'].iloc[-1]
        volume_conf = " (High Volume)" if last_volume > volume_avg * 1.5 else ""
        
        # Generate final signal
        if buy_signals >= 4:
            return f"STRONG BUY {trend_strength}{volume_conf}"
        elif buy_signals >= 2 and buy_signals > sell_signals:
            return f"BUY {trend_strength}{volume_conf}"
        elif sell_signals >= 4:
            return f"STRONG SELL {trend_strength}{volume_conf}"
        elif sell_signals >= 2 and sell_signals > buy_signals:
            return f"SELL {trend_strength}{volume_conf}"
        else:
            return f"HOLD {trend_strength} (Consolidation)"
            
    except Exception as e:
        return f"HOLD (Error: {str(e)})"
