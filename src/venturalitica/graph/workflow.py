from langgraph.graph import StateGraph, END
from venturalitica.graph.state import ComplianceState
from venturalitica.graph.nodes import NodeFactory

def create_compliance_graph(model_name: str = "mistral"):
    """
    Builds the Compliance-RAG graph.
    """
    # Initialize Nodes
    nodes = NodeFactory(model_name)
    
    # Define Graph
    workflow = StateGraph(ComplianceState)
    
    # Add Nodes
    workflow.add_node("scanner", nodes.scan_project)
    workflow.add_node("planner", nodes.plan_sections)
    workflow.add_node("writer_2a", nodes.write_section_2a) # Development Methods
    workflow.add_node("writer_2b", nodes.write_section_2b) # Logic & Assumptions
    workflow.add_node("writer_2c", nodes.write_section_2c) # Architecture
    workflow.add_node("writer_2g", nodes.write_section_2g) # Validation (from vl.enforce)
    workflow.add_node("compiler", nodes.compile_document)
    
    # Define Edges
    workflow.set_entry_point("scanner")
    workflow.add_edge("scanner", "planner")
    
    # Fan-out to parallel writers
    workflow.add_edge("planner", "writer_2a")
    workflow.add_edge("planner", "writer_2b")
    workflow.add_edge("planner", "writer_2c")
    workflow.add_edge("planner", "writer_2g")
    
    # Fan-in to compiler
    workflow.add_edge("writer_2a", "compiler")
    workflow.add_edge("writer_2b", "compiler")
    workflow.add_edge("writer_2c", "compiler")
    workflow.add_edge("writer_2g", "compiler")
    
    workflow.add_edge("compiler", END)
    
    return workflow.compile()
