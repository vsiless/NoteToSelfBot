import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict, Any, List
import os

class GraphVisualizer:
    """Visualize LangGraph workflows."""
    
    def __init__(self):
        self.colors = {
            'entry': '#4CAF50',      # Green for entry point
            'process': '#2196F3',    # Blue for processing nodes
            'decision': '#FF9800',   # Orange for decision nodes
            'end': '#F44336',        # Red for end nodes
            'special': '#9C27B0'     # Purple for special handling
        }
    
    def visualize_langgraph_workflow(self, graph, save_path: str = "langgraph_workflow.png"):
        """Create a visual representation of the LangGraph workflow."""
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes with their types
        node_types = {}
        
        # Entry point
        G.add_node("START", node_type="entry")
        node_types["START"] = "entry"
        
        # Add all nodes from the graph
        for node_name in graph.nodes:
            if node_name == "analyze_input":
                node_type = "decision"
            elif node_name in ["process_links", "handle_status_update", "generate_response", "handle_special_request"]:
                node_type = "process"
            else:
                node_type = "process"
            
            G.add_node(node_name, node_type=node_type)
            node_types[node_name] = node_type
        
        # Add END node
        G.add_node("END", node_type="end")
        node_types["END"] = "end"
        
        # Add edges based on the workflow
        edges = [
            ("START", "analyze_input"),
            ("analyze_input", "process_links"),
            ("analyze_input", "handle_status_update"),
            ("analyze_input", "generate_response"),
            ("analyze_input", "handle_special_request"),
            ("process_links", "END"),
            ("handle_status_update", "END"),
            ("generate_response", "END"),
            ("handle_special_request", "END")
        ]
        
        for edge in edges:
            G.add_edge(edge[0], edge[1])
        
        # Create the visualization with transparent background
        fig = plt.figure(figsize=(12, 8))
        fig.patch.set_alpha(0.0)  # Make figure background transparent
        ax = plt.gca()
        ax.set_facecolor('none')  # Make axis background transparent
        
        # Position nodes using spring layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw nodes with different colors based on type
        for node_type in set(node_types.values()):
            node_list = [node for node, ntype in node_types.items() if ntype == node_type]
            nx.draw_networkx_nodes(G, pos, 
                                 nodelist=node_list,
                                 node_color=self.colors[node_type],
                                 node_size=3000,  # Increased node size
                                 alpha=0.9,
                                 edgecolors='black',
                                 linewidths=2)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, 
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              arrowstyle='->',
                              width=2)
        
        # Add labels with black text for better readability
        nx.draw_networkx_labels(G, pos, 
                               font_size=9,
                               font_weight='bold',
                               font_color='black')  # Changed to black
        
        # Add edge labels for conditional routing
        edge_labels = {
            ("analyze_input", "process_links"): "links",
            ("analyze_input", "handle_status_update"): "status_update",
            ("analyze_input", "generate_response"): "general",
            ("analyze_input", "handle_special_request"): "special"
        }
        
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=9, font_color='darkblue')
        
        # Add title and legend
        plt.title("LangGraph Link Organizer Workflow", fontsize=16, fontweight='bold', pad=20)
        
        # Create legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors['entry'], 
                      markersize=15, label='Entry Point'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors['decision'], 
                      markersize=15, label='Decision Node'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors['process'], 
                      markersize=15, label='Processing Node'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors['end'], 
                      markersize=15, label='End Point')
        ]
        
        legend = plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
        legend.get_frame().set_alpha(0.0)  # Make legend background transparent
        
        # Save the plot with transparent background
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='none', edgecolor='none', transparent=True)
        plt.close()
        
        print(f"✅ Graph visualization saved to: {save_path}")
        return save_path
    
    def create_workflow_diagram(self, save_path: str = "workflow_diagram.png"):
        """Create a detailed workflow diagram showing the bot's decision tree."""
        
        # Create a new figure with transparent background
        fig, ax = plt.subplots(figsize=(14, 10))
        fig.patch.set_alpha(0.0)  # Make figure background transparent
        ax.set_facecolor('none')  # Make axis background transparent
        
        # Define node positions manually for better layout
        nodes = {
            'START': (0.5, 0.9),
            'analyze_input': (0.5, 0.75),
            'process_links': (0.2, 0.5),
            'handle_status_update': (0.4, 0.5),
            'generate_response': (0.6, 0.5),
            'handle_special_request': (0.8, 0.5),
            'END': (0.5, 0.1)
        }
        
        # Draw nodes with transparent fill and colored borders
        for node, pos in nodes.items():
            if node == 'START':
                color = self.colors['entry']
                size = (0.15, 0.08)  # (width, height)
            elif node == 'analyze_input':
                color = self.colors['decision']
                size = (0.12, 0.06)
            elif node == 'END':
                color = self.colors['end']
                size = (0.15, 0.08)
            else:
                color = self.colors['process']
                size = (0.10, 0.05)
            
            # Create ellipse with transparent fill and colored border
            from matplotlib.patches import Ellipse
            ellipse = Ellipse(pos, size[0], size[1], 
                            facecolor='none', alpha=1.0, edgecolor=color, linewidth=3)
            ax.add_patch(ellipse)
            
            # Add text with better positioning and black color
            ax.text(pos[0], pos[1], node.replace('_', '\n'), 
                   ha='center', va='center', fontsize=10, fontweight='bold', color='black')
        
        # Draw edges
        edges = [
            ('START', 'analyze_input'),
            ('analyze_input', 'process_links'),
            ('analyze_input', 'handle_status_update'),
            ('analyze_input', 'generate_response'),
            ('analyze_input', 'handle_special_request'),
            ('process_links', 'END'),
            ('handle_status_update', 'END'),
            ('generate_response', 'END'),
            ('handle_special_request', 'END')
        ]
        
        for start, end in edges:
            start_pos = nodes[start]
            end_pos = nodes[end]
            ax.annotate('', xy=end_pos, xytext=start_pos,
                       arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
        
        # Add edge labels
        edge_labels = {
            ('analyze_input', 'process_links'): 'URLs detected',
            ('analyze_input', 'handle_status_update'): 'Status command',
            ('analyze_input', 'generate_response'): 'General chat',
            ('analyze_input', 'handle_special_request'): 'Special commands'
        }
        
        for (start, end), label in edge_labels.items():
            start_pos = nodes[start]
            end_pos = nodes[end]
            mid_x = (start_pos[0] + end_pos[0]) / 2
            mid_y = (start_pos[1] + end_pos[1]) / 2
            ax.text(mid_x, mid_y, label, ha='center', va='center', 
                   fontsize=9, fontweight='bold', color='darkblue',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='darkblue'))
        
        # Add title and description
        ax.set_title("Link Organizer Bot - LangGraph Workflow", fontsize=16, fontweight='bold', pad=20, color='black')
        
        # Add description text
        description = """
        Workflow Description:
        • START: Bot receives message
        • analyze_input: Determines message type and routes accordingly
        • process_links: Extracts URLs, categorizes, and saves to storage
        • handle_status_update: Updates task status (done, in_progress, etc.)
        • generate_response: Handles general conversation using OpenAI
        • handle_special_request: Processes commands (help, list, etc.)
        • END: Sends response back to user
        """
        
        ax.text(0.02, 0.02, description, transform=ax.transAxes, fontsize=9, fontweight='bold',
               verticalalignment='bottom', color='black',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='black'))
        
        # Set axis properties
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Save the diagram with transparent background
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='none', edgecolor='none', transparent=True)
        plt.close()
        
        print(f"✅ Workflow diagram saved to: {save_path}")
        return save_path
