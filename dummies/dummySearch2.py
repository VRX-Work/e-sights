from typing import List, Dict, Any, Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import Graph, END
from langchain_core.runnables import RunnablePassthrough
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from semantic_hybrid_search import SemanticHybridSearch

# Define the system state
class SystemState(TypedDict):
    accusations: List[str]
    search_results: Dict[str, Any]
    entity_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    final_report: str

# Initialize components
llm = ChatOpenAI()
semantic_hybrid_search = SemanticHybridSearch(...)  # Initialize with appropriate parameters

# Orchestrator Agent function
def orchestrate(state: SystemState) -> str:
    if not state['search_results']:
        return "start_search"
    elif not state['entity_analysis']:
        return "start_entity_analysis"
    elif not state['risk_assessment']:
        return "start_risk_assessment"
    elif not state['final_report']:
        return "generate_report"
    else:
        return END

# Search Agent functions
def generate_initial_queries(state: SystemState) -> SystemState:
    for accusation in state['accusations']:
        prompt = ChatPromptTemplate.from_template(initial_query_prompt())
        response = llm.invoke(prompt.format(accusation=accusation))
        state['search_results'][accusation] = {'queries': response.content}
    return state

def perform_search(state: SystemState) -> SystemState:
    for accusation, data in state['search_results'].items():
        queries = data['queries']
        elastic_query, semantic_query = parse_queries(queries)
        results = semantic_hybrid_search.hybrid_search(elastic_query, semantic_query)
        state['search_results'][accusation]['results'] = results
    return state

def extract_information(state: SystemState) -> SystemState:
    for accusation, data in state['search_results'].items():
        results = data['results']
        prompt = ChatPromptTemplate.from_template(information_extraction_prompt())
        extracted_info = llm.invoke(prompt.format(accusation=accusation, results=results))
        state['search_results'][accusation]['extracted_info'] = extracted_info.content
    return state

def refine_queries(state: SystemState) -> SystemState:
    for accusation, data in state['search_results'].items():
        extracted_info = data['extracted_info']
        current_queries = data['queries']
        prompt = ChatPromptTemplate.from_template(refine_search_prompt())
        refined_queries = llm.invoke(prompt.format(
            accusation=accusation,
            info=extracted_info,
            elastic_query=current_queries['elastic_query'],
            semantic_query=current_queries['semantic_query']
        ))
        state['search_results'][accusation]['queries'] = refined_queries.content
    return state

def should_continue_searching(state: SystemState) -> str:
    for data in state['search_results'].values():
        if "insufficient evidence" in data['extracted_info'].lower():
            return "continue_search"
    return "search_complete"

# Placeholder functions for other agents
def entity_analysis_agent(state: SystemState) -> SystemState:
    # Placeholder for entity analysis logic
    state['entity_analysis'] = "Entity analysis completed"
    return state

def risk_assessment_agent(state: SystemState) -> SystemState:
    # Placeholder for risk assessment logic
    state['risk_assessment'] = "Risk assessment completed"
    return state

def report_generation_agent(state: SystemState) -> SystemState:
    # Placeholder for report generation logic
    state['final_report'] = "Final report generated"
    return state

# Define the graph
workflow = Graph()

# Add nodes
workflow.add_node("orchestrator", orchestrate)
workflow.add_node("generate_initial_queries", generate_initial_queries)
workflow.add_node("perform_search", perform_search)
workflow.add_node("extract_information", extract_information)
workflow.add_node("refine_queries", refine_queries)
workflow.add_node("entity_analysis_agent", entity_analysis_agent)
workflow.add_node("risk_assessment_agent", risk_assessment_agent)
workflow.add_node("report_generation_agent", report_generation_agent)

# Add edges
workflow.add_edge("orchestrator", "generate_initial_queries")
workflow.add_edge("generate_initial_queries", "perform_search")
workflow.add_edge("perform_search", "extract_information")
workflow.add_edge("extract_information", should_continue_searching)
workflow.add_edge("refine_queries", "perform_search")
workflow.set_edge_with_condition("extract_information", "refine_queries", lambda x: x == "continue_search")
workflow.set_edge_with_condition("extract_information", "orchestrator", lambda x: x == "search_complete")
workflow.set_edge_with_condition("orchestrator", "entity_analysis_agent", lambda x: x == "start_entity_analysis")
workflow.set_edge_with_condition("orchestrator", "risk_assessment_agent", lambda x: x == "start_risk_assessment")
workflow.set_edge_with_condition("orchestrator", "report_generation_agent", lambda x: x == "generate_report")
workflow.add_edge("entity_analysis_agent", "orchestrator")
workflow.add_edge("risk_assessment_agent", "orchestrator")
workflow.add_edge("report_generation_agent", "orchestrator")

# Set the entrypoint
workflow.set_entry_point("orchestrator")

# Compile the graph
app = workflow.compile()

# Run the workflow
initial_state: SystemState = {
    "accusations": ["Accusation 1", "Accusation 2", "Accusation 3"],
    "search_results": {},
    "entity_analysis": {},
    "risk_assessment": {},
    "final_report": ""
}

final_state = app.invoke(initial_state)
print(final_state["final_report"])
