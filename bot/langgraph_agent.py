from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .link_processor import LinkProcessor
from .storage import FileStorage
from .models import LinkItem, TaskStatus, LinkCategory
from .graph_visualizer import GraphVisualizer
from .reminder_system import ReminderSystem
import json

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    user_id: Annotated[str, "The Telegram user ID"]
    current_step: Annotated[str, "Current step in the workflow"]
    context: Annotated[Dict[str, Any], "Additional context for the conversation"]
    links: Annotated[List[LinkItem], "Links extracted from the message"]
    storage: Annotated[FileStorage, "Storage instance for user data"]

class LangGraphAgent:
    """A LangGraph-based conversational agent for Telegram."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.link_processor = LinkProcessor()
        self.storage = FileStorage()
        self.visualizer = GraphVisualizer()
        
        # Initialize reminder system with a placeholder callback
        # This will be set properly when integrated with Telegram bot
        self.reminder_system = None
        self.graph = self._build_graph()
    
    def set_reminder_system(self, reminder_system: ReminderSystem):
        """Set the reminder system for this agent."""
        self.reminder_system = reminder_system
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("process_links", self._process_links)
        workflow.add_node("handle_status_update", self._handle_status_update)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_special_request", self._handle_special_request)
        
        # Set entry point
        workflow.set_entry_point("analyze_input")
        
        # Add conditional routing from analyze_input
        workflow.add_conditional_edges(
            "analyze_input",
            self._route_request,
            {
                "links": "process_links",
                "status_update": "handle_status_update",
                "general": "generate_response",
                "special": "handle_special_request"
            }
        )
        
        # Add edges to END
        workflow.add_edge("process_links", END)
        workflow.add_edge("handle_status_update", END)
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_special_request", END)
        
        return workflow.compile()
    
    def _analyze_input(self, state: AgentState) -> AgentState:
        """Analyze the user input to determine the type of request."""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Initialize storage in state if not present
        if "storage" not in state:
            state["storage"] = self.storage
        
        # Check for status updates first
        status_update = self.link_processor.parse_status_update(last_message)
        if status_update:
            state["current_step"] = "status_update"
            state["context"]["status_update"] = status_update
            return state
        
        # Check for links
        links = self.link_processor.process_message(last_message)
        if links:
            state["current_step"] = "links"
            state["links"] = links
            return state
        
        # Check for special commands
        special_keywords = ["help", "info", "about", "commands", "start", "stop", "list", "show", "deadlines", "overdue", "milestone", "progress", "remind", "snooze"]
        is_special = any(keyword in last_message.lower() for keyword in special_keywords)
        
        state["current_step"] = "special" if is_special else "general"
        return state
    
    def _route_request(self, state: AgentState) -> str:
        """Route the request based on analysis."""
        return state["current_step"]
    
    def _process_links(self, state: AgentState) -> AgentState:
        """Process and store links from the message."""
        user_id = state["user_id"]
        links = state["links"]
        storage = state["storage"]
        
        saved_links = []
        updated_links = []
        
        for link in links:
            try:
                # Use the new deduplication method
                if self.reminder_system:
                    # Use the new deduplication method with reminders
                    result_link, is_new = self.reminder_system.add_or_update_link_with_reminders(user_id, link)
                    if is_new:
                        saved_links.append(result_link)
                    else:
                        updated_links.append(result_link)
                else:
                    # Use deduplication in storage
                    result_link, is_new = storage.add_or_update_link(user_id, link)
                    if is_new:
                        saved_links.append(result_link)
                    else:
                        updated_links.append(result_link)
                        
            except Exception as e:
                print(f"Error processing link {link.url}: {e}")
                continue
        
        # Generate response
        response_parts = []
        
        if saved_links:
            response_parts.append("✅ **New links saved successfully!**\n")
            for link in saved_links:
                category_emoji = {
                    LinkCategory.JOB_APPLICATION: "💼",
                    LinkCategory.GRANT_APPLICATION: "💰",
                    LinkCategory.NOTES_TO_READ: "📖",
                    LinkCategory.RESEARCH: "🔬",
                    LinkCategory.LEARNING: "🎓",
                    LinkCategory.PERSONAL: "👤",
                    LinkCategory.OTHER: "🔗"
                }.get(link.category, "🔗")
                
                deadline_text = ""
                if link.deadline:
                    days_until = link.days_until_deadline()
                    if days_until is not None:
                        if days_until < 0:
                            deadline_text = f" ⚠️ **OVERDUE** ({abs(days_until)} days ago)"
                        elif days_until == 0:
                            deadline_text = " ⏰ **Due today!**"
                        elif days_until <= 3:
                            deadline_text = f" ⚡ **Due in {days_until} days**"
                        else:
                            deadline_text = f" 📅 Due in {days_until} days"
                
                response_parts.append(
                    f"{category_emoji} **{link.title}**\n"
                    f"🔗 {link.url}\n"
                    f"📂 Category: {link.category.value.replace('_', ' ').title()}\n"
                    f"🆔 ID: `{link.id[:8]}`{deadline_text}\n"
                )
        
        if updated_links:
            response_parts.append("🔄 **Existing links updated!**\n")
            for link in updated_links:
                category_emoji = {
                    LinkCategory.JOB_APPLICATION: "💼",
                    LinkCategory.GRANT_APPLICATION: "💰",
                    LinkCategory.NOTES_TO_READ: "📖",
                    LinkCategory.RESEARCH: "🔬",
                    LinkCategory.LEARNING: "🎓",
                    LinkCategory.PERSONAL: "👤",
                    LinkCategory.OTHER: "🔗"
                }.get(link.category, "🔗")
                
                deadline_text = ""
                if link.deadline:
                    days_until = link.days_until_deadline()
                    if days_until is not None:
                        if days_until < 0:
                            deadline_text = f" ⚠️ **OVERDUE** ({abs(days_until)} days ago)"
                        elif days_until == 0:
                            deadline_text = " ⏰ **Due today!**"
                        elif days_until <= 3:
                            deadline_text = f" ⚡ **Due in {days_until} days**"
                        else:
                            deadline_text = f" 📅 Due in {days_until} days"
                
                response_parts.append(
                    f"{category_emoji} **{link.title}**\n"
                    f"🔗 {link.url}\n"
                    f"📂 Category: {link.category.value.replace('_', ' ').title()}\n"
                    f"🆔 ID: `{link.id[:8]}`{deadline_text}\n"
                )
        
        if response_parts:
            response = "\n".join(response_parts)
        else:
            response = "❌ Failed to process links. Please try again."
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    def _handle_status_update(self, state: AgentState) -> AgentState:
        """Handle status update commands."""
        user_id = state["user_id"]
        storage = state["storage"]
        status_update = state["context"]["status_update"]
        
        if status_update:
            link_id, new_status = status_update
            
            # Try to find the link by ID (first 8 characters)
            user_links = storage.get_user_links(user_id)
            target_link = None
            
            for link in user_links:
                if link.id.startswith(link_id):
                    target_link = link
                    break
            
            if target_link and storage.update_link_status(user_id, target_link.id, new_status):
                status_emoji = {
                    TaskStatus.TODO: "📋",
                    TaskStatus.IN_PROGRESS: "🔄",
                    TaskStatus.DONE: "✅",
                    TaskStatus.EXPIRED: "⏰"
                }.get(new_status, "📋")
                
                response = (
                    f"{status_emoji} **Status updated!**\n"
                    f"**{target_link.title}** is now marked as **{new_status.value.replace('_', ' ').title()}**"
                )
            else:
                response = f"❌ Could not find link with ID `{link_id}` or failed to update status."
        else:
            response = "❌ Invalid status update command. Use format: 'done <link_id>' or 'mark <link_id> as done'"
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate a conversational response using the LLM."""
        messages = state["messages"]
        
        # Create a prompt template for conversational responses
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful and friendly AI assistant integrated with Telegram. 
            Provide helpful, accurate, and engaging responses to user queries. 
            Keep responses concise but informative, and maintain a conversational tone."""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        # Generate response
        chain = prompt | self.llm
        response = chain.invoke({"messages": messages})
        
        # Add the response to the conversation
        state["messages"].append(response)
        return state
    
    def _handle_special_request(self, state: AgentState) -> AgentState:
        """Handle special requests like help, info, etc."""
        messages = state["messages"]
        last_message = messages[-1].content.lower() if messages else ""
        user_id = state["user_id"]
        storage = state["storage"]
        
        if "help" in last_message or "commands" in last_message:
            help_text = """🤖 **Link Organizer Bot - Available Commands:**

