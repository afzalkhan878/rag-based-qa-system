"""
Unit tests for the RAG system
"""
import unittest
from rag_system import SemanticChunker, AdvancedRAGSystem
import tempfile
import shutil


class TestSemanticChunker(unittest.TestCase):
    """Test the semantic chunking functionality"""
    
    def setUp(self):
        self.chunker = SemanticChunker(
            target_chunk_size=100,
            min_chunk_size=50,
            max_chunk_size=200,
            overlap_tokens=20
        )
    
    def test_basic_chunking(self):
        """Test that text is chunked"""
        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = self.chunker.chunk_text(text, "test_doc")
        
        self.assertGreater(len(chunks), 0, "Should create at least one chunk")
        
        # Check all chunks have text and metadata
        for chunk_text, metadata in chunks:
            self.assertIsInstance(chunk_text, str)
            self.assertTrue(len(chunk_text) > 0)
            self.assertEqual(metadata.document_id, "test_doc")
    
    def test_semantic_density_calculation(self):
        """Test semantic density calculation"""
        dense_text = "Quantum entanglement phenomenon particles superposition"
        sparse_text = "The the the and and and"
        
        dense_score = self.chunker._calculate_semantic_density(dense_text)
        sparse_score = self.chunker._calculate_semantic_density(sparse_text)
        
        self.assertGreater(dense_score, sparse_score, 
                          "Dense text should have higher score")
    
    def test_chunk_size_constraints(self):
        """Test that chunks respect size constraints"""
        long_text = " ".join(["This is a sentence."] * 100)
        chunks = self.chunker.chunk_text(long_text, "test_doc")
        
        for chunk_text, metadata in chunks:
            chunk_len = len(chunk_text)
            self.assertGreaterEqual(chunk_len, self.chunker.min_chunk_size - 50,
                                   f"Chunk too small: {chunk_len}")
            self.assertLessEqual(chunk_len, self.chunker.max_chunk_size + 100,
                                f"Chunk too large: {chunk_len}")
    
    def test_overlap(self):
        """Test that chunks have proper overlap"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = self.chunker.chunk_text(text, "test_doc")
        
        if len(chunks) > 1:
            # Check metadata indicates overlap
            for i, (_, metadata) in enumerate(chunks):
                if i > 0:
                    self.assertTrue(metadata.overlap_previous)
                if i < len(chunks) - 1:
                    self.assertTrue(metadata.overlap_next)


class TestAdvancedRAGSystem(unittest.TestCase):
    """Test the complete RAG system"""
    
    def setUp(self):
        # Create temporary directory for ChromaDB
        self.temp_dir = tempfile.mkdtemp()
        self.rag = AdvancedRAGSystem(persist_directory=self.temp_dir)
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_document_ingestion(self):
        """Test document ingestion"""
        documents = [
            {'id': 'doc1', 'text': 'This is a test document about machine learning.'},
            {'id': 'doc2', 'text': 'This is another test document about AI.'}
        ]
        
        num_chunks = self.rag.ingest_documents(documents)
        self.assertGreater(num_chunks, 0, "Should create chunks")
    
    def test_query(self):
        """Test querying the system"""
        documents = [
            {'id': 'doc1', 'text': 'Machine learning is a subset of artificial intelligence.'},
            {'id': 'doc2', 'text': 'Deep learning uses neural networks with multiple layers.'}
        ]
        
        self.rag.ingest_documents(documents)
        result = self.rag.query("What is machine learning?", top_k=2)
        
        self.assertIn('query', result)
        self.assertIn('retrieved_chunks', result)
        self.assertIn('metrics', result)
        self.assertGreater(len(result['retrieved_chunks']), 0)
    
    def test_metrics_tracking(self):
        """Test that metrics are tracked"""
        documents = [
            {'id': 'doc1', 'text': 'Test document content.'}
        ]
        
        self.rag.ingest_documents(documents)
        self.rag.query("test query", top_k=1)
        
        metrics_summary = self.rag.get_metrics_summary()
        self.assertEqual(metrics_summary['total_queries'], 1)
        self.assertIn('avg_query_time_ms', metrics_summary)
    
    def test_similarity_scores(self):
        """Test that similarity scores are reasonable"""
        documents = [
            {'id': 'doc1', 'text': 'Python is a programming language.'},
            {'id': 'doc2', 'text': 'The weather is sunny today.'}
        ]
        
        self.rag.ingest_documents(documents)
        result = self.rag.query("What is Python?", top_k=2)
        
        # First result should be about Python with higher score
        chunks = result['retrieved_chunks']
        if len(chunks) >= 2:
            self.assertGreater(chunks[0]['similarity_score'], 
                             chunks[1]['similarity_score'],
                             "Most relevant result should have highest score")
    
    def test_top_k_parameter(self):
        """Test that top_k parameter works"""
        documents = [
            {'id': f'doc{i}', 'text': f'Document {i} content.'} 
            for i in range(5)
        ]
        
        self.rag.ingest_documents(documents)
        
        result = self.rag.query("document", top_k=3)
        self.assertLessEqual(len(result['retrieved_chunks']), 3)


class TestHybridRetrieval(unittest.TestCase):
    """Test hybrid retrieval specifically"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rag = AdvancedRAGSystem(persist_directory=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_keyword_matching(self):
        """Test that keyword matching works"""
        documents = [
            {'id': 'doc1', 'text': 'Quantum computing uses qubits for computation.'},
            {'id': 'doc2', 'text': 'Classical computing uses bits for data storage.'}
        ]
        
        self.rag.ingest_documents(documents)
        
        # Query with specific keyword
        result = self.rag.query("qubits", top_k=2)
        
        # Should retrieve doc1 with high score
        self.assertGreater(len(result['retrieved_chunks']), 0)
        top_result = result['retrieved_chunks'][0]
        self.assertIn('quantum', top_result['text'].lower())


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticChunker))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedRAGSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestHybridRetrieval))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
