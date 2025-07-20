import yfinance as yf
import pandas as pd
import numpy as np
import time
import os
import json
import requests
from datetime import datetime, timedelta
from .config_manager import ConfigManager
import logging

# Configure logging
logging.basicConfig(
    filename='logs/data_fetcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.config = ConfigManager.load_config()
        self.cache_dir = 'data_cache'
        self._create_cache_dir()
        self.api_keys = self._load_api_keys()
        self.request_count = 0
        self.last_request_time = time.time()
        
    def _create_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")
    
    def _load_api_keys(self):
        """Load API keys from environment or config file"""
        keys = {}
        try:
            # Try to get from environment variables
            keys['alpha_vantage'] = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
            keys['twelvedata'] = os.getenv('TWELVE_DATA_API_KEY', 'demo')
            
            # Override with config file if available
            if 'API' in self.config:
                keys['alpha_vantage'] = self.config.get('API', 'alpha_vantage_key', fallback=keys['alpha_vantage'])
                keys['twelvedata'] = self.config.get('API', 'twelvedata_key', fallback=keys['twelvedata'])
                
            logger.info("API keys loaded successfully")
        except Exception as e:
            logger.error(f"Error loading API keys: {str(e)}")
            keys = {'alpha_vantage': 'demo', 'twelvedata': 'demo'}
        return keys
    
    def _rate_limit(self):
        """Enforce rate limiting to avoid API bans"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Free APIs typically allow 5 requests per minute
        if elapsed < 12:  # 12 seconds between requests = 5 per minute
            sleep_time = 12 - elapsed
            time.sleep(sleep_time)
            logger.debug(f"Rate limited: Slept for {sleep_time:.2f} seconds")
            
        self.last_request_time = time.time()
        self.request_count += 1
        
    def get_historical_data(self, symbol, period='1d', interval='15m', source='auto'):
        """
        Get historical price data for a symbol
        
        Args:
            symbol (str): Financial instrument symbol
            period (str): Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval (str): Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            source (str): Data source (yfinance, alpha_vantage, twelvedata, auto)
            
        Returns:
            pd.DataFrame: Historical data with OHLCV columns
        """
        cache_key = f"{symbol}_{period}_{interval}.csv"
        cache_path = os.path.join(self.cache_dir, cache_key)
        
        # Check cache first
        if os.path.exists(cache_path):
            try:
                data = pd.read_csv(cache_path, parse_dates=True, index_col='Date')
                if not data.empty:
                    logger.info(f"Loaded {symbol} data from cache: {cache_path}")
                    return data
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_path}: {str(e)}")
        
        # Determine best source
        if source == 'auto':
            source = self._select_data_source(symbol, interval)
        
        # Fetch data
        try:
            self._rate_limit()
            
            if source == 'yfinance':
                data = self._fetch_yfinance(symbol, period, interval)
            elif source == 'alpha_vantage':
                data = self._fetch_alpha_vantage(symbol, interval)
            elif source == 'twelvedata':
                data = self._fetch_twelvedata(symbol, period, interval)
            else:
                raise ValueError(f"Invalid data source: {source}")
            
            # Save to cache
            if not data.empty:
                data.to_csv(cache_path)
                logger.info(f"Cached {symbol} data: {cache_path}")
                
            return data
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _select_data_source(self, symbol, interval):
        """Select the best available data source for the request"""
        # Use premium sources for crypto and intraday data
        if interval in ['1m', '2m', '5m']:
            if self.api_keys['twelvedata'] != 'demo':
                return 'twelvedata'
            elif self.api_keys['alpha_vantage'] != 'demo':
                return 'alpha_vantage'
        
        # For other cases, yfinance is reliable and free
        return 'yfinance'
    
    def _fetch_yfinance(self, symbol, period, interval):
        """Fetch data using Yahoo Finance"""
        logger.info(f"Fetching {symbol} from Yahoo Finance ({period}, {interval})")
        
        # Handle different symbol formats
        if symbol.endswith('=X'):
            ticker = yf.Ticker(symbol)
        else:
            # Add exchange suffixes for better accuracy
            if '.' not in symbol and ' ' not in symbol:
                symbol = self._add_exchange_suffix(symbol)
            ticker = yf.Ticker(symbol)
        
        data = ticker.history(period=period, interval=interval, actions=False)
        
        # Handle empty data
        if data.empty:
            # Try without suffix if we added one
            if symbol != self._add_exchange_suffix(symbol):
                return self._fetch_yfinance(symbol.split('.')[0], period, interval)
            raise ValueError("No data returned from Yahoo Finance")
        
        # Clean and format data
        data.index.name = 'Date'
        data.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        return data
    
    def _add_exchange_suffix(self, symbol):
        """Add exchange suffix to symbol for better recognition"""
        # Map symbols to likely exchanges
        if symbol in ['US500', 'US30', 'JP225', 'DE40']:
            return f"^{symbol}"
        elif symbol in ['XAUUSD', 'XAGUSD']:
            return f"{symbol}=X"
        elif symbol in ['BTCUSD', 'ETHUSD']:
            return f"{symbol}-USD"
        elif len(symbol) <= 4 and symbol.isalpha():
            return f"{symbol}.AX"  # Assume Australian exchange for short symbols
        return symbol
    
    def _fetch_alpha_vantage(self, symbol, interval):
        """Fetch data using Alpha Vantage API"""
        logger.info(f"Fetching {symbol} from Alpha Vantage ({interval})")
        
        # Map intervals to Alpha Vantage parameters
        interval_map = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '60m': '60min',
            '1h': '60min',
            '1d': 'daily'
        }
        
        av_interval = interval_map.get(interval)
        if not av_interval:
            raise ValueError(f"Unsupported interval for Alpha Vantage: {interval}")
        
        # API endpoint selection
        function = 'TIME_SERIES_INTRADAY' if 'min' in av_interval else 'TIME_SERIES_DAILY'
        
        params = {
            'function': function,
            'symbol': symbol,
            'interval': av_interval if 'min' in av_interval else None,
            'outputsize': 'full',
            'apikey': self.api_keys['alpha_vantage']
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = requests.get('https://www.alphavantage.co/query', params=params)
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        if function == 'TIME_SERIES_INTRADAY':
            time_key = f"Time Series ({av_interval})"
        else:
            time_key = 'Time Series (Daily)'
        
        if time_key not in data:
            logger.error(f"Alpha Vantage error: {data.get('Note', 'Unknown error')}")
            return pd.DataFrame()
        
        df = pd.DataFrame.from_dict(data[time_key], orient='index')
        df.index = pd.to_datetime(df.index)
        df.index.name = 'Date'
        
        # Rename columns
        df = df.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        })
        
        # Convert to numeric
        df = df.apply(pd.to_numeric)
        
        # Sort chronologically
        return df.sort_index()
    
    def _fetch_twelvedata(self, symbol, period, interval):
        """Fetch data using Twelve Data API"""
        logger.info(f"Fetching {symbol} from Twelve Data ({period}, {interval})")
        
        # Map periods to Twelve Data format
        period_map = {
            '1d': '1',
            '5d': '5',
            '1mo': '30',
            '3mo': '90',
            '6mo': '180',
            '1y': '365',
            '2y': '730',
            'max': 'max'
        }
        
        # Convert interval to Twelve Data format
        interval_map = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '60m': '60min',
            '1h': '1h',
            '1d': '1day',
            '1wk': '1week',
            '1mo': '1month'
        }
        
        td_interval = interval_map.get(interval)
        if not td_interval:
            raise ValueError(f"Unsupported interval for Twelve Data: {interval}")
        
        td_period = period_map.get(period, '365')  # Default to 1 year
        
        params = {
            'symbol': symbol,
            'interval': td_interval,
            'outputsize': td_period,
            'apikey': self.api_keys['twelvedata']
        }
        
        response = requests.get('https://api.twelvedata.com/time_series', params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'values' not in data:
            logger.error(f"Twelve Data error: {data.get('message', 'Unknown error')}")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        df.index.name = 'Date'
        
        # Rename columns
        df = df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        
        # Convert to numeric
        df = df.apply(pd.to_numeric)
        
        # Sort chronologically
        return df.sort_index()
    
    def get_real_time_price(self, symbol):
        """Get real-time price for a symbol"""
        try:
            self._rate_limit()
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            if not data.empty:
                return data['Close'].iloc[-1]
        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {str(e)}")
        return None
    
    def get_multiple_prices(self, symbols):
        """Get real-time prices for multiple symbols efficiently"""
        try:
            self._rate_limit()
            tickers = yf.Tickers(" ".join(symbols))
            return tickers.download(period='1d', interval='1m', group_by='ticker')
        except Exception as e:
            logger.error(f"Error getting multiple prices: {str(e)}")
            return {}
    
    def get_technical_indicators(self, symbol, period='1y', interval='1d'):
        """
        Get technical indicators for a symbol
        Returns: dict with RSI, MACD, Bollinger Bands, etc.
        """
        data = self.get_historical_data(symbol, period, interval)
        if data.empty:
            return {}
        
        # Calculate indicators
        indicators = {}
        
        # RSI (14 periods)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['RSI'] = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD (12, 26, 9)
        exp12 = data['close'].ewm(span=12, adjust=False).mean()
        exp26 = data['close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        indicators['MACD'] = macd.iloc[-1]
        indicators['MACD_Signal'] = signal.iloc[-1]
        indicators['MACD_Hist'] = (macd - signal).iloc[-1]
        
        # Bollinger Bands (20 periods)
        sma20 = data['close'].rolling(window=20).mean()
        std20 = data['close'].rolling(window=20).std()
        indicators['BB_Upper'] = (sma20 + (std20 * 2)).iloc[-1]
        indicators['BB_Middle'] = sma20.iloc[-1]
        indicators['BB_Lower'] = (sma20 - (std20 * 2)).iloc[-1]
        indicators['BB_Percent'] = ((data['close'].iloc[-1] - indicators['BB_Lower']) / 
                                   (indicators['BB_Upper'] - indicators['BB_Lower']))
        
        # Moving Averages
        indicators['MA_50'] = data['close'].rolling(window=50).mean().iloc[-1]
        indicators['MA_200'] = data['close'].rolling(window=200).mean().iloc[-1]
        
        # Volume analysis
        indicators['Volume_Avg'] = data['volume'].rolling(window=20).mean().iloc[-1]
        indicators['Volume_Ratio'] = data['volume'].iloc[-1] / indicators['Volume_Avg']
        
        return indicators
    
    def get_market_sentiment(self, symbol):
        """Get market sentiment for a symbol"""
        # Placeholder - in a real system, this would call sentiment analysis APIs
        # or scrape news/social media
        return {
            'symbol': symbol,
            'sentiment': 'Neutral',
            'confidence': 50,
            'positive_news': 0,
            'negative_news': 0
        }
    
    def clear_cache(self, older_than_days=7):
        """Clear cached data older than specified days"""
        now = time.time()
        cutoff = now - (older_than_days * 86400)
        deleted = 0
        
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff:
                    try:
                        os.remove(file_path)
                        deleted += 1
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {str(e)}")
        
        logger.info(f"Cleared cache: Deleted {deleted} files older than {older_than_days} days")
        return deleted

# Singleton instance for easy access
data_fetcher = DataFetcher()

if __name__ == "__main__":
    # Test the data fetcher
    print("Testing DataFetcher...")
    
    # Test different asset types
    assets = [
        ('EURUSD=X', 'forex'),
        ('BTC-USD', 'crypto'),
        ('AAPL', 'stock'),
        ('GC=F', 'commodity'),
        ('^GSPC', 'index')
    ]
    
    for symbol, asset_type in assets:
        print(f"\nFetching {asset_type}: {symbol}")
        data = data_fetcher.get_historical_data(symbol, period='5d', interval='15m')
        
        if not data.empty:
            print(f"Latest data for {symbol}:")
            print(data.tail(1))
            
            # Test technical indicators
            if len(data) > 50:
                indicators = data_fetcher.get_technical_indicators(symbol, period='5d', interval='15m')
                print("\nTechnical Indicators:")
                for k, v in indicators.items():
                    print(f"{k}: {v:.4f}")
        else:
            print(f"Failed to fetch data for {symbol}")
    
    # Test cache clearing
    print("\nClearing old cache files...")
    deleted = data_fetcher.clear_cache(older_than_days=0)  # Delete all
    print(f"Deleted {deleted} cache files")