**📋 Link Management:**
• Send any URL to automatically categorize and save it
• Add context like: "Job application at Google due 12/31/2024"
• Use: "done <link_id>" to mark as complete
• Use: "mark <link_id> as in_progress/paused/waiting" to update status

**📊 View Your Links:**
• "list all" - Show all active links (excludes overdue)
• "list jobs" - Show active job applications
• "list grants" - Show active grant applications
• "list overdue" - Show overdue items
• "list deadlines [days]" - Show upcoming deadlines (e.g., "list deadlines 30")
• "list reminders" - Show links with active reminders

**🎯 Progress & Milestones:**
• "add milestone <link_id> <title>" - Add milestone to task
• "complete milestone <milestone_id>" - Mark milestone as done
• "list milestones <link_id>" - Show task milestones
• "progress all" - Show overall progress summary
• "progress <link_id>" - Show progress for specific task

**🔔 Reminders:**
• "remind me about <link_id>" - Get immediate reminder
• Automatic reminders for overdue, due today, tomorrow, 3 days, 1 week
• Daily summaries (9 AM) and weekly summaries (Monday 9 AM)

**🎨 Visualization:**
• "visualize" or "graph" - Generate LangGraph workflow diagrams

**⚙️ Other Commands:**
• /start - Start the conversation
• /help - Show this help message
• /info - Get information about the bot

