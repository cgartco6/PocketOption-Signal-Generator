import telegram
import logging

class TelegramBot:
    def __init__(self, token):
        self.bot = telegram.Bot(token=token)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
    def send_message(self, chat_id, text):
        try:
            self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            print(f"Telegram error: {str(e)}")
            return False
