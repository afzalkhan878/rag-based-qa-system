"""
Example Usage - Advanced RAG System
Run this to see the system in action with various scenarios
"""

from rag_system import AdvancedRAGSystem
import json


def example_1_basic_usage():
    """Basic document ingestion and querying"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Usage")
    print("="*80)
    
    # Initialize
    rag = AdvancedRAGSystem()
    
    # Sample documents
    documents = [
        {
            'id': 'ml_basics',
            'text': """
            Machine learning is a method of data analysis that automates analytical 
            model building. It is a branch of artificial intelligence based on the 
            idea that systems can learn from data, identify patterns and make decisions 
            with minimal human intervention. Machine learning algorithms are trained 
            on data sets that contain examples. The algorithm learns from these examples 
            and can then make predictions or decisions when given new data.
            """
        },
        {
            'id': 'deep_learning',
            'text': """
            Deep learning is a subset of machine learning that uses neural networks 
            with multiple layers. These deep neural networks attempt to mimic how the 
            human brain works, although they fall far short of matching its ability. 
            Deep learning drives many artificial intelligence applications and services 
            that improve automation. It can be used for image recognition, speech 
            recognition, natural language processing, and many other tasks.
            """
        }
    ]
    
    # Ingest
    print("\n📥 Ingesting documents...")
    num_chunks = rag.ingest_documents(documents)
    print(f"✓ Created {num_chunks} chunks from {len(documents)} documents")
    
    # Query
    queries = [
        "What is machine learning?",
        "How does deep learning work?",
        "What is neural network?"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        result = rag.query(query, top_k=2)
        
        print(f"   Retrieved {result['num_results']} chunks in {result['metrics']['query_time_ms']:.1f}ms")
        
        for i, chunk in enumerate(result['retrieved_chunks'][:1], 1):  # Show top 1
            print(f"\n   Top Result (score: {chunk['similarity_score']:.3f}):")
            print(f"   {chunk['text'][:200]}...")


def example_2_chunking_comparison():
    """Compare chunking on different content types"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Chunking Strategy Comparison")
    print("="*80)
    
    from rag_system import SemanticChunker
    
    chunker = SemanticChunker()
    
    test_cases = [
        {
            'name': 'Technical (Dense)',
            'text': """
            Quantum entanglement is a phenomenon where quantum states of two or more 
            objects are linked. EPR paradox demonstrates non-locality. Bell's theorem 
            proves quantum mechanics contradicts local realism. Measurements show 
            correlation regardless of distance.
            """
        },
        {
            'name': 'Narrative (Medium)',
            'text': """
            The company announced its quarterly results yesterday. Revenue increased 
            by 15% year-over-year. The CEO expressed optimism about future growth. 
            Investors reacted positively to the news. Stock prices rose by 8% in 
            after-hours trading.
            """
        },
        {
            'name': 'Simple (Sparse)',
            'text': """
            The cat sat on the mat. The dog ran in the park. The bird flew in the sky. 
            The fish swam in the pond. The sun shone brightly. The weather was nice.
            """
        }
    ]
    
    print("\n📊 Chunking Analysis:\n")
    
    for test in test_cases:
        chunks = chunker.chunk_text(test['text'], test['name'])
        
        print(f"{test['name']}:")
        print(f"  Original: {len(test['text'])} chars")
        print(f"  Chunks: {len(chunks)}")
        
        for i, (text, meta) in enumerate(chunks):
            print(f"    Chunk {i+1}: {len(text)} chars, density: {meta.semantic_density:.2f}")
        print()


