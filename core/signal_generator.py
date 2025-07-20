import random
import json
import os
from datetime import datetime
from ai_agents import forex_agent, crypto_agent, stock_agent, commodity_agent, index_agent

class SignalGenerator:
    def __init__(self, config):
        self.config = config
        with open('config/assets_list.json') as f:
            self.assets = json.load(f)
        
    def generate_signals(self):
        signals = []
        selected_assets = random.sample(self.assets, min(5, len(self.assets)))
        
        for asset in selected_assets:
            asset_type = asset['type']
            
            if asset_type == 'forex':
                signal = forex_agent.generate_signal(asset['symbol'])
            elif asset_type == 'crypto':
                signal = crypto_agent.generate_signal(asset['symbol'])
            elif asset_type == 'stock':
                signal = stock_agent.generate_signal(asset['symbol'])
            elif asset_type == 'commodity':
                signal = commodity_agent.generate_signal(asset['symbol'])
            elif asset_type == 'index':
                signal = index_agent.generate_signal(asset['symbol'])
            else:
                continue
                
            signals.append({
                'asset': asset['name'],
                'symbol': asset['symbol'],
                'signal': signal,
                'confidence': random.randint(70, 95),
                'timestamp': datetime.now().isoformat()
            })
        
        return signals
