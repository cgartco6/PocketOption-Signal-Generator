import random
from datetime import datetime

def generate_signal(symbol):
    # In production: Connect to FX data API
    # Simulated AI logic
    signals = ['STRONG BUY', 'BUY', 'SELL', 'STRONG SELL', 'HOLD']
    weights = [0.25, 0.25, 0.2, 0.2, 0.1]
    
    # Market hour awareness
    hour = datetime.utcnow().hour
    if 12 <= hour < 16:  # NY/London overlap
        weights = [0.35, 0.3, 0.15, 0.15, 0.05]
    
    return random.choices(signals, weights=weights, k=1)[0]
