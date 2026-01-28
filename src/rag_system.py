"""
Advanced RAG System with Semantic Chunking and Hybrid Retrieval
"""
import os
import time
from typing import List, Dict, Tuple, Optional
import numpy as np
from dataclasses import dataclass
from collections import defaultdict
import re

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Installing required packages...")
    os.system("pip install sentence-transformers chromadb anthropic --break-system-packages")
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings


@dataclass
class ChunkMetadata:
    """Metadata for each chunk"""
    chunk_id: str
    document_id: str
    chunk_index: int
    char_start: int
    char_end: int
    semantic_density: float
    overlap_previous: bool
    overlap_next: bool


@dataclass
class RetrievalMetrics:
    """Metrics for tracking retrieval performance"""
    query_time: float
    num_chunks_retrieved: int
    avg_similarity_score: float
    max_similarity_score: float
    min_similarity_score: float
    reranking_time: Optional[float] = None


class SemanticChunker:
    """
    Implements semantic-aware chunking strategy.
    
    Strategy: Instead of fixed-size chunks, we use semantic boundaries
    (sentences, paragraphs) with dynamic sizing based on content density.
    
    Why this approach:
    1. Preserves semantic coherence - chunks don't break mid-thought
    2. Adaptive sizing - complex sections get smaller chunks for precision
    3. Overlapping windows - maintains context across boundaries
    """
    
    def __init__(
        self, 
        target_chunk_size: int = 512,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1024,
        overlap_tokens: int = 50
    ):
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_tokens = overlap_tokens
        
    def _calculate_semantic_density(self, text: str) -> float:
        """
        Calculate semantic density - how much information per character.
        Higher density = more complex content = smaller chunks preferred.
        """
        # Simple heuristic: unique word ratio, punctuation density
        words = text.lower().split()
        if not words:
            return 0.0
        
        unique_ratio = len(set(words)) / len(words)
        punct_density = sum(1 for c in text if c in '.,;:!?') / len(text)
        
        # Normalize to 0-1 range
        density = (unique_ratio * 0.7 + punct_density * 10 * 0.3)
        return min(1.0, density)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex"""
        # Handle common abbreviations
        text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr)\.', r'\1<PERIOD>', text)
        sentences = re.split(r'[.!?]+\s+', text)
        # Restore periods
        sentences = [s.replace('<PERIOD>', '.') for s in sentences]
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_text(self, text: str, document_id: str) -> List[Tuple[str, ChunkMetadata]]:
        """
        Chunk text using semantic boundaries with adaptive sizing.
        """
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0
        char_position = 0
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            sentence_len = len(sentence)
            density = self._calculate_semantic_density(sentence)
            
            # Adjust target size based on density
            adjusted_target = int(self.target_chunk_size * (1.5 - density))
            adjusted_target = max(self.min_chunk_size, min(adjusted_target, self.max_chunk_size))
            
            # Check if adding this sentence would exceed our target
            if current_size + sentence_len > adjusted_target and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = ' '.join(current_chunk)
                chunk_start = char_position - current_size
                
                metadata = ChunkMetadata(
                    chunk_id=f"{document_id}_chunk_{chunk_index}",
                    document_id=document_id,
                    chunk_index=chunk_index,
                    char_start=chunk_start,
                    char_end=char_position,
                    semantic_density=self._calculate_semantic_density(chunk_text),
                    overlap_previous=chunk_index > 0,
                    overlap_next=i < len(sentences) - 1
                )
                
                chunks.append((chunk_text, metadata))
                
                # Start new chunk with overlap
                if self.overlap_tokens > 0 and current_chunk:
                    # Keep last sentence(s) for overlap
                    overlap_text = current_chunk[-1]
                    current_chunk = [overlap_text, sentence]
                    current_size = len(overlap_text) + sentence_len
                else:
                    current_chunk = [sentence]
                    current_size = sentence_len
                
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_size += sentence_len
            
            char_position += sentence_len + 1  # +1 for space
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_start = char_position - current_size
            
            metadata = ChunkMetadata(
                chunk_id=f"{document_id}_chunk_{chunk_index}",
                document_id=document_id,
                chunk_index=chunk_index,
                char_start=chunk_start,
                char_end=char_position,
                semantic_density=self._calculate_semantic_density(chunk_text),
                overlap_previous=chunk_index > 0,
                overlap_next=False
            )
            
            chunks.append((chunk_text, metadata))
        
        return chunks


class HybridRetriever:
    """
    Implements hybrid retrieval combining:
    1. Dense vector similarity (semantic search)
    2. BM25-style keyword matching (lexical search)
    3. Metadata filtering
    """
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.collection = None
        self.keyword_index = defaultdict(set)  # word -> set of chunk_ids
        
    def _build_keyword_index(self, chunk_id: str, text: str):
        """Build inverted index for keyword search"""
        words = set(text.lower().split())
        for word in words:
            if len(word) > 2:  # Filter very short words
                self.keyword_index[word].add(chunk_id)
    
    def _keyword_search(self, query: str, top_k: int = 20) -> Dict[str, float]:
        """BM25-style keyword matching"""
        query_words = set(query.lower().split())
        scores = defaultdict(float)
        
        for word in query_words:
            if word in self.keyword_index:
                # Simple scoring: presence bonus + IDF approximation
                idf = np.log(1 + len(self.keyword_index) / (1 + len(self.keyword_index[word])))
                for chunk_id in self.keyword_index[word]:
                    scores[chunk_id] += idf
        
        # Normalize scores
        if scores:
            max_score = max(scores.values())
            scores = {k: v/max_score for k, v in scores.items()}
        
        # Return top-k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return dict(sorted_results)
    
    def add_documents(self, chunks: List[Tuple[str, ChunkMetadata]], collection):
        """Add chunked documents to vector store and keyword index"""
        self.collection = collection
        
        texts = []
        metadatas = []
        ids = []
        
        for text, metadata in chunks:
            texts.append(text)
            metadatas.append({
                'document_id': metadata.document_id,
                'chunk_index': metadata.chunk_index,
                'semantic_density': metadata.semantic_density,
                'char_start': metadata.char_start,
                'char_end': metadata.char_end
            })
            ids.append(metadata.chunk_id)
            
            # Build keyword index
            self._build_keyword_index(metadata.chunk_id, text)
        
        # Add to vector store
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        hybrid_alpha: float = 0.7,
        min_similarity: float = 0.3
    ) -> Tuple[List[Dict], RetrievalMetrics]:
        """
        Hybrid retrieval with metrics tracking.
        
        Args:
            query: Search query
            top_k: Number of results to return
            hybrid_alpha: Weight for dense retrieval (1-alpha for keyword)
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of retrieved chunks with metadata and metrics
        """
        start_time = time.time()
        
        # Dense retrieval (vector similarity)
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k * 2, 20)  # Get more for reranking
        )
        
        dense_scores = {}
        for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
            # Convert distance to similarity (ChromaDB uses cosine distance)
            similarity = 1 - distance
            dense_scores[doc_id] = similarity
        
        # Keyword retrieval
        keyword_scores = self._keyword_search(query, top_k=top_k * 2)
        
        # Hybrid fusion
        all_doc_ids = set(dense_scores.keys()) | set(keyword_scores.keys())
        hybrid_scores = {}
        
        for doc_id in all_doc_ids:
            dense_score = dense_scores.get(doc_id, 0.0)
            keyword_score = keyword_scores.get(doc_id, 0.0)
            hybrid_scores[doc_id] = (hybrid_alpha * dense_score + 
                                    (1 - hybrid_alpha) * keyword_score)
        
        # Filter by minimum similarity and sort
        filtered_scores = {k: v for k, v in hybrid_scores.items() 
                          if v >= min_similarity}
        sorted_results = sorted(filtered_scores.items(), 
                               key=lambda x: x[1], reverse=True)[:top_k]
        
        # Retrieve full documents
        retrieved_chunks = []
        if sorted_results:
            chunk_ids = [doc_id for doc_id, _ in sorted_results]
            full_results = self.collection.get(
                ids=chunk_ids,
                include=['documents', 'metadatas']
            )
            
            for i, (doc_id, score) in enumerate(sorted_results):
                retrieved_chunks.append({
                    'chunk_id': doc_id,
                    'text': full_results['documents'][i],
                    'metadata': full_results['metadatas'][i],
                    'similarity_score': score,
                    'rank': i + 1
                })
        
        query_time = time.time() - start_time
        
        # Calculate metrics
        similarity_scores = [chunk['similarity_score'] for chunk in retrieved_chunks]
        metrics = RetrievalMetrics(
            query_time=query_time,
            num_chunks_retrieved=len(retrieved_chunks),
            avg_similarity_score=np.mean(similarity_scores) if similarity_scores else 0.0,
            max_similarity_score=max(similarity_scores) if similarity_scores else 0.0,
            min_similarity_score=min(similarity_scores) if similarity_scores else 0.0
        )
        
        return retrieved_chunks, metrics


class AdvancedRAGSystem:
    """
    Complete RAG system with semantic chunking and hybrid retrieval.
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        persist_directory: str = "./chroma_db"
    ):
        self.chunker = SemanticChunker()
        self.retriever = HybridRetriever(embedding_model)
        
        # Initialize ChromaDB
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Create or get collection
        try:
            self.collection = self.client.create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
        except:
            self.collection = self.client.get_collection(name="documents")
        
        self.metrics_history = []
    
    def ingest_documents(self, documents: List[Dict[str, str]]):
        """
        Ingest documents into the RAG system.
        
        Args:
            documents: List of dicts with 'id' and 'text' keys
        """
        all_chunks = []
        
        for doc in documents:
            doc_id = doc['id']
            text = doc['text']
            
            # Chunk the document
            chunks = self.chunker.chunk_text(text, doc_id)
            all_chunks.extend(chunks)
            
            print(f"Document {doc_id}: created {len(chunks)} chunks")
        
        # Add to retriever
        self.retriever.add_documents(all_chunks, self.collection)
        print(f"\nTotal chunks ingested: {len(all_chunks)}")
        
        return len(all_chunks)
    
    def query(
        self, 
        query: str, 
        top_k: int = 5,
        return_metrics: bool = True
    ) -> Dict:
        """
        Query the RAG system.
        
        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            return_metrics: Whether to return metrics
        
        Returns:
            Dictionary with results and optionally metrics
        """
        chunks, metrics = self.retriever.retrieve(query, top_k=top_k)
        
        # Store metrics
        self.metrics_history.append({
            'query': query,
            'timestamp': time.time(),
            'metrics': metrics
        })
        
        result = {
            'query': query,
            'retrieved_chunks': chunks,
            'num_results': len(chunks)
        }
        
        if return_metrics:
            result['metrics'] = {
                'query_time_ms': metrics.query_time * 1000,
                'num_chunks_retrieved': metrics.num_chunks_retrieved,
                'avg_similarity_score': metrics.avg_similarity_score,
                'max_similarity_score': metrics.max_similarity_score,
                'min_similarity_score': metrics.min_similarity_score
            }
        
        return result
    
    def get_metrics_summary(self) -> Dict:
        """Get summary statistics of all queries"""
        if not self.metrics_history:
            return {}
        
        query_times = [m['metrics'].query_time for m in self.metrics_history]
        avg_scores = [m['metrics'].avg_similarity_score for m in self.metrics_history]
        
        return {
            'total_queries': len(self.metrics_history),
            'avg_query_time_ms': np.mean(query_times) * 1000,
            'median_query_time_ms': np.median(query_times) * 1000,
            'avg_similarity_score': np.mean(avg_scores),
            'p95_query_time_ms': np.percentile(query_times, 95) * 1000
        }


