import os
import re
import faiss
import json
import pandas as pd
from elasticsearch.helpers import bulk
from difflib import SequenceMatcher
from typing import List, Dict, Any


class SemanticHybridSearch:
    """
    A class that combines Elasticsearch for keyword-based lexical searches and Faiss for semantic searches.

    This class provides methods to load and search both Elasticsearch and Faiss indices,
    as well as a hybrid search method that combines results from both search types.

    Attributes:
        data (list): The dataset used for searching.
        es_client (Elasticsearch): Elasticsearch client for performing lexical searches.
        embedding_model: Model used for encoding queries into embeddings.
        vector_index (faiss.Index): Faiss index for semantic searches.
        elastic_index_name (str): Name of the Elasticsearch index.
    """

    def __init__(
        self,
        es_client,
        embedding_model,
        data: list,
        elastic_index_path: str,
        vector_index_path: str,
    ):
        """
        Initialize the SemanticHybridSearch class.

        Args:
            es_client (Elasticsearch): Elasticsearch client.
            embedding_model: Model for encoding queries into embeddings.
            data (list): Dataset used for searching.
            elastic_index_path (str): Path to the Elasticsearch index file.
            vector_index_path (str): Path to the Faiss vector index file.
        """
        self.data = data
        self.es_client = es_client
        self.embedding_model = embedding_model
        self.vector_index = self.load_vector_index(vector_index_path)
        self.elastic_index = self.load_elastic_index(elastic_index_path)

        self.elastic_index_name = ""

    def load_elastic_index(self, elastic_index_path: str):
        """
        Load the Elasticsearch index from a file.

        Args:
            elastic_index_path (str): Path to the Elasticsearch index file.
        """
        with open(elastic_index_path) as f:
            documents = json.load(f)
            self.elastic_index_name = os.path.basename(elastic_index_path)
            print(f"Loading Index {self.elastic_index_name}")

            actions = [
                {
                    "_index": self.elastic_index_name,
                    "_id": doc["_id"],
                    "_source": doc["_source"],
                }
                for doc in documents
            ]
            bulk(self.es_client, actions)

    def load_vector_index(self, vector_index_path: str):
        """
        Load the Faiss vector index from a file.

        Args:
            vector_index_path (str): Path to the Faiss vector index file.

        Returns:
            faiss.Index: Loaded Faiss index.
        """
        print(f"Loading Index {os.path.basename(vector_index_path)}")
        index = faiss.read_index(vector_index_path)
        return index

    def elastic_search(self, query: dict, top_k: int = 3) -> list:
        """
        Perform a keyword-based search using Elasticsearch.

        Args:
            query (dict): Elasticsearch query.
            top_k (int): Number of top results to return. Defaults to 3.

        Returns:
            list: Top k search results.
        """
        results = self.es_client.search(index=self.elastic_index_name, body=query)
        return [result["_source"] for result in results["hits"]["hits"][:top_k]]

    def semantic_search(self, query: str, top_k: int = 3) -> list:
        """
        Perform a semantic search using Faiss.

        Args:
            query (str): Search query.
            top_k (int): Number of top results to return. Defaults to 3.

        Returns:
            list: Top k search results.
        """
        embedding = self.embedding_model.encode([query]).astype("float32")
        distances, idx = self.vector_index.search(embedding, top_k)
        results = [self.data[i] for i in idx[0]]

        return results

    def hybrid_search(
        self,
        elastic_query: dict,
        semantic_query: str,
        top_k: tuple = (3, 3),
        clean_overlap: bool = True,
    ) -> list:
        """
        Perform a hybrid search combining results from Elasticsearch and Faiss.

        Args:
            elastic_query (dict): Elasticsearch query for lexical search.
            semantic_query (str): Query string for semantic search.
            top_k (tuple): Tuple containing the number of top results to return for (elastic, semantic) searches. Defaults to 3.
            clean_overlap (bool): Whether to remove overlap in email threads results. Defaults to True.

        Returns:
            list: Combined and deduplicated search results.
        """
        elastic_results = self.elastic_search(elastic_query, top_k[0])
        semantic_results = self.semantic_search(semantic_query, top_k[1])

        hybrid_concat = pd.concat(
            [pd.DataFrame(elastic_results), pd.DataFrame(semantic_results)],
            ignore_index=True,
        ).drop_duplicates()
        hybrid_results = hybrid_concat.to_dict(orient="records")

        if clean_overlap:
            return self._extract_unique_content(hybrid_results)
        return hybrid_results

    def _clean_text(self, text: str) -> str:
        """
        Remove extra whitespace and newlines from the given text.

        Args:
            text (str): The input text to be cleaned.

        Returns:
            str: The cleaned text with extra whitespace removed.
        """
        return re.sub(r"\s+", " ", text).strip()

    def _find_overlap(self, text1: str, text2: str) -> str:
        """
        Find the longest common substring between two texts.

        Args:
            text1 (str): The first text to compare.
            text2 (str): The second text to compare.

        Returns:
            str: The longest common substring, or an empty string if no overlap is found.
        """
        matcher = SequenceMatcher(None, text1, text2)
        match = matcher.find_longest_match(0, len(text1), 0, len(text2))
        return text1[match.a : match.a + match.size] if match.size > 0 else ""

    def _extract_unique_content(
        self, emails: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract unique content from a list of email dictionaries by removing overlapping text.

        This function processes a list of email dictionaries, removing any overlapping content
        between emails to reduce redundancy. It preserves the original email structure and
        metadata while modifying only the 'Mail_Body' field.

        Args:
            emails (List[Dict[str, Any]]): A list of dictionaries, each representing an email
            keys for 'Origin', 'Subject', 'To', 'From', 'Cc', 'Bcc', 'Date', 'Attachment_Count',
            and 'Mail_Body'.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with the same structure as the input,
            but with overlapping content removed from the 'Mail_Body' field.

        Note:
            This function assumes that emails are ordered chronologically, with newer emails
            appearing later in the list.
        """
        unique_contents = []

        for i, email in enumerate(emails):
            current_email = self._clean_text(email["Mail_Body"])
            unique_content = current_email

            for j in range(i):
                previous_email = self._clean_text(emails[j]["Mail_Body"])
                overlap = self._find_overlap(previous_email, current_email)

                if len(overlap) > 10:
                    unique_content = unique_content.replace(overlap, "").strip()

            unique_contents.append(
                {
                    "Origin": email["Origin"],
                    "Subject": email["Subject"],
                    "To": email["To"],
                    "From": email["From"],
                    "Cc": email["Cc"],
                    "Bcc": email["Bcc"],
                    "Date": email["Date"],
                    "Attachment_Count": email["Attachment_Count"],
                    "Mail_Body": unique_content,
                }
            )

        return unique_contents
