import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .langgraph_agent import LangGraphAgent
from .config import Config
from .reminder_system import ReminderSystem
from .storage import FileStorage

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
        
        # Initialize reminder system
        self.storage = FileStorage()
        self.reminder_system = ReminderSystem(self.storage, self._send_reminder_message)
        
        # Connect reminder system to agent
        self.agent.set_reminder_system(self.reminder_system)
        
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
            
            # Send the response without Markdown parsing to avoid entity errors
            await update.message.reply_text(response)
            
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
    
    def _send_reminder_message(self, user_id: str, message: str):
        """Send a reminder message to a user."""
        import asyncio
        import threading
        
        async def send_async():
            try:
                await self.application.bot.send_message(
                    chat_id=user_id, 
                    text=message, 
                    parse_mode='Markdown'
                )
                logger.info(f"Reminder sent successfully to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending reminder to user {user_id}: {e}")
        
        # Handle async message sending from background thread
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # Schedule the coroutine to run in the main thread's event loop
            asyncio.run_coroutine_threadsafe(send_async(), loop)
        except RuntimeError:
            # No running event loop, create a new one in a separate thread
            def run_in_thread():
                asyncio.run(send_async())
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Telegram bot...")
        
        # Start the reminder system
        self.reminder_system.start()
        logger.info("Reminder system started")
        
        try:
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        finally:
            # Stop the reminder system when bot stops
            self.reminder_system.stop()
    
    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping Telegram bot...")
        self.reminder_system.stop()
        await self.application.stop()
