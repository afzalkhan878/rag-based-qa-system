"""
Vector Store Module
Manages document embeddings storage and similarity search using FAISS
"""
import numpy as np
from typing import List, Dict, Optional
import logging
import pickle
import os

logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS-based vector store for efficient similarity search
    
    Uses FAISS IndexFlatIP (Inner Product) for cosine similarity
    since embeddings are normalized.
    """
    
    def __init__(self, embedding_dim: int = 384, persist_dir: str = "./data"):
        """
        Initialize vector store
        
        Args:
            embedding_dim: Dimension of embeddings
            persist_dir: Directory to persist index and metadata
        """
        self.embedding_dim = embedding_dim
        self.persist_dir = persist_dir
        self.index = None
        self.chunks = []  # Store chunk metadata
        self.document_map = {}  # Map document_id to chunk indices
        
        # Create persist directory
        os.makedirs(persist_dir, exist_ok=True)
        
        self._initialize_index()
        self._load_persisted_data()
        
        logger.info(f"VectorStore initialized with dimension {embedding_dim}")
    
    def _initialize_index(self):
        """Initialize FAISS index"""
        try:
            import faiss
            
            # Use IndexFlatIP for inner product (cosine similarity with normalized vectors)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            logger.info("FAISS index initialized with IndexFlatIP")
            
        except ImportError:
            logger.error("FAISS not installed")
            raise ImportError("FAISS library required. Install with: pip install faiss-cpu")
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {str(e)}")
            raise
    
    def add_documents(self, chunks: List[Dict], embeddings: np.ndarray, document_id: str):
        """
        Add document chunks and their embeddings to the vector store
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: NumPy array of embeddings
            document_id: Unique document identifier
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        try:
            # Get starting index for new chunks
            start_idx = len(self.chunks)
            
            # Add to index
            self.index.add(embeddings.astype('float32'))
            
            # Store chunk metadata
            self.chunks.extend(chunks)
            
            # Update document map
            chunk_indices = list(range(start_idx, start_idx + len(chunks)))
            if document_id in self.document_map:
                self.document_map[document_id].extend(chunk_indices)
            else:
                self.document_map[document_id] = chunk_indices
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id}. Total chunks: {len(self.chunks)}")
            
            # Persist to disk
            self._persist_data()
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """
        Search for similar chunks using query embedding
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
        
        Returns:
            List of dictionaries containing chunk data and similarity scores
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty, no results to return")
            return []
        
        try:
            # Ensure query embedding is 2D
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), min(top_k, self.index.ntotal))
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks) and idx >= 0:
                    result = {
                        'text': self.chunks[idx]['text'],
                        'metadata': self.chunks[idx]['metadata'],
                        'score': float(score)  # Cosine similarity score
                    }
                    results.append(result)
            
            logger.info(f"Retrieved {len(results)} chunks with scores: {[r['score'] for r in results]}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its chunks from the store
        
        Note: FAISS doesn't support deletion, so we rebuild the index
        
        Args:
            document_id: Document ID to delete
        
        Returns:
            True if document was deleted, False if not found
        """
        if document_id not in self.document_map:
            logger.warning(f"Document {document_id} not found")
            return False
        
        try:
            # Get indices to remove
            indices_to_remove = set(self.document_map[document_id])
            
            # Filter chunks and rebuild embeddings
            new_chunks = []
            new_embeddings = []
            
            for i, chunk in enumerate(self.chunks):
                if i not in indices_to_remove:
                    new_chunks.append(chunk)
            
            # Rebuild index if we have chunks left
            if new_chunks:
                # Re-generate embeddings for remaining chunks
                from .embedding_service import EmbeddingService
                embedding_service = EmbeddingService()
                texts = [chunk['text'] for chunk in new_chunks]
                new_embeddings = embedding_service.embed_chunks(texts)
                
                # Reset index
                self._initialize_index()
                self.index.add(new_embeddings.astype('float32'))
                self.chunks = new_chunks
                
                # Rebuild document map
                self.document_map = {}
                for idx, chunk in enumerate(self.chunks):
                    doc_id = chunk['metadata']['document_id']
                    if doc_id in self.document_map:
                        self.document_map[doc_id].append(idx)
                    else:
                        self.document_map[doc_id] = [idx]
            else:
                # No chunks left, reset everything
                self._initialize_index()
                self.chunks = []
                self.document_map = {}
            
            # Persist changes
            self._persist_data()
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'chunks': len(self.chunks),
            'documents': len(self.document_map),
            'embedding_dim': self.embedding_dim
        }
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the store"""
        documents = []
        for doc_id, chunk_indices in self.document_map.items():
            if chunk_indices:
                first_chunk = self.chunks[chunk_indices[0]]
                documents.append({
                    'document_id': doc_id,
                    'filename': first_chunk['metadata']['filename'],
                    'chunk_count': len(chunk_indices)
                })
        return documents
    
    def _persist_data(self):
        """Persist index and metadata to disk"""
        try:
            import faiss
            
            # Save FAISS index
            index_path = os.path.join(self.persist_dir, "faiss_index.bin")
            faiss.write_index(self.index, index_path)
            
            # Save metadata
            metadata_path = os.path.join(self.persist_dir, "metadata.pkl")
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'chunks': self.chunks,
                    'document_map': self.document_map
                }, f)
            
            logger.info("Data persisted to disk")
            
        except Exception as e:
            logger.error(f"Error persisting data: {str(e)}")
    
    def _load_persisted_data(self):
        """Load persisted index and metadata from disk"""
        try:
            import faiss
            
            index_path = os.path.join(self.persist_dir, "faiss_index.bin")
            metadata_path = os.path.join(self.persist_dir, "metadata.pkl")
            
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                # Load FAISS index
                self.index = faiss.read_index(index_path)
                
                # Load metadata
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.chunks = data['chunks']
                    self.document_map = data['document_map']
                
                logger.info(f"Loaded persisted data: {len(self.chunks)} chunks, {len(self.document_map)} documents")
            else:
                logger.info("No persisted data found, starting fresh")
                
        except Exception as e:
            logger.warning(f"Error loading persisted data: {str(e)}. Starting fresh.")
