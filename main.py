from core.signal_generator import SignalGenerator
from core.telegram_bot import TelegramBot
from core.config_manager import ConfigManager
import time

def main():
    config = ConfigManager.load_config()
    bot = TelegramBot(config['Telegram']['bot_token'])
    
    generator = SignalGenerator(config)
    
    while True:
        try:
            signals = generator.generate_signals()
            if signals:
                message = "🚀 PocketOption Signals 🚀\n\n" + "\n".join(
                    [f"{s['asset']}: {s['signal']} (Confidence: {s['confidence']}%)" 
                     for s in signals]
                )
                bot.send_message(config['Telegram']['chat_id'], message)
        except Exception as e:
            print(f"Error: {str(e)}")
        
        time.sleep(int(config['Settings']['interval']))

if __name__ == "__main__":
    main()
