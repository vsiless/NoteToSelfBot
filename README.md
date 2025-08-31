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
└── # 🤖 Smart Link Organizer Bot

A powerful Telegram bot built with LangGraph that helps you organize articles, job posts, grants, and other links with intelligent deadline tracking, progress monitoring, and automated reminders.

## ✨ Features

### 📋 **Link Management**
- **Automatic categorization** of URLs into job applications, grants, research, learning, etc.
- **Smart deadline extraction** from natural language (e.g., "due next Friday")
- **Priority levels** (1-5) for task importance
- **Status tracking** (TODO, In Progress, Done, Paused, Waiting, Expired)

### 🎯 **Progress & Milestones**
- **Milestone tracking** - Break down tasks into smaller steps
- **Progress percentage** - Automatic calculation based on completed milestones
- **Activity tracking** - Monitor when you last worked on tasks
- **Progress summaries** - Get overview of all your tasks and completion rates

### 🔔 **Smart Reminders**
- **Automatic notifications** for:
  - Overdue items (every 4 hours)
  - Items due today (morning alerts)
  - Items due tomorrow (evening alerts)
  - Items due in 3 days and 1 week
- **Daily summaries** (9 AM) with your task overview
- **Weekly summaries** (Monday 9 AM) with progress reports
- **On-demand reminders** for specific tasks

### 📊 **Analytics & Visualization**
- **Progress tracking** with completion rates
- **LangGraph workflow visualization** 
- **Task categorization** with emoji indicators
- **Deadline countdown** with urgency indicators

## 🚀 Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Telegram Bot Token

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd selfmessage
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_openai_api_key
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

4. **Run the bot**
```bash
python main.py
```

## 📱 Usage

### Basic Commands

**Link Management:**
- Send any URL: `https://example.com/job - Software Engineer at Google due 12/31/2024`
- Mark complete: `done abc12345`
- Update status: `mark abc12345 as in_progress`

**View Your Links:**
- `list all` - Show all saved links
- `list jobs` - Show job applications only
- `list grants` - Show grant applications
- `list overdue` - Show overdue items
- `list deadlines` - Show upcoming deadlines

**Progress & Milestones:**
- `add milestone abc12345 Submit resume` - Add milestone to task
- `complete milestone def67890` - Mark milestone as done
- `list milestones abc12345` - Show task milestones
- `progress all` - Show overall progress summary
- `progress abc12345` - Show progress for specific task

**Reminders:**
- `remind me about abc12345` - Get immediate reminder
- Automatic reminders are sent based on deadlines

**Other:**
- `/help` - Show all commands
- `/info` - About the bot
- `visualize` - Generate workflow diagrams

### Example Workflows

**Job Application Tracking:**
```
1. Send: "https://company.com/careers/engineer - Senior Engineer role due Jan 15"
2. Add milestones: "add milestone abc12345 Tailor resume"
3. Add milestone: "add milestone abc12345 Submit application"
4. Complete: "complete milestone def67890"
5. Check progress: "progress abc12345"
```

**Grant Application Management:**
```
1. Send: "https://foundation.org/grant - Research grant due March 1"
2. Add milestones: "add milestone xyz98765 Write proposal"
3. Add milestone: "add milestone xyz98765 Get recommendation letters"
4. Track: "list grants" to see all grant applications
```

## 🏗️ Architecture

### Core Components

- **`LangGraphAgent`** - Main conversational AI with workflow routing
- **`ReminderSystem`** - Background scheduler for deadline notifications
- **`LinkProcessor`** - URL analysis and categorization
- **`FileStorage`** - Persistent data storage
- **`Models`** - Data structures for links, milestones, and progress

### Workflow

```
User Message → Analyze Input → Route to Handler → Process → Send Response
                     ↓
            [Links, Status, Special, General]
                     ↓
         [Save Links, Update Status, Show Info, Chat]
```

### Reminder Schedule

- **Every 4 hours**: Check for overdue items
- **Daily 9 AM**: Send daily summary
- **Daily 6 PM**: Check upcoming deadlines
- **Monday 9 AM**: Send weekly summary

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_enhanced_bot.py
```

Tests cover:
- ✅ Enhanced models with milestones
- ✅ Storage with milestone persistence
- ✅ Reminder system functionality
- ✅ Progress tracking calculations
- ✅ Agent command handling

## 📁 Project Structure

```
selfmessage/
├── bot/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── langgraph_agent.py     # Main LangGraph agent
│   ├── models.py              # Data models
│   ├── storage.py             # File-based storage
│   ├── reminder_system.py     # Automated reminders
│   ├── link_processor.py      # URL processing
│   ├── telegram_handler.py    # Telegram integration
│   └── graph_visualizer.py    # Workflow visualization
├── main.py                    # Entry point
├── test_enhanced_bot.py       # Test suite
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional
OPENAI_MODEL_NAME=gpt-4o-mini  # Default model
```

### Reminder Schedule Customization

Edit `reminder_system.py` to customize notification times:

```python
# Daily summary at 9 AM
schedule.every().day.at("09:00").do(self._send_daily_summary)

# Weekly summary on Monday at 9 AM  
schedule.every().monday.at("09:00").do(self._send_weekly_summary)

# Check urgent deadlines every 4 hours
schedule.every(4).hours.do(self._check_urgent_deadlines)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter issues:

1. Check the logs for error messages
2. Verify your API keys are correct
3. Ensure all dependencies are installed
4. Run the test suite to verify functionality

## 🎯 Roadmap

- [ ] Snooze functionality for reminders
- [ ] Web dashboard for link management
- [ ] Integration with calendar apps
- [ ] Export functionality (CSV, JSON)
- [ ] Team collaboration features
- [ ] Mobile app companion

---

**Built with ❤️ using LangGraph, OpenAI, and Python**             # This file
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