if __name__ == "__main__":
    # Example usage
    print("Initializing Advanced RAG System...")
    rag = AdvancedRAGSystem()
    
    # Sample documents
    documents = [
        {
            'id': 'doc1',
            'text': """
            Machine learning is a subset of artificial intelligence that focuses on 
            developing systems that can learn from data. Deep learning, a specialized 
            branch of machine learning, uses neural networks with multiple layers to 
            process information. These networks can identify patterns in large datasets, 
            making them useful for tasks like image recognition and natural language 
            processing. The key advantage of deep learning is its ability to automatically 
            extract features from raw data without manual feature engineering.
            """
        },
        {
            'id': 'doc2',
            'text': """
            Natural language processing (NLP) enables computers to understand and 
            generate human language. Modern NLP systems use transformer architectures, 
            which were introduced in 2017. Transformers use attention mechanisms to 
            process sequences of text, allowing them to capture long-range dependencies. 
            This architecture has revolutionized the field, leading to models like BERT 
            and GPT that achieve state-of-the-art performance on many tasks.
            """
        }
    ]
    
    print("\nIngesting documents...")
    num_chunks = rag.ingest_documents(documents)
    
    print("\nQuerying the system...")
    result = rag.query("What are transformers in NLP?", top_k=3)
    
    print(f"\nQuery: {result['query']}")
    print(f"Retrieved {result['num_results']} chunks:")
    for chunk in result['retrieved_chunks']:
        print(f"\n  Rank {chunk['rank']}: Score {chunk['similarity_score']:.3f}")
        print(f"  {chunk['text'][:150]}...")
    
    print(f"\nMetrics: {result['metrics']}")
