"""
REST API for Advanced RAG System
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_system import AdvancedRAGSystem
import os
import time

app = Flask(__name__)
CORS(app)

# Initialize RAG system
rag_system = AdvancedRAGSystem()

# In-memory store for tracking
request_log = []


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })


@app.route('/ingest', methods=['POST'])
def ingest_documents():
    """
    Ingest documents into the RAG system.

    Request body:
    {
        "documents": [
            {"id": "doc1", "text": "..."},
            {"id": "doc2", "text": "..."}
        ]
    }
    """
    try:
        data = request.get_json()

        if 'documents' not in data:
            return jsonify({'error': 'Missing documents field'}), 400

        documents = data['documents']

        # Validate documents
        for doc in documents:
            if 'id' not in doc or 'text' not in doc:
                return jsonify({'error': 'Each document must have id and text'}), 400

        start_time = time.time()
        num_chunks = rag_system.ingest_documents(documents)
        ingest_time = time.time() - start_time

        return jsonify({
            'success': True,
            'num_documents': len(documents),
            'num_chunks_created': num_chunks,
            'ingest_time_seconds': ingest_time
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def query():
    """
    Query the RAG system.

    Request body:
    {
        "query": "your question here",
        "top_k": 5,  # optional, default 5
        "return_metrics": true  # optional, default true
    }
    """
    try:
        data = request.get_json()

        if 'query' not in data:
            return jsonify({'error': 'Missing query field'}), 400

        query_text = data['query']
        top_k = data.get('top_k', 5)
        return_metrics = data.get('return_metrics', True)

        # Execute query
        result = rag_system.query(
            query_text,
            top_k=top_k,
            return_metrics=return_metrics
        )

        # Log request
        request_log.append({
            'timestamp': time.time(),
            'query': query_text,
            'top_k': top_k,
            'num_results': result['num_results']
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system-wide metrics"""
    try:
        metrics_summary = rag_system.get_metrics_summary()

        return jsonify({
            'system_metrics': metrics_summary,
            'total_requests': len(request_log),
            'recent_queries': request_log[-10:]  # Last 10 queries
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chunking-info', methods=['GET'])
def chunking_info():
    """Get information about the chunking strategy"""
    return jsonify({
        'strategy': 'Semantic Chunking with Adaptive Sizing',
        'parameters': {
            'target_chunk_size': rag_system.chunker.target_chunk_size,
            'min_chunk_size': rag_system.chunker.min_chunk_size,
            'max_chunk_size': rag_system.chunker.max_chunk_size,
            'overlap_tokens': rag_system.chunker.overlap_tokens
        },
        'description': """
        Uses semantic boundaries (sentences) with dynamic sizing based on content density.
        High-density content gets smaller chunks for precision, low-density gets larger chunks.
        Includes overlapping windows to maintain context across boundaries.
        """
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