**💡 Examples:**
• "https://example.com/job - Software Engineer position due next Friday"
• "done abc12345" (use first 8 chars of link ID)
• "add milestone abc12345 Submit resume"
• "progress all" to see your overall progress"""
            
            state["messages"].append(AIMessage(content=help_text))
        
        elif "info" in last_message or "about" in last_message:
            info_text = """ℹ️ **About This Link Organizer Bot:**
            
I'm your personal link organizer powered by LangGraph and OpenAI! I can:

🔗 **Automatically categorize links** into:
• 💼 Job Applications
• 💰 Grant Applications  
• 📖 Notes to Read
• 🔬 Research
• 🎓 Learning
• 👤 Personal

⏰ **Track deadlines** and remind you of upcoming due dates
📊 **Manage task status** (TODO, In Progress, Done)
🎯 **Organize your workflow** and keep you on track

Just send me any URL and I'll help you organize it!"""
            
            state["messages"].append(AIMessage(content=info_text))
        
        elif "start" in last_message:
            welcome_text = """👋 **Welcome to Your Link Organizer!**
            
I'm here to help you organize your links, track deadlines, and manage your tasks!

**How to use me:**
1. Send me any URL to save and categorize it
2. Add context like deadlines: "Job app due 12/31/2024"
3. Use commands like "list all" to see your saved links
4. Mark items as done with "done <link_id>"

**Example:** Send me a job posting URL with "due next Friday" and I'll categorize it and set a reminder!

Type "help" to see all available commands."""
            
            state["messages"].append(AIMessage(content=welcome_text))
        
        elif "list" in last_message:
            # Handle list commands
            response = self._handle_list_command(last_message, user_id, storage)
            state["messages"].append(AIMessage(content=response))
        
        elif "visualize" in last_message or "graph" in last_message or "plot" in last_message:
            # Handle visualization requests
            response = self._handle_visualization_request()
            state["messages"].append(AIMessage(content=response))
        
        elif "milestone" in last_message:
            # Handle milestone commands
            response = self._handle_milestone_command(last_message, user_id, storage)
            state["messages"].append(AIMessage(content=response))
        
        elif "progress" in last_message:
            # Handle progress commands
            response = self._handle_progress_command(last_message, user_id, storage)
            state["messages"].append(AIMessage(content=response))
        
        elif "remind" in last_message:
            # Handle reminder commands
            response = self._handle_reminder_command(last_message, user_id, storage)
            state["messages"].append(AIMessage(content=response))
        
        else:
            # Default response for other special requests
            state["messages"].append(AIMessage(content="I'm here to help! Send me a URL to organize it, or type 'help' to see all commands."))
        
        return state
    
    def _handle_list_command(self, command: str, user_id: str, storage: FileStorage) -> str:
        """Handle list commands to show user's links."""
        command_lower = command.lower()
        user_links = storage.get_user_links(user_id)
        
        if not user_links:
            return "📭 You don't have any saved links yet. Send me a URL to get started!"
        
        if "all" in command_lower:
            # Filter out overdue items from "all" list
            active_links = [link for link in user_links if not link.is_overdue()]
            return self._format_links_list(active_links, "All Active Links")
        
        elif "job" in command_lower:
            job_links = [link for link in user_links if link.category == LinkCategory.JOB_APPLICATION and not link.is_overdue()]
            return self._format_links_list(job_links, "Active Job Applications")
        
        elif "grant" in command_lower:
            grant_links = [link for link in user_links if link.category == LinkCategory.GRANT_APPLICATION and not link.is_overdue()]
            return self._format_links_list(grant_links, "Active Grant Applications")
        
        elif "overdue" in command_lower:
            overdue_links = storage.get_overdue_links(user_id)
            return self._format_links_list(overdue_links, "Overdue Items")
        
        elif "deadline" in command_lower:
            # Parse optional day parameter: "list deadlines 30" or "list deadlines"
            days = 7  # default
            parts = command_lower.split()
            if len(parts) >= 3 and parts[2].isdigit():
                days = int(parts[2])
                days = min(days, 365)  # Cap at 1 year
            
            upcoming_links = storage.get_upcoming_deadlines(user_id, days)
            return self._format_links_list(upcoming_links, f"Upcoming Deadlines (Next {days} Days)")
        
        elif "reminder" in command_lower:
            reminder_links = self._get_links_with_reminders(user_id, storage)
            return self._format_links_list(reminder_links, "Active Reminders")
        
        else:
            return "📋 **Available list commands:**\n• list all\n• list jobs\n• list grants\n• list overdue\n• list deadlines [days] (e.g., 'list deadlines 30')\n• list reminders"
    
    def _format_links_list(self, links: List[LinkItem], title: str) -> str:
        """Format a list of links for display."""
        if not links:
            return f"📭 No {title.lower()} found."
        
        response_parts = [f"📋 **{title}** ({len(links)} items):\n"]
        
        for i, link in enumerate(links, 1):
            status_emoji = {
                TaskStatus.TODO: "📋",
                TaskStatus.IN_PROGRESS: "🔄", 
                TaskStatus.DONE: "✅",
                TaskStatus.EXPIRED: "⏰"
            }.get(link.status, "📋")
            
            category_emoji = {
                LinkCategory.JOB_APPLICATION: "💼",
                LinkCategory.GRANT_APPLICATION: "💰",
                LinkCategory.NOTES_TO_READ: "📖",
                LinkCategory.RESEARCH: "🔬",
                LinkCategory.LEARNING: "🎓",
                LinkCategory.PERSONAL: "👤",
                LinkCategory.OTHER: "🔗"
            }.get(link.category, "🔗")
            
            deadline_text = ""
            if link.deadline:
                days_until = link.days_until_deadline()
                if days_until is not None:
                    if days_until < 0:
                        deadline_text = f" ⚠️ **OVERDUE** ({abs(days_until)} days ago)"
                    elif days_until == 0:
                        deadline_text = " ⏰ **Due today!**"
                    elif days_until <= 3:
                        deadline_text = f" ⚡ **Due in {days_until} days**"
                    else:
                        deadline_text = f" 📅 Due in {days_until} days"
            
            response_parts.append(
                f"{i}. {status_emoji}{category_emoji} **{link.title}**\n"
                f"   🔗 {link.url}\n"
                f"   🆔 ID: `{link.id[:8]}` | Status: {link.status.value.replace('_', ' ').title()}{deadline_text}\n"
            )
        
        return "\n".join(response_parts)
    
    def _get_links_with_reminders(self, user_id: str, storage: FileStorage) -> List[LinkItem]:
        """Get links that have active reminders (have deadlines and are not done/expired)."""
        user_links = storage.get_user_links(user_id)
        reminder_links = []
        
        for link in user_links:
            if (link.deadline and 
                link.status not in [TaskStatus.DONE, TaskStatus.EXPIRED] and
                not link.is_overdue()):  # Exclude overdue items
                reminder_links.append(link)
        
        # Sort by deadline (closest first)
        reminder_links.sort(key=lambda x: x.deadline if x.deadline else datetime.max)
        return reminder_links
    
    def _handle_visualization_request(self) -> str:
        """Handle requests to visualize the LangGraph workflow."""
        try:
            # Generate both types of visualizations
            workflow_path = self.visualizer.create_workflow_diagram("workflow_diagram.png")
            network_path = self.visualizer.visualize_langgraph_workflow(self.graph, "langgraph_workflow.png")
            
            response = f"""🎨 **LangGraph Workflow Visualization Generated!**

I've created two visualizations of my workflow:

📊 **Workflow Diagram**: `{workflow_path}`
   • Shows the decision tree and flow
   • Includes descriptions of each node
   • Easy to understand the bot's logic

🔄 **Network Graph**: `{network_path}`
   • Interactive network visualization
   • Shows all nodes and connections
   • Color-coded by node type

**Node Types:**
🟢 **Entry Point**: Where the workflow starts
🟠 **Decision Node**: Routes messages to appropriate handlers
🔵 **Processing Node**: Handles specific types of requests
🔴 **End Point**: Where responses are sent

**Workflow Flow:**
1. Message received → analyze_input (decision)
2. analyze_input routes to:
   • process_links (URLs detected)
   • handle_status_update (status commands)
   • generate_response (general chat)
   • handle_special_request (special commands)
3. All paths → END (send response)

The images have been saved to your project directory!"""
            
            return response
            
        except Exception as e:
            return f"❌ Error generating visualization: {e}"
    
    def _handle_milestone_command(self, command: str, user_id: str, storage: FileStorage) -> str:
        """Handle milestone-related commands."""
        command_lower = command.lower()
        
        # Parse different milestone commands
        if "add milestone" in command_lower:
            return self._add_milestone(command, user_id, storage)
        elif "complete milestone" in command_lower or "done milestone" in command_lower:
            return self._complete_milestone(command, user_id, storage)
        elif "list milestone" in command_lower or "show milestone" in command_lower:
            return self._list_milestones(command, user_id, storage)
        else:
            return """📋 **Milestone Commands:**
• `add milestone <link_id> <title>` - Add a milestone to a task
• `complete milestone <milestone_id>` - Mark milestone as done
• `list milestones <link_id>` - Show milestones for a task

**Example:** `add milestone abc12345 Submit application`"""
    
    def _add_milestone(self, command: str, user_id: str, storage: FileStorage) -> str:
        """Add a milestone to a link."""
        try:
            # Parse: "add milestone <link_id> <title>"
            parts = command.split(" ", 3)
            if len(parts) < 4:
                return "❌ Usage: `add milestone <link_id> <title>`"
            
            link_id = parts[2]
            title = parts[3]
            
            user_links = storage.get_user_links(user_id)
            target_link = None
            
            for link in user_links:
                if link.id.startswith(link_id):
                    target_link = link
                    break
            
            if not target_link:
                return f"❌ Could not find link with ID `{link_id}`"
            
            milestone = target_link.add_milestone(title)
            
            # Save the updated link
            user_data = storage.load_user_data(user_id)
            storage.save_user_data(user_data)
            
            return f"""✅ **Milestone Added!**
📋 **{milestone.title}**
Added to: **{target_link.title}**
🆔 Milestone ID: `{milestone.id[:8]}`

Use `complete milestone {milestone.id[:8]}` to mark as done."""
            
        except Exception as e:
            return f"❌ Error adding milestone: {e}"
    
    def _complete_milestone(self, command: str, user_id: str, storage: FileStorage) -> str:
        """Complete a milestone."""
        try:
            # Parse: "complete milestone <milestone_id>"
            parts = command.split()
            if len(parts) < 3:
                return "❌ Usage: `complete milestone <milestone_id>`"
            
            milestone_id = parts[2]
            
            user_links = storage.get_user_links(user_id)
            
            for link in user_links:
                if link.complete_milestone(milestone_id):
                    # Save the updated data
                    user_data = storage.load_user_data(user_id)
                    storage.save_user_data(user_data)
                    
                    return f"""✅ **Milestone Completed!**
Task: **{link.title}**
📊 {link.get_progress_summary()}

{"🎉 Task completed!" if link.progress_percentage == 100 else "Keep up the great work!"}"""
            
            return f"❌ Could not find milestone with ID `{milestone_id}`"
            
        except Exception as e:
            return f"❌ Error completing milestone: {e}"
    
    def _list_milestones(self, command: str, user_id: str, storage: FileStorage) -> str:
        """List milestones for a link."""
        try:
            # Parse: "list milestones <link_id>"
            parts = command.split()
            if len(parts) < 3:
                return "❌ Usage: `list milestones <link_id>`"
            
            link_id = parts[2]
            
            user_links = storage.get_user_links(user_id)
            target_link = None
            
            for link in user_links:
                if link.id.startswith(link_id):
                    target_link = link
                    break
            
            if not target_link:
                return f"❌ Could not find link with ID `{link_id}`"
            
            if not target_link.milestones:
                return f"📭 No milestones found for **{target_link.title}**\n\nUse `add milestone {link_id} <title>` to add one."
            
            response_parts = [f"📋 **Milestones for {target_link.title}**\n"]
            response_parts.append(f"📊 {target_link.get_progress_summary()}\n")
            
            for i, milestone in enumerate(target_link.milestones, 1):
                status = "✅" if milestone.completed else "⭕"
                completed_text = f" (completed {milestone.completed_at.strftime('%m/%d')})" if milestone.completed else ""
                
                response_parts.append(
                    f"{i}. {status} **{milestone.title}**{completed_text}\n"
                    f"   🆔 ID: `{milestone.id[:8]}`"
                )
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error listing milestones: {e}"
    
    def _handle_progress_command(self, command: str, user_id: str, storage: FileStorage) -> str:
        """Handle progress-related commands."""
        command_lower = command.lower()
        
        if "progress" in command_lower and any(word in command_lower for word in ["all", "summary", "overview"]):
            return self._show_progress_summary(user_id, storage)
        elif "progress" in command_lower:
            # Show progress for specific link
            parts = command.split()
            if len(parts) >= 2:
                link_id = parts[1]
                return self._show_link_progress(link_id, user_id, storage)
        
        return """📊 **Progress Commands:**
• `progress all` - Show overall progress summary
• `progress <link_id>` - Show progress for specific task

**Example:** `progress abc12345`"""
    
    def _show_progress_summary(self, user_id: str, storage: FileStorage) -> str:
        """Show overall progress summary."""
        user_links = storage.get_user_links(user_id)
        
        if not user_links:
            return "📭 No tasks found. Add some links to get started!"
        
        # Calculate overall stats
        total_tasks = len(user_links)
        completed_tasks = len([l for l in user_links if l.status == TaskStatus.DONE])
        in_progress_tasks = len([l for l in user_links if l.status == TaskStatus.IN_PROGRESS])
        
        # Calculate milestone stats
        total_milestones = sum(len(l.milestones) for l in user_links)
        completed_milestones = sum(len([m for m in l.milestones if m.completed]) for l in user_links)
        
        response_parts = ["📊 **Your Progress Summary**\n"]
        
        # Task completion rate
        completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        response_parts.append(f"🎯 **Tasks:** {completed_tasks}/{total_tasks} completed ({completion_rate}%)")
        
        if in_progress_tasks > 0:
            response_parts.append(f"🔄 **In Progress:** {in_progress_tasks} tasks")
        
        # Milestone completion rate
        if total_milestones > 0:
            milestone_rate = int((completed_milestones / total_milestones) * 100)
            response_parts.append(f"📋 **Milestones:** {completed_milestones}/{total_milestones} completed ({milestone_rate}%)")
        
        # Show top priority tasks
        high_priority = [l for l in user_links if l.priority >= 4 and l.status != TaskStatus.DONE]
        if high_priority:
            response_parts.append(f"\n⚡ **High Priority Tasks:** {len(high_priority)}")
            for link in high_priority[:3]:  # Show top 3
                days_until = link.days_until_deadline()
                deadline_text = f" (due in {days_until} days)" if days_until and days_until > 0 else ""
                response_parts.append(f"   • {link.title}{deadline_text}")
        
        return "\n".join(response_parts)
    
    def _show_link_progress(self, link_id: str, user_id: str, storage: FileStorage) -> str:
        """Show progress for a specific link."""
        user_links = storage.get_user_links(user_id)
        target_link = None
        
        for link in user_links:
            if link.id.startswith(link_id):
                target_link = link
                break
        
        if not target_link:
            return f"❌ Could not find link with ID `{link_id}`"
        
        response_parts = [f"📊 **Progress for {target_link.title}**\n"]
        
        # Basic info
        status_emoji = {
            TaskStatus.TODO: "📋",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.DONE: "✅",
            TaskStatus.EXPIRED: "⏰",
            TaskStatus.PAUSED: "⏸️",
            TaskStatus.WAITING: "⏳"
        }.get(target_link.status, "📋")
        
        response_parts.append(f"{status_emoji} **Status:** {target_link.status.value.replace('_', ' ').title()}")
        response_parts.append(f"📊 **{target_link.get_progress_summary()}**")
        
        # Deadline info
        if target_link.deadline:
            days_until = target_link.days_until_deadline()
            if days_until is not None:
                if days_until < 0:
                    response_parts.append(f"⚠️ **OVERDUE** by {abs(days_until)} days")
                elif days_until == 0:
                    response_parts.append("⏰ **Due today!**")
                else:
                    response_parts.append(f"📅 **Due in {days_until} days**")
        
        # Recent activity
        if target_link.last_activity:
            days_since = (datetime.now() - target_link.last_activity).days
            if days_since == 0:
                response_parts.append("🔥 **Active today**")
            elif days_since == 1:
                response_parts.append("📅 **Last activity: yesterday**")
            else:
                response_parts.append(f"📅 **Last activity: {days_since} days ago**")
        
        # Milestones summary
        if target_link.milestones:
            completed = len([m for m in target_link.milestones if m.completed])
            total = len(target_link.milestones)
            response_parts.append(f"\n📋 **Milestones:** {completed}/{total} completed")
            
            # Show next milestone
            next_milestone = next((m for m in target_link.milestones if not m.completed), None)
            if next_milestone:
                response_parts.append(f"🎯 **Next:** {next_milestone.title}")
        
        return "\n".join(response_parts)
    
    def _handle_reminder_command(self, command: str, user_id: str, storage: FileStorage) -> str:
        """Handle reminder-related commands."""
        command_lower = command.lower()
        
        if "remind me" in command_lower or "remind" in command_lower:
            # Parse: "remind me about <link_id>"
            parts = command.split()
            if len(parts) >= 3:
                link_id = parts[-1]  # Get the last part as link_id
                
                # Try to send immediate reminder
                if hasattr(self, 'reminder_system'):
                    success = self.reminder_system.send_immediate_reminder(user_id, link_id)
                    if success:
                        return "🔔 **Reminder sent!** Check above for details."
                    else:
                        return f"❌ Could not find link with ID `{link_id}`"
                else:
                    # Fallback: show link details
                    user_links = storage.get_user_links(user_id)
                    for link in user_links:
                        if link.id.startswith(link_id):
                            days_until = link.days_until_deadline()
                            deadline_text = f"Due in {days_until} days" if days_until and days_until > 0 else "No deadline"
                            return f"🔔 **Reminder:** {link.title}\n📅 {deadline_text}\n🔗 {link.url}"
                    return f"❌ Could not find link with ID `{link_id}`"
        
        return """🔔 **Reminder Commands:**
• `remind me about <link_id>` - Get immediate reminder
• Automatic reminders are sent for:
  - Overdue items (every 4 hours)
  - Items due today (morning)
  - Items due tomorrow (evening)
  - Items due in 3 days
  - Items due in 1 week
  - Daily summaries (9 AM)
  - Weekly summaries (Monday 9 AM)

**Example:** `remind me about abc12345`"""
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a user message and return the response."""
        # Initialize state
        state = AgentState(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            current_step="",
            context={},
            links=[],
            storage=self.storage
        )
        
        # Run the graph
        result = self.graph.invoke(state)
        
        # Return the last AI message
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        if ai_messages:
            return ai_messages[-1].content
        else:
            return "I'm sorry, I couldn't generate a response. Please try again."
    
    def get_conversation_history(self, user_id: str) -> List[BaseMessage]:
        """Get conversation history for a user (placeholder for future implementation)."""
        # In a real implementation, you'd store this in a database
        return []
