"""
Retrieval Service Module
Handles query embedding and retrieval from vector store
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving relevant document chunks based on queries
    
    Implements semantic search using cosine similarity
    """
    
    def __init__(self, vector_store, embedding_service):
        """
        Initialize retrieval service
        
        Args:
            vector_store: VectorStore instance
            embedding_service: EmbeddingService instance
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.similarity_threshold = 0.3  # Minimum similarity score to consider
        
        logger.info(f"RetrievalService initialized with similarity threshold: {self.similarity_threshold}")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User query string
            top_k: Number of top results to retrieve
        
        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            logger.info(f"Retrieving chunks for query: '{query}' (top_k={top_k})")
            
            # Generate query embedding
            query_embedding = self.embedding_service.embed_query(query)
            
            # Search vector store
            results = self.vector_store.search(query_embedding, top_k=top_k)
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in results 
                if result['score'] >= self.similarity_threshold
            ]
            
            if len(filtered_results) < len(results):
                logger.info(f"Filtered {len(results) - len(filtered_results)} results below threshold {self.similarity_threshold}")
            
            # Log retrieval quality metrics
            if filtered_results:
                scores = [r['score'] for r in filtered_results]
                logger.info(f"Retrieved {len(filtered_results)} chunks. Score range: [{min(scores):.4f}, {max(scores):.4f}]")
            else:
                logger.warning(f"No chunks retrieved above threshold {self.similarity_threshold}")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            raise
    
    def set_similarity_threshold(self, threshold: float):
        """
        Set the minimum similarity threshold
        
        Args:
            threshold: Minimum similarity score (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        self.similarity_threshold = threshold
        logger.info(f"Similarity threshold updated to {threshold}")
