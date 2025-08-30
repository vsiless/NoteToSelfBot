import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .langgraph_agent import LangGraphAgent
from .config import Config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot handler with LangGraph integration."""
    
    def __init__(self):
        """Initialize the bot with LangGraph agent."""
        self.agent = LangGraphAgent(Config.OPENAI_MODEL_NAME)
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("info", self._info_command))
        
        # Message handler for all text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        user_id = str(update.effective_user.id)
        welcome_message = self.agent.process_message(user_id, "/start")
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        user_id = str(update.effective_user.id)
        help_message = self.agent.process_message(user_id, "/help")
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def _info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /info command."""
        user_id = str(update.effective_user.id)
        info_message = self.agent.process_message(user_id, "/info")
        await update.message.reply_text(info_message, parse_mode='Markdown')
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages."""
        user_id = str(update.effective_user.id)
        message_text = update.message.text
        
        try:
            # Process the message through LangGraph agent
            response = self.agent.process_message(user_id, message_text)
            
            # Send the response
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(
                "I'm sorry, I encountered an error while processing your message. Please try again."
            )
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot."""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "I'm sorry, something went wrong. Please try again later."
            )
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping Telegram bot...")
        await self.application.stop()
