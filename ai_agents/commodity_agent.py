import yfinance as yf
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta

def generate_signal(symbol):
    """Generate trading signals for commodities using trend and seasonality analysis"""
    try:
        # Get data - longer period for commodities
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        data = yf.download(symbol, start=start_date, end=end_date, interval='60m')
        
        if len(data) < 100:
            return "HOLD (Insufficient Data)"
        
        # Calculate technical indicators
        data['EMA_20'] = talib.EMA(data['Close'], timeperiod=20)
        data['EMA_50'] = talib.EMA(data['Close'], timeperiod=50)
        data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=14)
        data['ADX'] = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=14)
        
        # Get latest values
        last_close = data['Close'].iloc[-1]
        ema20 = data['EMA_20'].iloc[-1]
        ema50 = data['EMA_50'].iloc[-1]
        atr = data['ATR'].iloc[-1]
        adx = data['ADX'].iloc[-1]
        
        # Volatility analysis
        volatility = atr / last_close
        
        # Trend analysis
        trend = "BULLISH" if ema20 > ema50 else "BEARISH"
        trend_strength = "STRONG" if adx > 25 else "WEAK"
        
        # Seasonality factor (simulated)
        month = datetime.now().month
        if symbol == 'GC=F':  # Gold
            seasonality = "POSITIVE" if month in [1, 9, 10] else "NEUTRAL"
        elif symbol == 'CL=F':  # Crude Oil
            seasonality = "POSITIVE" if month in [2, 3, 7] else "NEUTRAL"
        else:
            seasonality = "NEUTRAL"
        
        # AI Decision Matrix
        if trend == "BULLISH":
            if trend_strength == "STRONG" and volatility > 0.01 and seasonality == "POSITIVE":
                return f"STRONG BUY (Trend: {trend}, Volatility: High)"
            elif last_close > ema20 and adx > 20:
                return f"BUY (Trend: {trend}, Strength: {trend_strength})"
        else:  # BEARISH
            if trend_strength == "STRONG" and volatility > 0.01 and seasonality == "NEUTRAL":
                return f"STRONG SELL (Trend: {trend}, Volatility: High)"
            elif last_close < ema20 and adx > 20:
                return f"SELL (Trend: {trend}, Strength: {trend_strength})"
        
        # Mean reversion strategy
        if volatility > 0.015:
            if last_close < ema20 * 0.98:
                return f"BUY (Mean Reversion, Volatility: High)"
            elif last_close > ema20 * 1.02:
                return f"SELL (Mean Reversion, Volatility: High)"
        
        return f"HOLD (Trend: {trend}, Strength: {trend_strength}, Seasonality: {seasonality})"
            
    except Exception as e:
        return f"HOLD (Error: {str(e)})"
