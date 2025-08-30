from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    user_id: Annotated[str, "The Telegram user ID"]
    current_step: Annotated[str, "Current step in the workflow"]
    context: Annotated[Dict[str, Any], "Additional context for the conversation"]

class LangGraphAgent:
    """A LangGraph-based conversational agent for Telegram."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_special_request", self._handle_special_request)
        
        # Set entry point
        workflow.set_entry_point("analyze_input")
        
        # Add conditional routing from analyze_input
        workflow.add_conditional_edges(
            "analyze_input",
            self._route_request,
            {
                "general": "generate_response",
                "special": "handle_special_request"
            }
        )
        
        # Add edges to END
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_special_request", END)
        
        return workflow.compile()
    
    def _analyze_input(self, state: AgentState) -> AgentState:
        """Analyze the user input to determine the type of request."""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Simple keyword-based analysis (you can make this more sophisticated)
        special_keywords = ["help", "info", "about", "commands", "start", "stop"]
        is_special = any(keyword in last_message.lower() for keyword in special_keywords)
        
        state["current_step"] = "special" if is_special else "general"
        return state
    
    def _route_request(self, state: AgentState) -> str:
        """Route the request based on analysis."""
        return state["current_step"]
    
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
        
        if "help" in last_message or "commands" in last_message:
            help_text = """🤖 **Available Commands:**
            
/start - Start the conversation
/help - Show this help message
/info - Get information about the bot
/stop - End the conversation

You can also just chat with me normally! I'm here to help with any questions you might have."""
            
            state["messages"].append(AIMessage(content=help_text))
        
        elif "info" in last_message or "about" in last_message:
            info_text = """ℹ️ **About This Bot:**
            
I'm an AI assistant powered by LangGraph and OpenAI. I can help you with:
• General questions and conversations
• Information and explanations
• Creative writing and brainstorming
• And much more!

Feel free to ask me anything!"""
            
            state["messages"].append(AIMessage(content=info_text))
        
        elif "start" in last_message:
            welcome_text = """👋 **Welcome!**
            
Hello! I'm your AI assistant. I'm here to help you with any questions or tasks you might have. 
Just send me a message and I'll do my best to assist you!

Type /help to see available commands."""
            
            state["messages"].append(AIMessage(content=welcome_text))
        
        else:
            # Default response for other special requests
            state["messages"].append(AIMessage(content="I'm here to help! What would you like to know?"))
        
        return state
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a user message and return the response."""
        # Initialize state
        state = AgentState(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            current_step="",
            context={}
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
