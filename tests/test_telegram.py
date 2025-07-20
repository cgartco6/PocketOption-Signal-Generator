import unittest
from unittest.mock import patch, MagicMock
from core.telegram_bot import TelegramBot
import telegram

class TestTelegramIntegration(unittest.TestCase):
    def setUp(self):
        # Mock configuration
        self.config = {
            'Telegram': {
                'bot_token': 'test_token',
                'chat_id': 'test_chat_id'
            }
        }
        
        # Patch Telegram Bot
        self.telegram_patcher = patch('telegram.Bot')
        self.mock_bot_class = self.telegram_patcher.start()
        self.mock_bot = MagicMock()
        self.mock_bot_class.return_value = self.mock_bot

    def tearDown(self):
        self.telegram_patcher.stop()

    def test_bot_initialization(self):
        """Test Telegram bot initializes correctly"""
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        self.mock_bot_class.assert_called_once_with(token='test_token')
        
    def test_message_sending_success(self):
        """Test successful message delivery"""
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        result = bot.send_message('test_chat_id', 'Test message')
        
        # Verify bot called correctly
        self.mock_bot.send_message.assert_called_once_with(
            chat_id='test_chat_id',
            text='Test message',
            parse_mode='Markdown'
        )
        self.assertTrue(result)
        
    def test_message_sending_failure(self):
        """Test error handling for failed messages"""
        # Configure mock to raise exception
        self.mock_bot.send_message.side_effect = telegram.error.TelegramError("API error")
        
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        result = bot.send_message('test_chat_id', 'Test message')
        
        # Verify failure handling
        self.assertFalse(result)
        
    def test_message_formatting(self):
        """Test Markdown formatting support"""
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        
        # Test with Markdown content
        message = "**Bold** _Italic_ [Link](https://example.com)"
        bot.send_message('test_chat_id', message)
        
        # Verify parse mode
        self.mock_bot.send_message.assert_called_with(
            chat_id='test_chat_id',
            text=message,
            parse_mode='Markdown'
        )
        
    def test_long_message_handling(self):
        """Test message truncation for long content"""
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        
        # Create message longer than Telegram limit (4096 characters)
        long_message = "A" * 5000
        bot.send_message('test_chat_id', long_message)
        
        # Verify truncation
        sent_text = self.mock_bot.send_message.call_args[1]['text']
        self.assertLessEqual(len(sent_text), 4096)
        self.assertTrue(sent_text.endswith("... [truncated]"))
        
    def test_notification_structure(self):
        """Test signal notification format"""
        from core.signal_generator import SignalGenerator
        from core.telegram_bot import TelegramBot
        
        # Create mock signals
        signals = [
            {
                'asset': 'EUR/USD',
                'signal': 'BUY',
                'confidence': 85,
                'timestamp': '2023-01-01T12:00:00'
            },
            {
                'asset': 'Gold',
                'signal': 'STRONG BUY',
                'confidence': 92,
                'timestamp': '2023-01-01T12:00:00'
            }
        ]
        
        # Generate message
        message = "🚀 PocketOption Signals 🚀\n\n"
        message += "\n".join(
            [f"{s['asset']}: {s['signal']} (Confidence: {s['confidence']}%)" 
             for s in signals]
        )
        
        # Test with Telegram bot
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        bot.send_message('test_chat_id', message)
        
        # Verify content
        sent_text = self.mock_bot.send_message.call_args[1]['text']
        self.assertIn("PocketOption Signals", sent_text)
        self.assertIn("EUR/USD: BUY", sent_text)
        self.assertIn("Gold: STRONG BUY", sent_text)
        self.assertIn("Confidence: 85%", sent_text)
        self.assertIn("Confidence: 92%", sent_text)
        
    def test_retry_mechanism(self):
        """Test message retry on failure"""
        # Configure first call to fail, second to succeed
        self.mock_bot.send_message.side_effect = [
            telegram.error.TimedOut("Timeout"),
            None  # Success
        ]
        
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        with patch('time.sleep') as mock_sleep:
            result = bot.send_message('test_chat_id', 'Test message')
            
            # Verify retry
            self.assertEqual(self.mock_bot.send_message.call_count, 2)
            mock_sleep.assert_called_once_with(5)  # Wait before retry
            self.assertTrue(result)
            
    def test_network_failure_handling(self):
        """Test handling of network issues"""
        # Configure persistent failure
        self.mock_bot.send_message.side_effect = telegram.error.NetworkError("No connection")
        
        bot = TelegramBot(self.config['Telegram']['bot_token'])
        with patch('logging.Logger.error') as mock_logger:
            result = bot.send_message('test_chat_id', 'Test message')
            
            # Verify error handling
            self.assertFalse(result)
            mock_logger.assert_called()
            self.assertIn("NetworkError", mock_logger.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
