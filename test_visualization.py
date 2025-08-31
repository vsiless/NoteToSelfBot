#!/usr/bin/env python3
"""
Test script for visualization functionality.
"""

import os
import sys

# Mock the OpenAI client to avoid API key requirement
class MockChatOpenAI:
    def __init__(self, model=None, temperature=None):
        pass

# Mock the imports
sys.modules['langchain_openai'] = type('MockModule', (), {
    'ChatOpenAI': MockChatOpenAI
})

def test_visualization():
    """Test the visualization functionality."""
    
    print("🧪 Testing visualization functionality...")
    
    try:
        # Import after mocking
        from bot.graph_visualizer import GraphVisualizer
        
        # Create the visualizer
        visualizer = GraphVisualizer()
        
        # Test creating workflow diagram
        print("📊 Testing workflow diagram creation...")
        workflow_path = visualizer.create_workflow_diagram("test_workflow_diagram.png")
        print(f"✅ Workflow diagram created: {workflow_path}")
        
        # Test creating network graph (with mock graph)
        print("🔄 Testing network graph creation...")
        
        # Create a simple mock graph structure
        from langgraph.graph import StateGraph, END
        
        class MockState:
            pass
        
        workflow = StateGraph(MockState)
        
        def mock_func(state):
            return state
        
        workflow.add_node("analyze_input", mock_func)
        workflow.add_node("process_links", mock_func)
        workflow.add_node("generate_response", mock_func)
        workflow.set_entry_point("analyze_input")
        workflow.add_edge("analyze_input", "process_links")
        workflow.add_edge("process_links", "generate_response")
        workflow.add_edge("generate_response", END)
        
        graph = workflow.compile()
        
        network_path = visualizer.visualize_langgraph_workflow(graph, "test_network_graph.png")
        print(f"✅ Network graph created: {network_path}")
        
        # Check if files exist
        if os.path.exists(workflow_path) and os.path.exists(network_path):
            print("✅ All visualization tests passed!")
            print(f"📁 Files created:")
            print(f"   - {workflow_path}")
            print(f"   - {network_path}")
        else:
            print("❌ Some files were not created")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_visualization()
