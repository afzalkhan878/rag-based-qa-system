"""
Metrics Tracker Module
Tracks and reports system performance metrics
"""
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricsTracker:
    """
    Tracks various system metrics for monitoring and analysis
    
    Metrics tracked:
    - Query latency (retrieval, generation, total)
    - Similarity scores
    - Document processing time
    - Error rates
    """
    
    def __init__(self):
        """Initialize metrics tracker"""
        self.queries: List[Dict] = []
        self.documents: List[Dict] = []
        self.errors: List[Dict] = []
        
        logger.info("MetricsTracker initialized")
    
    def track_query(
        self,
        question: str,
        chunks_retrieved: int,
        retrieval_time_ms: float,
        generation_time_ms: float,
        total_time_ms: float,
        confidence_score: float
    ):
        """
        Track query metrics
        
        Args:
            question: User question
            chunks_retrieved: Number of chunks retrieved
            retrieval_time_ms: Time spent on retrieval
            generation_time_ms: Time spent on answer generation
            total_time_ms: Total query time
            confidence_score: Confidence of the answer
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'question_length': len(question),
            'chunks_retrieved': chunks_retrieved,
            'retrieval_time_ms': retrieval_time_ms,
            'generation_time_ms': generation_time_ms,
            'total_time_ms': total_time_ms,
            'confidence_score': confidence_score
        }
        
        self.queries.append(metric)
        
        # Log warning if query is slow
        if total_time_ms > 5000:  # 5 seconds
            logger.warning(f"Slow query detected: {total_time_ms:.2f}ms")
    
    def track_document_processing(
        self,
        document_id: str,
        chunks_created: int,
        processing_time_ms: float
    ):
        """
        Track document processing metrics
        
        Args:
            document_id: Document identifier
            chunks_created: Number of chunks created
            processing_time_ms: Processing time
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'document_id': document_id,
            'chunks_created': chunks_created,
            'processing_time_ms': processing_time_ms,
            'time_per_chunk_ms': processing_time_ms / chunks_created if chunks_created > 0 else 0
        }
        
        self.documents.append(metric)
        
        logger.info(f"Document processing tracked: {chunks_created} chunks in {processing_time_ms:.2f}ms")
    
    def track_error(self, error_type: str, error_message: str):
        """
        Track error occurrence
        
        Args:
            error_type: Type/category of error
            error_message: Error message
        """
        error = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message
        }
        
        self.errors.append(error)
        logger.error(f"Error tracked: {error_type} - {error_message}")
    
    def get_metrics(self) -> Dict:
        """
        Get aggregated metrics
        
        Returns:
            Dictionary containing metric summaries
        """
        return {
            'summary': self._get_summary(),
            'query_metrics': self._get_query_metrics(),
            'document_metrics': self._get_document_metrics(),
            'error_metrics': self._get_error_metrics()
        }
    
    def _get_summary(self) -> Dict:
        """Get high-level summary"""
        return {
            'total_queries': len(self.queries),
            'total_documents': len(self.documents),
            'total_errors': len(self.errors),
            'error_rate': len(self.errors) / max(len(self.queries), 1)
        }
    
    def _get_query_metrics(self) -> Dict:
        """Get query-specific metrics"""
        if not self.queries:
            return {
                'count': 0,
                'avg_retrieval_time_ms': 0,
                'avg_generation_time_ms': 0,
                'avg_total_time_ms': 0,
                'avg_confidence': 0,
                'avg_chunks_retrieved': 0
            }
        
        return {
            'count': len(self.queries),
            'avg_retrieval_time_ms': sum(q['retrieval_time_ms'] for q in self.queries) / len(self.queries),
            'avg_generation_time_ms': sum(q['generation_time_ms'] for q in self.queries) / len(self.queries),
            'avg_total_time_ms': sum(q['total_time_ms'] for q in self.queries) / len(self.queries),
            'avg_confidence': sum(q['confidence_score'] for q in self.queries) / len(self.queries),
            'avg_chunks_retrieved': sum(q['chunks_retrieved'] for q in self.queries) / len(self.queries),
            'p50_total_time_ms': self._percentile([q['total_time_ms'] for q in self.queries], 50),
            'p95_total_time_ms': self._percentile([q['total_time_ms'] for q in self.queries], 95),
            'p99_total_time_ms': self._percentile([q['total_time_ms'] for q in self.queries], 99)
        }
    
    def _get_document_metrics(self) -> Dict:
        """Get document processing metrics"""
        if not self.documents:
            return {
                'count': 0,
                'avg_chunks_per_doc': 0,
                'avg_processing_time_ms': 0,
                'avg_time_per_chunk_ms': 0
            }
        
        return {
            'count': len(self.documents),
            'avg_chunks_per_doc': sum(d['chunks_created'] for d in self.documents) / len(self.documents),
            'avg_processing_time_ms': sum(d['processing_time_ms'] for d in self.documents) / len(self.documents),
            'avg_time_per_chunk_ms': sum(d['time_per_chunk_ms'] for d in self.documents) / len(self.documents)
        }
    
    def _get_error_metrics(self) -> Dict:
        """Get error metrics"""
        if not self.errors:
            return {
                'count': 0,
                'by_type': {}
            }
        
        # Count errors by type
        error_counts = {}
        for error in self.errors:
            error_type = error['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            'count': len(self.errors),
            'by_type': error_counts,
            'recent_errors': self.errors[-5:]  # Last 5 errors
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.queries = []
        self.documents = []
        self.errors = []
        logger.info("Metrics reset")
