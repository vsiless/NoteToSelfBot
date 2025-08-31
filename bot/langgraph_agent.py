from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .link_processor import LinkProcessor
from .storage import FileStorage
from .models import LinkItem, TaskStatus, LinkCategory
from .graph_visualizer import GraphVisualizer
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
        self.graph = self._build_graph()
    
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
        special_keywords = ["help", "info", "about", "commands", "start", "stop", "list", "show", "deadlines", "overdue"]
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
        for link in links:
            if storage.add_link(user_id, link):
                saved_links.append(link)
        
        # Generate response
        if saved_links:
            response_parts = ["✅ **Links saved successfully!**\n"]
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
            
            response = "\n".join(response_parts)
        else:
            response = "❌ Failed to save links. Please try again."
        
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
• Use: "mark <link_id> as in_progress" to update status

**📊 View Your Links:**
• "list all" - Show all your saved links
• "list jobs" - Show job applications
• "list grants" - Show grant applications
• "list overdue" - Show overdue items
• "list deadlines" - Show upcoming deadlines

**🎨 Visualization:**
• "visualize" or "graph" - Generate LangGraph workflow diagrams

**⚙️ Other Commands:**
• /start - Start the conversation
• /help - Show this help message
• /info - Get information about the bot

**💡 Examples:**
• "https://example.com/job - Software Engineer position"
• "done abc12345" (use first 8 chars of link ID)
• "list all" to see your saved links"""
            
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
            return self._format_links_list(user_links, "All Links")
        
        elif "job" in command_lower:
            job_links = [link for link in user_links if link.category == LinkCategory.JOB_APPLICATION]
            return self._format_links_list(job_links, "Job Applications")
        
        elif "grant" in command_lower:
            grant_links = [link for link in user_links if link.category == LinkCategory.GRANT_APPLICATION]
            return self._format_links_list(grant_links, "Grant Applications")
        
        elif "overdue" in command_lower:
            overdue_links = storage.get_overdue_links(user_id)
            return self._format_links_list(overdue_links, "Overdue Items")
        
        elif "deadline" in command_lower:
            upcoming_links = storage.get_upcoming_deadlines(user_id, 7)
            return self._format_links_list(upcoming_links, "Upcoming Deadlines (Next 7 Days)")
        
        else:
            return "📋 **Available list commands:**\n• list all\n• list jobs\n• list grants\n• list overdue\n• list deadlines"
    
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
