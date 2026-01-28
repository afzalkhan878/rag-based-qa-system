# RAG System Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │   Web    │  │  Mobile  │  │   CLI    │  │   API    │              │
│  │ Browser  │  │   App    │  │  Client  │  │ Consumer │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │             │                       │
│       └─────────────┴─────────────┴─────────────┘                       │
│                           │                                              │
│                    HTTP/REST API                                         │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                                │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                      FastAPI Application                           │ │
│  │  ┌────────────────────────────────────────────────────────────┐  │ │
│  │  │            Middleware & Security Layer                      │  │ │
│  │  │  • CORS          • Rate Limiter      • Request Validator   │  │ │
│  │  │  • Logging       • Error Handler     • Metrics Collector   │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  │                                                                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │ │
│  │  │   /upload   │  │   /query    │  │  /metrics   │             │ │
│  │  │             │  │             │  │             │             │ │
│  │  │  • Validate │  │  • Validate │  │  • Get      │             │ │
│  │  │  • Queue    │  │  • Retrieve │  │    Stats    │             │ │
│  │  │  • Return   │  │  • Generate │  │  • Return   │             │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │ │
│  └─────────┼─────────────────┼─────────────────┼────────────────────┘ │
└────────────┼─────────────────┼─────────────────┼──────────────────────┘
             │                 │                 │
             ▼                 │                 ▼
    ┌─────────────────┐       │         ┌─────────────────┐
    │ Background Task │       │         │ Metrics Tracker │
    │     Queue       │       │         │                 │
    └────────┬────────┘       │         │  • Query Stats  │
             │                 │         │  • Doc Stats    │
             │                 │         │  • Errors       │
             ▼                 │         └─────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│                       PROCESSING LAYER                                   │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Document Processing Pipeline                   │  │
│  │                                                                    │  │
│  │  1. Extract Text      2. Clean Text       3. Chunk Text          │  │
│  │  ┌──────────┐         ┌──────────┐        ┌──────────┐          │  │
│  │  │   PDF    │────────▶│ Remove   │───────▶│ Sentence │          │  │
│  │  │   TXT    │         │ Noise    │        │ Boundary │          │  │
│  │  │ Parser   │         │ Normalize│        │ Chunking │          │  │
│  │  └──────────┘         └──────────┘        └─────┬────┘          │  │
│  │                                                  │                │  │
│  │                                                  ▼                │  │
│  │                                           ┌──────────┐            │  │
│  │                                           │ Chunks   │            │  │
│  │                                           │ ~512 tok │            │  │
│  │                                           │ 128 ovlp │            │  │
│  │                                           └─────┬────┘            │  │
│  └────────────────────────────────────────────────┼──────────────────┘  │
│                                                    │                     │
│                                                    ▼                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Retrieval Processing Pipeline                  │  │
│  │                                                                    │  │
│  │  1. Embed Query       2. Search Index      3. Rank Results       │  │
│  │  ┌──────────┐         ┌──────────┐        ┌──────────┐          │  │
│  │  │ Sentence │────────▶│  FAISS   │───────▶│ Filter   │          │  │
│  │  │Transform │         │ Cosine   │        │ Threshold│          │  │
│  │  │  Model   │         │Similarity│        │ Top-K    │          │  │
│  │  └──────────┘         └──────────┘        └─────┬────┘          │  │
│  │                                                  │                │  │
│  │                                                  ▼                │  │
│  │                                           ┌──────────┐            │  │
│  │                                           │ Relevant │            │  │
│  │                                           │  Chunks  │            │  │
│  │                                           └─────┬────┘            │  │
│  └────────────────────────────────────────────────┼──────────────────┘  │
└────────────────────────────────────────────────────┼────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           AI/ML LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Embedding Service                              │  │
│  │                                                                    │  │
│  │  Model: all-MiniLM-L6-v2                                          │  │
│  │  • Sentence-Transformers                                          │  │
│  │  • 384-dimensional vectors                                        │  │
│  │  • Normalized for cosine similarity                               │  │
│  │  • ~90MB model size                                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Answer Generator                               │  │
│  │                                                                    │  │
│  │  Model: deepset/roberta-base-squad2                               │  │
│  │  • Question Answering model                                       │  │
│  │  • Trained on SQuAD 2.0                                           │  │
│  │  • Extracts answer from context                                   │  │
│  │  • Provides confidence score                                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          STORAGE LAYER                                   │
│                                                                           │
│  ┌───────────────────────────┐      ┌───────────────────────────┐      │
│  │     Vector Store (FAISS)   │      │    Metadata Store         │      │
│  │                            │      │                           │      │
│  │  • IndexFlatIP             │◀────▶│  • Chunks                 │      │
│  │  • Cosine Similarity       │      │  • Document Map           │      │
│  │  • ~384 dimensions         │      │  • Persisted (pickle)     │      │
│  │  • In-memory + disk        │      │                           │      │
│  │                            │      │                           │      │
│  │  Files:                    │      │  Files:                   │      │
│  │  • faiss_index.bin         │      │  • metadata.pkl           │      │
│  └───────────────────────────┘      └───────────────────────────┘      │
└───────────────────────────────────────────────────────────────────────┘


