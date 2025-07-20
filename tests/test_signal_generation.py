import unittest
from unittest.mock import patch, MagicMock
from ai_agents import forex_agent, crypto_agent, stock_agent, commodity_agent, index_agent
from core.signal_generator import SignalGenerator
import pandas as pd
from datetime import datetime

class TestSignalGeneration(unittest.TestCase):
    def setUp(self):
        # Create sample data for technical indicators
        self.sample_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'High': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'Low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            'Volume': [10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000]
        }, index=pd.date_range(start='2023-01-01', periods=10, freq='D'))
        
        # Patch yfinance for all tests
        self.yfinance_patcher = patch('yfinance.download')
        self.mock_yfinance = self.yfinance_patcher.start()
        self.mock_yfinance.return_value = self.sample_data
        
        # Patch data fetcher
        self.data_fetcher_patcher = patch('core.data_fetcher.data_fetcher')
        self.mock_data_fetcher = self.data_fetcher_patcher.start()
        self.mock_data_fetcher.get_historical_data.return_value = self.sample_data

    def tearDown(self):
        self.yfinance_patcher.stop()
        self.data_fetcher_patcher.stop()

    def test_forex_agent_basic(self):
        """Test forex agent generates valid signals"""
        signal = forex_agent.generate_signal('EURUSD')
        self.assertIn(signal, ['STRONG BUY', 'BUY', 'SELL', 'STRONG SELL', 'HOLD'])
        
        # Test session awareness
        with patch('ai_agents.forex_agent.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 8  # European session
            signal_eu = forex_agent.generate_signal('EURUSD')
            mock_datetime.now.return_value.hour = 14  # US session
            signal_us = forex_agent.generate_signal('EURUSD')
            self.assertNotEqual(signal_eu, signal_us)

    def test_crypto_agent_indicators(self):
        """Test crypto agent uses technical indicators correctly"""
        signal = crypto_agent.generate_signal('BTCUSD')
        self.assertIn(signal, ['STRONG BUY', 'BUY', 'SELL', 'STRONG SELL', 'HOLD'])
        
        # Test with different RSI values
        with patch('ai_agents.crypto_agent.talib.RSI') as mock_rsi:
            mock_rsi.return_value = pd.Series([30] * 10)  # Oversold
            signal_low_rsi = crypto_agent.generate_signal('BTCUSD')
            self.assertIn('BUY', signal_low_rsi)
            
            mock_rsi.return_value = pd.Series([70] * 10)  # Overbought
            signal_high_rsi = crypto_agent.generate_signal('BTCUSD')
            self.assertIn('SELL', signal_high_rsi)

    def test_stock_agent_fundamentals(self):
        """Test stock agent incorporates trend analysis"""
        signal = stock_agent.generate_signal('AAPL')
        self.assertIn(signal, ['STRONG BUY', 'BUY', 'SELL', 'STRONG SELL', 'HOLD'])
        
        # Test trend detection
        with patch('ai_agents.stock_agent.talib.SMA') as mock_sma:
            # Bullish trend (50 > 200)
            mock_sma.side_effect = [
                pd.Series([100, 101, 102]),  # SMA_50
                pd.Series([90, 91, 92])      # SMA_200
            ]
            signal_bullish = stock_agent.generate_signal('AAPL')
            self.assertIn('BUY', signal_bullish)
            
            # Bearish trend (50 < 200)
            mock_sma.side_effect = [
                pd.Series([90, 91, 92]),     # SMA_50
                pd.Series([100, 101, 102])    # SMA_200
            ]
            signal_bearish = stock_agent.generate_signal('AAPL')
            self.assertIn('SELL', signal_bearish)

    def test_commodity_agent_seasonality(self):
        """Test commodity agent considers seasonality"""
        with patch('ai_agents.commodity_agent.datetime') as mock_datetime:
            # Gold positive seasonality (January)
            mock_datetime.now.return_value.month = 1
            signal_gold_jan = commodity_agent.generate_signal('GC=F')
            self.assertIn('BUY', signal_gold_jan)
            
            # Gold neutral seasonality (April)
            mock_datetime.now.return_value.month = 4
            signal_gold_apr = commodity_agent.generate_signal('GC=F')
            self.assertNotIn('STRONG BUY', signal_gold_apr)

    def test_index_agent_market_breadth(self):
        """Test index agent analyzes market breadth"""
        signal = index_agent.generate_signal('^GSPC')
        self.assertIn(signal, ['STRONG BUY', 'BUY', 'SELL', 'STRONG SELL', 'HOLD'])
        
        # Test with different RSI values
        with patch('ai_agents.index_agent.talib.RSI') as mock_rsi:
            mock_rsi.return_value = pd.Series([65] * 10)  # Strong breadth
            signal_strong = index_agent.generate_signal('^GSPC')
            self.assertIn('BUY', signal_strong)
            
            mock_rsi.return_value = pd.Series([45] * 10)  # Weak breadth
            signal_weak = index_agent.generate_signal('^GSPC')
            self.assertIn('HOLD', signal_weak)

    def test_signal_generator_integration(self):
        """Test full signal generator workflow"""
        # Mock configuration
        config = {
            'Assets': {
                'enabled_assets': 'forex,crypto,stock,commodity,index'
            }
        }
        
        # Mock assets list
        assets = [
            {"name": "EUR/USD", "symbol": "EURUSD", "type": "forex"},
            {"name": "Bitcoin", "symbol": "BTCUSD", "type": "crypto"},
            {"name": "Apple", "symbol": "AAPL", "type": "stock"},
            {"name": "Gold", "symbol": "XAUUSD", "type": "commodity"},
            {"name": "S&P 500", "symbol": "US500", "type": "index"}
        ]
        
        # Create generator
        generator = SignalGenerator(config)
        generator.assets = assets
        
        # Generate signals
        signals = generator.generate_signals()
        
        # Verify output
        self.assertEqual(len(signals), 5)
        for signal in signals:
            self.assertIn('asset', signal)
            self.assertIn('signal', signal)
            self.assertIn('confidence', signal)
            self.assertIn('timestamp', signal)
            self.assertIn(signal['signal'], ['STRONG BUY', 'BUY', 'SELL', 'STRONG SELL', 'HOLD'])
            
        # Test asset filtering
        config['Assets']['enabled_assets'] = 'forex,stock'
        generator = SignalGenerator(config)
        generator.assets = assets
        signals = generator.generate_signals()
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0]['asset'], "EUR/USD")
        self.assertEqual(signals[1]['asset'], "Apple")

    def test_error_handling(self):
        """Test agents handle errors gracefully"""
        # Simulate data fetch failure
        self.mock_yfinance.side_effect = Exception("API error")
        
        # Test each agent
        self.assertEqual(forex_agent.generate_signal('EURUSD'), "HOLD (Error: API error)")
        self.assertEqual(crypto_agent.generate_signal('BTCUSD'), "HOLD (Error: API error)")
        self.assertEqual(stock_agent.generate_signal('AAPL'), "HOLD (Error: API error)")
        self.assertEqual(commodity_agent.generate_signal('GC=F'), "HOLD (Error: API error)")
        self.assertEqual(index_agent.generate_signal('^GSPC'), "HOLD (Error: API error)")
        
        # Test with insufficient data
        self.mock_yfinance.return_value = pd.DataFrame()
        self.assertEqual(forex_agent.generate_signal('EURUSD'), "HOLD (Insufficient Data)")

if __name__ == '__main__':
    unittest.main()