def example_3_hybrid_retrieval():
    """Demonstrate hybrid retrieval advantages"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Hybrid Retrieval (Vector + Keyword)")
    print("="*80)
    
    rag = AdvancedRAGSystem()
    
    documents = [
        {
            'id': 'python',
            'text': 'Python is a high-level programming language known for its simplicity.'
        },
        {
            'id': 'java',
            'text': 'Java is an object-oriented programming language used for enterprise applications.'
        },
        {
            'id': 'javascript',
            'text': 'JavaScript is primarily used for web development and runs in browsers.'
        }
    ]
    
    rag.ingest_documents(documents)
    
    print("\n🔍 Query: 'programming language for web'")
    result = rag.query('programming language for web', top_k=3)
    
    print("\n📋 Results ranked by hybrid score:\n")
    for chunk in result['retrieved_chunks']:
        print(f"  Rank {chunk['rank']}: {chunk['chunk_id']}")
        print(f"    Score: {chunk['similarity_score']:.3f}")
        print(f"    Text: {chunk['text'][:60]}...")
        print()
    
    print("💡 Notice: 'JavaScript' ranks highest because:")
    print("   • Semantic match: 'web' relates to JavaScript")
    print("   • Keyword match: 'programming language' appears in text")
    print("   • Hybrid fusion combines both signals")


def example_4_metrics_monitoring():
    """Show metrics tracking"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Metrics Tracking")
    print("="*80)
    
    rag = AdvancedRAGSystem()
    
    # Create sample data
    documents = [{'id': f'doc{i}', 'text': f'Document {i} content ' * 20} 
                 for i in range(10)]
    
    rag.ingest_documents(documents)
    
    # Run multiple queries
    queries = [
        'document content',
        'sample text',
        'information about document 5',
        'find document',
        'search query'
    ]
    
    print("\n📊 Running queries and tracking metrics...\n")
    
    for query in queries:
        result = rag.query(query, top_k=3)
        metrics = result['metrics']
        
        print(f"Query: '{query}'")
        print(f"  Latency: {metrics['query_time_ms']:.2f}ms")
        print(f"  Avg similarity: {metrics['avg_similarity_score']:.3f}")
        print(f"  Results: {metrics['num_chunks_retrieved']}")
        print()
    
    # Get summary
    summary = rag.get_metrics_summary()
    
    print("📈 Performance Summary:")
    print(f"  Total queries: {summary['total_queries']}")
    print(f"  Avg latency: {summary['avg_query_time_ms']:.2f}ms")
    print(f"  Median latency: {summary['median_query_time_ms']:.2f}ms")
    print(f"  P95 latency: {summary['p95_query_time_ms']:.2f}ms")
    print(f"  Avg similarity: {summary['avg_similarity_score']:.3f}")


def example_5_failure_case():
    """Demonstrate and explain a retrieval failure"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Retrieval Failure Analysis")
    print("="*80)
    
    rag = AdvancedRAGSystem()
    
    documents = [
        {
            'id': 'ml_doc',
            'text': 'Machine learning uses algorithms to learn from data. Models improve with experience.'
        },
        {
            'id': 'recipe',
            'text': 'To make pasta, boil water, add salt, cook pasta for 10 minutes, drain and serve.'
        }
    ]
    
    rag.ingest_documents(documents)
    
    # This query should fail or return low-confidence results
    query = "How to prevent overfitting in neural networks?"
    
    print(f"\n❌ Query: {query}")
    result = rag.query(query, top_k=2)
    
    print(f"\n📊 Results:")
    for chunk in result['retrieved_chunks']:
        print(f"\n  {chunk['chunk_id']} (score: {chunk['similarity_score']:.3f})")
        print(f"  {chunk['text']}")
    
    print("\n💡 Analysis:")
    print("  This query fails because:")
    print("  1. Documents mention 'machine learning' but not 'neural networks'")
    print("  2. No information about 'overfitting' or prevention techniques")
    print("  3. Semantic embeddings can't bridge this knowledge gap")
    print("\n  Solutions:")
    print("  • Add more comprehensive documents")
    print("  • Use query expansion (neural networks → ML models)")
    print("  • Implement query understanding to detect missing info")
    print("  • Return confidence scores to user")


def main():
    """Run all examples"""
    print("\n")
    print("┌" + "─"*78 + "┐")
    print("│" + " "*20 + "Advanced RAG System Examples" + " "*29 + "│")
    print("└" + "─"*78 + "┘")
    
    examples = [
        example_1_basic_usage,
        example_2_chunking_comparison,
        example_3_hybrid_retrieval,
        example_4_metrics_monitoring,
        example_5_failure_case
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"\n⚠️  Error in example {i}: {e}")
        
        if i < len(examples):
            input("\nPress Enter to continue to next example...")
    
    print("\n" + "="*80)
    print("✓ All examples completed!")
    print("="*80)
    print("\nNext steps:")
    print("  • Try api.py to run the REST API")
    print("  • Run test_rag.py to execute unit tests")
    print("  • Read EXPLANATION.md for technical details")


if __name__ == '__main__':
    main()
