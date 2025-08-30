# LangGraph Telegram Bot

A powerful Telegram bot built with LangGraph and LangChain, featuring intelligent conversation handling and workflow management.

## Features

- 🤖 **LangGraph Integration**: Uses LangGraph for sophisticated conversation workflows
- 🧠 **OpenAI Integration**: Powered by OpenAI's language models
- 💬 **Smart Conversation Handling**: Routes different types of requests appropriately
- 📱 **Telegram Integration**: Full Telegram bot functionality with commands
- 🔧 **Modular Architecture**: Clean, maintainable code structure
- ⚡ **Async Support**: Built with async/await for better performance

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Telegram bot token

## Setup

### 1. Clone and Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 2. Get Your API Keys

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you'll need it for the next step)

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your API keys
nano .env
```

Fill in your API keys in the `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_MODEL_NAME=gpt-3.5-turbo
```

### 4. Run the Bot

```bash
python main.py
```

The bot will start and you should see:
```
✅ Configuration validated successfully
🤖 Bot initialized successfully
🚀 Starting bot... (Press Ctrl+C to stop)
```

## Usage

### Bot Commands

- `/start` - Start the conversation
- `/help` - Show available commands
- `/info` - Get information about the bot

### Regular Chat

You can also just send regular messages to the bot, and it will respond intelligently using the LangGraph workflow.

## Architecture

### LangGraph Workflow

The bot uses a LangGraph workflow with the following components:

1. **Input Analysis**: Analyzes user input to determine request type
2. **Request Routing**: Routes to appropriate handler based on analysis
3. **Response Generation**: Generates responses using OpenAI
4. **Special Request Handling**: Handles commands and special requests

### File Structure

```
selfmessage/
├── bot/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── langgraph_agent.py # LangGraph agent implementation
│   └── telegram_handler.py # Telegram bot handler
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
└── README.md             # This file
```

## Customization

### Adding New Commands

To add new commands, modify the `TelegramBot` class in `bot/telegram_handler.py`:

```python
async def _new_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle a new command."""
    user_id = str(update.effective_user.id)
    response = self.agent.process_message(user_id, "/newcommand")
    await update.message.reply_text(response, parse_mode='Markdown')

# Add to _setup_handlers method:
self.application.add_handler(CommandHandler("newcommand", self._new_command))
```

### Modifying the LangGraph Workflow

To modify the conversation workflow, edit the `LangGraphAgent` class in `bot/langgraph_agent.py`:

1. Add new nodes to the graph
2. Modify the routing logic
3. Update the state structure as needed

### Changing the AI Model

You can change the OpenAI model by modifying the `OPENAI_MODEL_NAME` in your `.env` file or by passing a different model name to the `LangGraphAgent` constructor.

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Make sure you've created a `.env` file with your API keys
   - Check that the variable names match exactly

2. **"Invalid token" error**
   - Verify your Telegram bot token is correct
   - Make sure you copied the entire token

3. **OpenAI API errors**
   - Check your OpenAI API key is valid
   - Ensure you have sufficient credits in your OpenAI account

### Logs

The bot provides detailed logging. Check the console output for any error messages or warnings.

## Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests

## License

This project is open source and available under the MIT License.
