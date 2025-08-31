#!/usr/bin/env python3
"""
Script to visualize the LangGraph workflow.
"""

import os
import sys
from bot.graph_visualizer import GraphVisualizer

def create_mock_graph():
    """Create a mock graph structure for visualization without requiring OpenAI."""
    from langgraph.graph import StateGraph, END
    from typing import Dict, Any, List, TypedDict, Annotated
    
    # Define the state structure
    class AgentState(TypedDict):
        messages: Annotated[List, "The messages in the conversation"]
        user_id: Annotated[str, "The Telegram user ID"]
        current_step: Annotated[str, "Current step in the workflow"]
        context: Annotated[Dict[str, Any], "Additional context for the conversation"]
        links: Annotated[List, "Links extracted from the message"]
        storage: Annotated[Any, "Storage instance for user data"]
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes (mock functions)
    def mock_analyze_input(state):
        return state
    
    def mock_process_links(state):
        return state
    
    def mock_handle_status_update(state):
        return state
    
    def mock_generate_response(state):
        return state
    
    def mock_handle_special_request(state):
        return state
    
    def mock_route_request(state):
        return "general"
    
    workflow.add_node("analyze_input", mock_analyze_input)
    workflow.add_node("process_links", mock_process_links)
    workflow.add_node("handle_status_update", mock_handle_status_update)
    workflow.add_node("generate_response", mock_generate_response)
    workflow.add_node("handle_special_request", mock_handle_special_request)
    
    # Set entry point
    workflow.set_entry_point("analyze_input")
    
    # Add conditional routing from analyze_input
    workflow.add_conditional_edges(
        "analyze_input",
        mock_route_request,
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

def main():
    """Generate and display the LangGraph workflow visualization."""
    
    print("🎨 Generating LangGraph workflow visualization...")
    
    try:
        # Create a mock graph for visualization
        graph = create_mock_graph()
        
        # Create the visualizer
        visualizer = GraphVisualizer()
        
        # Generate both types of visualizations
        print("📊 Creating workflow diagram...")
        workflow_path = visualizer.create_workflow_diagram("workflow_diagram.png")
        
        print("🔄 Creating network graph...")
        network_path = visualizer.visualize_langgraph_workflow(graph, "langgraph_workflow.png")
        
        print("\n✅ Visualization complete!")
        print(f"📁 Workflow diagram: {workflow_path}")
        print(f"📁 Network graph: {network_path}")
        
        # Try to open the images if possible
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", workflow_path])
                subprocess.run(["open", network_path])
            elif system == "Windows":
                subprocess.run(["start", workflow_path], shell=True)
                subprocess.run(["start", network_path], shell=True)
            elif system == "Linux":
                subprocess.run(["xdg-open", workflow_path])
                subprocess.run(["xdg-open", network_path])
                
            print("🖼️  Images opened in your default viewer!")
            
        except Exception as e:
            print(f"⚠️  Could not open images automatically: {e}")
            print("📂 Please open the PNG files manually to view the visualizations.")
        
        # Print graph information
        print("\n📋 Graph Information:")
        print(f"   Nodes: {list(graph.nodes)}")
        print(f"   Entry point: analyze_input")
        print(f"   End points: END")
        
        print("\n🔄 Workflow Flow:")
        print("   1. START → analyze_input (decision node)")
        print("   2. analyze_input → process_links (if URLs detected)")
        print("   3. analyze_input → handle_status_update (if status command)")
        print("   4. analyze_input → generate_response (if general chat)")
        print("   5. analyze_input → handle_special_request (if special commands)")
        print("   6. All paths → END")
        
    except Exception as e:
        print(f"❌ Error generating visualization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
