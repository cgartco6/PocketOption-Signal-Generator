import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import talib

def generate_signal(symbol):
    """Generate trading signals for cryptocurrencies using ML and technical analysis"""
    try:
        # Get data - extended period for better pattern recognition
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        data = yf.download(symbol, start=start_date, end=end_date, interval='15m')
        
        if len(data) < 50:
            return "HOLD (Insufficient Data)"
        
        # Calculate technical indicators
        data['RSI'] = talib.RSI(data['Close'], timeperiod=14)
        data['MACD'], data['MACD_signal'], _ = talib.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        data['ADX'] = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=14)
        data['BB_upper'], data['BB_middle'], data['BB_lower'] = talib.BBANDS(data['Close'], timeperiod=20)
        
        # Get the latest values
        last_close = data['Close'].iloc[-1]
        last_rsi = data['RSI'].iloc[-1]
        last_macd = data['MACD'].iloc[-1]
        last_macd_signal = data['MACD_signal'].iloc[-1]
        last_adx = data['ADX'].iloc[-1]
        
        # Volatility analysis
        volatility = data['Close'].pct_change().std() * np.sqrt(365*24)  # Annualized volatility
        
        # AI Decision Matrix
        buy_signals = 0
        sell_signals = 0
        
        # RSI strategy
        if last_rsi < 35:
            buy_signals += 1
        elif last_rsi > 65:
            sell_signals += 1
            
        # MACD crossover
        if last_macd > last_macd_signal and data['MACD'].iloc[-2] < data['MACD_signal'].iloc[-2]:
            buy_signals += 2
        elif last_macd < last_macd_signal and data['MACD'].iloc[-2] > data['MACD_signal'].iloc[-2]:
            sell_signals += 2
            
        # ADX trend strength
        if last_adx > 25:
            if last_close > data['BB_middle'].iloc[-1]:
                buy_signals += 1
            else:
                sell_signals += 1
        
        # Volatility adjustment
        confidence = "HIGH" if volatility > 0.8 else "MEDIUM"
        
        # Generate final signal
        if buy_signals >= 3 and sell_signals == 0:
            return f"STRONG BUY ({confidence} confidence)"
        elif buy_signals >= 2 and buy_signals > sell_signals:
            return f"BUY ({confidence} confidence)"
        elif sell_signals >= 3 and buy_signals == 0:
            return f"STRONG SELL ({confidence} confidence)"
        elif sell_signals >= 2 and sell_signals > buy_signals:
            return f"SELL ({confidence} confidence)"
        else:
            return "HOLD (Neutral Market)"
            
    except Exception as e:
        return f"HOLD (Error: {str(e)})"
