from langgraph.graph import StateGraph, END
from venturalitica.assurance.graph.state import ComplianceState
from venturalitica.assurance.graph.nodes import NodeFactory

def create_compliance_graph(model_name: str = "mistral", provider: str = "auto", api_key: str = None):
    """
    Builds the Compliance-RAG graph.
    """
    # Initialize Nodes
    nodes = NodeFactory(model_name, provider, api_key)
    
    # Define Graph
    workflow = StateGraph(ComplianceState)
    
    # Add Nodes
    workflow.add_node("scanner", nodes.scan_project)
    workflow.add_node("planner", nodes.plan_sections)
    workflow.add_node("writer_2a", nodes.write_section_2a)
    workflow.add_node("writer_2b", nodes.write_section_2b)
    workflow.add_node("writer_2c", nodes.write_section_2c)
    workflow.add_node("writer_2d", nodes.write_section_2d)
    workflow.add_node("writer_2e", nodes.write_section_2e)
    workflow.add_node("writer_2f", nodes.write_section_2f)
    workflow.add_node("writer_2g", nodes.write_section_2g)
    workflow.add_node("writer_2h", nodes.write_section_2h)
    workflow.add_node("compiler", nodes.compile_document)
    workflow.add_node("critic", nodes.critique_document)
    workflow.add_node("translator", nodes.translate_document)
    
    # Define Edges
    workflow.set_entry_point("scanner")
    workflow.add_edge("scanner", "planner")
    
    # Fan-out to parallel writers
    writers = ["writer_2a", "writer_2b", "writer_2c", "writer_2d", "writer_2e", "writer_2f", "writer_2g", "writer_2h"]
    for w in writers:
        workflow.add_edge("planner", w)
        workflow.add_edge(w, "compiler")
    
    # Critic Loop
    workflow.add_edge("compiler", "critic")
    
    # Wait, simple rerouting to planner works, but planner resets state?
    # No, planner returns {"sections": {}, ...}.
    # If we route back to planner, it might reset sections.
    # We should route back to writers. But LangGraph needs explicit edges.
    # Router logic:
    def route_feedback(state: ComplianceState):
        if state.get("critic_verdict") == "APPROVE":
            # BYPASS TRANSLATOR if we generated natively in Spanish
            # We assume if the target language is Spanish and we loaded Spanish prompts, 
            # the compiler already has the final document in Spanish.
            lang = state.get("language", "English").lower()
            # If language is Spanish, we skip translator because sections were drafted in ES
            if lang.startswith("es") or lang == "spanish":
                print("  ⏭️  Bypassing translator (Native Spanish execution)...")
                return END
            return "translator"
        return writers
        
    workflow.add_conditional_edges(
        "critic",
        route_feedback,
        path_map={END: END, "translator": "translator", **{w: w for w in writers}} 
    )

    workflow.add_edge("translator", END)
    
    return workflow.compile()
