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

# Data Ingestion and Search Agent functions
def generate_queries(state: SystemState) -> SystemState:
    for accusation in state['accusations']:
        prompt = ChatPromptTemplate.from_template(
            "Generate Elasticsearch query and semantic query for the accusation: {accusation}"
        )
        response = llm.invoke(prompt.format(accusation=accusation))
        state['search_results'][accusation] = {'queries': response.content}
    return state

def perform_search(state: SystemState) -> SystemState:
    for accusation, data in state['search_results'].items():
        queries = data['queries']
        # Parse queries from LLM response
        elastic_query, semantic_query = parse_queries(queries)
        results = semantic_hybrid_search.hybrid_search(elastic_query, semantic_query)
        state['search_results'][accusation]['results'] = results
    return state

def extract_information(state: SystemState) -> SystemState:
    for accusation, data in state['search_results'].items():
        results = data['results']
        prompt = ChatPromptTemplate.from_template(
            "Extract relevant information from these search results related to the accusation: {accusation}\n\nResults: {results}"
        )
        extracted_info = llm.invoke(prompt.format(accusation=accusation, results=results))
        state['search_results'][accusation]['extracted_info'] = extracted_info.content
    return state

def refine_queries(state: SystemState) -> SystemState:
    for accusation, data in state['search_results'].items():
        extracted_info = data['extracted_info']
        prompt = ChatPromptTemplate.from_template(
            "Refine the search queries based on the extracted information:\n{extracted_info}\n\nFor the accusation: {accusation}"
        )
        refined_queries = llm.invoke(prompt.format(accusation=accusation, extracted_info=extracted_info))
        state['search_results'][accusation]['refined_queries'] = refined_queries.content
    return state

def should_continue_searching(state: SystemState) -> str:
    for data in state['search_results'].values():
        if "insufficient evidence" in data['extracted_info'].lower():
            return "continue_search"
    return "move_to_analysis"

# Entity and Content Analysis Agent function (placeholder)
def analyze_entities_and_content(state: SystemState) -> SystemState:
    # Placeholder for entity and content analysis logic
    all_extracted_info = "\n".join([data['extracted_info'] for data in state['search_results'].values()])
    prompt = ChatPromptTemplate.from_template(
        "Analyze the entities, their relationships, and the content in the following extracted information:\n{all_extracted_info}"
    )
    analysis = llm.invoke(prompt.format(all_extracted_info=all_extracted_info))
    state['entity_analysis'] = analysis.content
    return state

# Compliance and Risk Assessment Agent function (placeholder)
def assess_compliance_and_risks(state: SystemState) -> SystemState:
    prompt = ChatPromptTemplate.from_template(
        "Assess the compliance risks based on the entity analysis and extracted information:\n{entity_analysis}\n{extracted_info}"
    )
    assessment = llm.invoke(prompt.format(
        entity_analysis=state['entity_analysis'],
        extracted_info=str(state['search_results'])
    ))
    state['risk_assessment'] = assessment.content
    return state

# Report Generation Agent function (placeholder)
def generate_final_report(state: SystemState) -> SystemState:
    prompt = ChatPromptTemplate.from_template(
        "Generate a comprehensive final report based on the following information:\nAccusations: {accusations}\nSearch Results: {search_results}\nEntity Analysis: {entity_analysis}\nRisk Assessment: {risk_assessment}"
    )
    report = llm.invoke(prompt.format(
        accusations=state['accusations'],
        search_results=str(state['search_results']),
        entity_analysis=state['entity_analysis'],
        risk_assessment=state['risk_assessment']
    ))
    state['final_report'] = report.content
    return state

# Define the graph
workflow = Graph()

# Add nodes for all agents
workflow.add_node("generate_queries", generate_queries)
workflow.add_node("perform_search", perform_search)
workflow.add_node("extract_information", extract_information)
workflow.add_node("refine_queries", refine_queries)
workflow.add_node("analyze_entities_and_content", analyze_entities_and_content)
workflow.add_node("assess_compliance_and_risks", assess_compliance_and_risks)
workflow.add_node("generate_final_report", generate_final_report)

# Add edges to connect all agents
workflow.add_edge("generate_queries", "perform_search")
workflow.add_edge("perform_search", "extract_information")
workflow.add_edge("extract_information", should_continue_searching)
workflow.add_edge("refine_queries", "perform_search")
workflow.set_edge_with_condition("extract_information", "refine_queries", lambda x: x == "continue_search")
workflow.set_edge_with_condition("extract_information", "analyze_entities_and_content", lambda x: x == "move_to_analysis")
workflow.add_edge("analyze_entities_and_content", "assess_compliance_and_risks")
workflow.add_edge("assess_compliance_and_risks", "generate_final_report")
workflow.add_edge("generate_final_report", END)

# Set the entrypoint
workflow.set_entry_point("generate_queries")

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
