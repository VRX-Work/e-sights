def system_prompt() -> str:
    return """You are an advanced AI agent designed for forensic and compliance investigations, specializing in analyzing large email datasets. Your task is to investigate multiple accusations simultaneously, searching for evidence, extracting relevant information, and drawing conclusions. You have access to a SemanticHybridSearch tool that combines Elasticsearch for keyword-based lexical searches and Faiss for semantic searches.

Key Responsibilities:
- Generate and refine search queries for multiple accusations, providing both Elasticsearch queries and semantic search strings.
- Analyze search results to extract relevant information.
- Evaluate evidence to determine if it supports or refutes accusations.
- Generate conclusions based on the accumulated evidence.

Guidelines:
- Maintain objectivity and avoid bias in your analysis.
- Consider the context and relationships between different pieces of information.
- Be thorough in your investigation, but also efficient in your search refinement.
- Clearly distinguish between facts, inferences, and speculations in your reports.
- Adapt your search and analysis strategies based on the unique aspects of each accusation.
- Utilize both lexical (Elasticsearch) and semantic (Faiss) search capabilities effectively.

You will be provided with specific instructions for each task. Always strive for accuracy, clarity, and relevance in your responses.
"""


def initial_query_prompt() -> str:
    return """Task: Generate initial search queries for the following accusation, suitable for use with the SemanticHybridSearch tool.

Accusation: {accusation}
Response Format: Provide the response in JSON format with the following keys:
elastic: Contains the Elasticsearch query in JSON format.
semantic: Contains the semantic search query as a string.

Guidelines:
Unionized Search Approach:
- Combine Elasticsearch and semantic search capabilities effectively. For example: Use Elasticsearch to filter specific fields (e.g., recipients, senders). Use semantic search to refine or specify the context within filtered results.
- If only one type of search is required, leave the other key empty (e.g., {} for elastic or "" for semantic).

Data Schema:
{
  "Subject": "Subject of mail",
  "To": "All Recipients",
  "From": "Name of sender",
  "Cc": "All CC",
  "Bcc": "All BCC",
  "Date": "Date in datetime format",
  "Attachment_Count": "Number of attachments",
  "Mail_Body": "Content of the mail in plain text format"
}

Elasticsearch Query:
- Focus on key terms and concepts relevant to the accusation.
- Use appropriate Elasticsearch query DSL structures (e.g., bool, must, should, match, term).
- Consider field-specific searches (e.g., subject, body, from, to) and apply boosts where necessary.
- Ensure queries are broad enough to capture relevant information but specific enough to exclude irrelevant results.

Semantic Search Query:
- Use natural language to describe the context and meaning of the accusation.
- Incorporate synonyms, related terms, and broader concepts to capture nuances beyond simple keywords.

Efficiency and Contextual Relevance:
- Adapt search strategies based on the unique aspects of each accusation.
- Ensure objectivity and avoid bias in query generation.
- Clearly distinguish between facts, inferences, and speculations.

Output Example:
{
  "elastic": {
    // Elasticsearch query here
  },
  "semantic": "Semantic search string here"
}

Do not provide a preamble or an explanation, the output should strictly be in JSON format with no comments"""  # Pass


def refine_search_prompt() -> str:
    return """Task: Refine the search queries based on the current queries and extracted information to uncover more details about the accusation. Provide refined queries for both Elasticsearch and semantic search.

Current Elasticsearch Query: {elastic_query}
Current Semantic Query: {semantic_query}
Extracted Info Summary: {info}
Areas for Further Investigation: {areas}
Accusation: {accusation}

Guidelines:
Unionized Search Approach:
- Combine Elasticsearch and semantic search capabilities effectively. For example: Use Elasticsearch to filter specific fields (e.g., recipients, senders). Use semantic search to refine or specify the context within filtered results.
- If only one type of search is required, leave the other key empty (e.g., {} for elastic or "" for semantic).

Data Schema:
{
  "Subject": "Subject of mail",
  "To": "All Recipients",
  "From": "Name of sender",
  "Cc": "All CC",
  "Bcc": "All BCC",
  "Date": "Date in datetime format",
  "Attachment_Count": "Number of attachments",
  "Mail_Body": "Content of the mail in plain text format"
}

Your refined queries should:
- Build upon the insights gained from the extracted information.
- Focus on areas where evidence is lacking or inconclusive.
- Include any new relevant terms or concepts discovered in the previous search.
- Be more specific than the initial queries, targeting the most promising areas for further investigation.
- Utilize Elasticsearch-specific features for the lexical query and natural language for the semantic query.

Refined Search Queries:

{
  "elastic": {
    // Elasticsearch query here
  },
  "semantic": "Semantic search string here"
}

Do not provide a preamble or an explanation, the output should strictly be in JSON format with no comments
"""  # Pass


def information_extraction_prompt() -> str:
    return """Task: Extract relevant information from the hybrid search results related to the following accusation:

Accusation: {accusation}

Hybrid Search Results:
{results}

Analyze the results, which combine Elasticsearch and Faiss search outcomes. Each result contains fields like "Subject", "To", "From", "Cc", "Bcc", "Date", "Attachment_Count", and "Mail_Body".

Provide the following information in JSON format:

{
  "accused_suspects": [],
  "incident_details": {
    "events": [
      {
        "details": "",
        "description": "",
        "date": "",
        "uid":"",
      }
    ]
  },
  "other_parties": {
    "name": {
      "relationship": "",
      "role": "",
      "uid":"uid",
    }
  },
  "summary": ""
}

Ensure all relevant information is included within this structure. Omit any explanations or additional text outside the JSON.
"""  # Pass


def analyze_evidence_prompt() -> str:
    return """Task: Analyze the extracted information and determine if it provides sufficient evidence for the accusation. If not, suggest areas for further investigation.

Accusation: {accusation}

Extracted Information:
{info}

Summary of Previous Information:
{summary}

Provide your analysis in the following JSON format:

{
  "credibility_and_reliability": {
    "events_analysis": [
      {
        "event": "Description of the event",
        "credibility_score": "Score from 0-100",
        "reasoning": "Explanation for the credibility score",
        "uid": "The uid of the source where event is mentioned"
      }
    ],
    "relationships_analysis": [
      {
        "entity1": "Name of first entity",
        "entity2": "Name of second entity",
        "relationship": "Description of relationship",
        "credibility_impact": "How this relationship affects credibility",
        "uid": "The uid of the source where entities are mentioned"
      }
    ],
    "overall_credibility_assessment": "Summary of overall credibility"
  },
  "sufficiency": {
    "conclusion": "One of: sufficient, partial, insufficient",
    "confidence_score": "Score from 0-100",
    "conclusion_statement": "Detailed explanation of the sufficiency conclusion",
    "refrences": ["List of the uids referenced"]
  },
  "areas_for_further_investigation": [
    "List of specific areas or questions needing further investigation"
  ]
}

Ensure all relevant analysis is included within this structure. Omit any explanations or additional text outside the JSON.
"""
