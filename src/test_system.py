"""
Test Script for RAG Question Answering System
Run this after starting the server to validate functionality
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Health check passed")
        print(f"   Status: {data['status']}")
        print(f"   Documents indexed: {data['documents_indexed']}")
        print(f"   Total chunks: {data['total_chunks']}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_document_upload():
    """Test document upload"""
    print_section("Testing Document Upload")
    
    # Create a test document
    test_content = """
    Artificial Intelligence Overview
    
    Artificial Intelligence (AI) is the simulation of human intelligence processes by machines,
    especially computer systems. These processes include learning (the acquisition of information 
    and rules for using the information), reasoning (using rules to reach approximate or definite 
    conclusions) and self-correction.
    
    Machine Learning is a subset of AI that provides systems the ability to automatically learn 
    and improve from experience without being explicitly programmed. Machine learning focuses on 
    the development of computer programs that can access data and use it to learn for themselves.
    
    Deep Learning is a subset of machine learning that uses neural networks with multiple layers.
    These neural networks attempt to simulate the behavior of the human brain—albeit far from 
    matching its ability—allowing it to "learn" from large amounts of data.
    
    Natural Language Processing (NLP) is a branch of AI that helps computers understand, interpret 
    and manipulate human language. NLP draws from many disciplines, including computer science and 
    computational linguistics, in its pursuit to fill the gap between human communication and 
    computer understanding.
    """
    
    # Save to file
    with open("test_document.txt", "w") as f:
        f.write(test_content)
    
    # Upload
    with open("test_document.txt", "rb") as f:
        files = {"file": ("test_document.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Document upload successful")
        print(f"   Document ID: {data['document_id']}")
        print(f"   Filename: {data['filename']}")
        print(f"   Status: {data['status']}")
        print("\n   ⏳ Waiting 3 seconds for background processing...")
        time.sleep(3)
        return data['document_id']
    else:
        print(f"❌ Document upload failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_query(query_text):
    """Test querying documents"""
    print(f"\n🔍 Query: '{query_text}'")
    
    payload = {
        "question": query_text,
        "top_k": 3
    }
    
    response = requests.post(
        f"{BASE_URL}/query",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Query successful")
        print(f"\n   📝 Answer:")
        print(f"   {data['answer'][:200]}...")
        print(f"\n   📊 Metrics:")
        print(f"   - Confidence: {data['confidence_score']:.2f}")
        print(f"   - Retrieval time: {data['retrieval_time_ms']:.2f}ms")
        print(f"   - Generation time: {data['generation_time_ms']:.2f}ms")
        print(f"   - Chunks retrieved: {data['chunks_retrieved']}")
        print(f"\n   📚 Top Source:")
        if data['sources']:
            source = data['sources'][0]
            print(f"   - Document: {source['document']}")
            print(f"   - Similarity: {source['similarity_score']:.4f}")
            print(f"   - Text preview: {source['text'][:100]}...")
        return True
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_queries():
    """Test multiple queries"""
    print_section("Testing Queries")
    
    queries = [
        "What is artificial intelligence?",
        "Explain machine learning",
        "What is the difference between deep learning and machine learning?",
        "What is NLP?",
        "How does natural language processing work?"
    ]
    
    success_count = 0
    for query in queries:
        if test_query(query):
            success_count += 1
        time.sleep(1)  # Small delay between queries
    
    print(f"\n✅ {success_count}/{len(queries)} queries successful")

def test_metrics():
    """Test metrics endpoint"""
    print_section("Testing Metrics")
    
    response = requests.get(f"{BASE_URL}/metrics")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Metrics retrieved successfully")
        print(f"\n   📊 Summary:")
        summary = data['summary']
        print(f"   - Total queries: {summary['total_queries']}")
        print(f"   - Total documents: {summary['total_documents']}")
        print(f"   - Error rate: {summary['error_rate']:.2%}")
        
        if data['query_metrics']['count'] > 0:
            qm = data['query_metrics']
            print(f"\n   ⚡ Query Performance:")
            print(f"   - Avg retrieval time: {qm['avg_retrieval_time_ms']:.2f}ms")
            print(f"   - Avg generation time: {qm['avg_generation_time_ms']:.2f}ms")
            print(f"   - Avg total time: {qm['avg_total_time_ms']:.2f}ms")
            print(f"   - Avg confidence: {qm['avg_confidence']:.2f}")
        
        return True
    else:
        print(f"❌ Metrics retrieval failed: {response.status_code}")
        return False

def test_list_documents():
    """Test listing documents"""
    print_section("Testing Document Listing")
    
    response = requests.get(f"{BASE_URL}/documents")
    
    if response.status_code == 200:
        documents = response.json()
        print(f"✅ Found {len(documents)} document(s)")
        for doc in documents:
            print(f"   - {doc['filename']}: {doc['chunk_count']} chunks")
        return True
    else:
        print(f"❌ Document listing failed: {response.status_code}")
        return False

def test_rate_limiting():
    """Test rate limiting"""
    print_section("Testing Rate Limiting")
    
    print("🔄 Sending 12 rapid requests (limit is 10)...")
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(12):
        response = requests.post(
            f"{BASE_URL}/query",
            json={"question": f"Test query {i}"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
            print(f"   ⚠️  Request {i+1} rate limited (expected)")
    
    print(f"\n   ✅ Successful: {success_count}")
    print(f"   ⚠️  Rate limited: {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("✅ Rate limiting working correctly")
        return True
    else:
        print("⚠️  Rate limiting may not be working")
        return False

def main():
    """Run all tests"""
    print("\n" + "🚀 RAG System Test Suite".center(60))
    print("="*60)
    
    try:
        # Test 1: Health check
        if not test_health_check():
            print("\n❌ Server not responding. Is it running?")
            return
        
        # Test 2: Document upload
        doc_id = test_document_upload()
        if not doc_id:
            print("\n❌ Document upload failed. Cannot continue tests.")
            return
        
        # Test 3: Multiple queries
        test_queries()
        
        # Test 4: Metrics
        test_metrics()
        
        # Test 5: List documents
        test_list_documents()
        
        # Test 6: Rate limiting
        test_rate_limiting()
        
        # Final summary
        print_section("Test Summary")
        print("✅ All tests completed!")
        print("\n📝 Next steps:")
        print("   1. Check the API documentation: http://localhost:8000/docs")
        print("   2. Upload your own documents")
        print("   3. Try different types of queries")
        print("   4. Monitor metrics at /metrics endpoint")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server at", BASE_URL)
        print("   Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    main()