## Data Flow Diagrams

### Upload Flow
```
User Upload → Validate File → Background Queue → Extract Text → 
Chunk Text → Generate Embeddings → Store in FAISS → Update Metadata → 
Persist to Disk
```

### Query Flow
```
User Query → Rate Limit Check → Validate Input → Generate Query Embedding → 
Search FAISS Index → Retrieve Top-K Chunks → Filter by Threshold → 
Generate Answer → Calculate Confidence → Track Metrics → Return Response
```

## Component Details

### 1. Document Processor
- **Input**: PDF, TXT files
- **Processing**: Text extraction, cleaning, chunking
- **Output**: List of text chunks with metadata
- **Key Parameters**: chunk_size=2048, overlap=512

### 2. Embedding Service
- **Model**: all-MiniLM-L6-v2
- **Input**: Text strings
- **Output**: 384-dimensional vectors
- **Normalization**: L2 normalized for cosine similarity

### 3. Vector Store
- **Engine**: FAISS IndexFlatIP
- **Similarity**: Cosine similarity (inner product on normalized vectors)
- **Persistence**: Saves index and metadata to disk
- **Operations**: Add, Search, Delete

### 4. Retrieval Service
- **Input**: Query string
- **Process**: Embed query → Search index → Filter by threshold
- **Output**: Top-K most similar chunks with scores

### 5. Answer Generator
- **Model**: RoBERTa-base fine-tuned on SQuAD 2.0
- **Input**: Question + Context chunks
- **Output**: Answer + Confidence score
- **Fallback**: Extractive approach if model unavailable

### 6. Rate Limiter
- **Algorithm**: Token Bucket
- **Default**: 10 requests per 60 seconds
- **Scope**: Per user_id
- **Storage**: In-memory dictionary

### 7. Metrics Tracker
- **Tracked Metrics**:
  - Query latency (retrieval, generation, total)
  - Similarity scores
  - Document processing time
  - Error rates
- **Aggregations**: Mean, median, percentiles (P50, P95, P99)

## Key Design Decisions

1. **FAISS IndexFlatIP**: Fast exact search, no approximation
2. **Normalized Embeddings**: Enables cosine similarity via inner product
3. **Background Processing**: Non-blocking document ingestion
4. **Persistent Storage**: Survives server restarts
5. **Comprehensive Metrics**: Enable monitoring and optimization

## Scalability Considerations

### Current Capacity
- Documents: ~1,000
- Chunks: ~40,000
- Queries/sec: 10-15

### Scaling Strategy
- **10K documents**: Implement query caching
- **100K+ documents**: Switch to approximate index (IVF, HNSW)
- **High QPS**: Horizontal scaling with load balancer
- **Large files**: Implement streaming processing

## Security & Performance

### Security
- File size limit: 10MB
- File type validation: PDF, TXT only
- Rate limiting per user
- Input validation with Pydantic

### Performance Optimizations
- Normalized embeddings (faster similarity)
- Background processing (non-blocking)
- Efficient chunking (sentence boundaries)
- FAISS C++ backend (fast search)
```
