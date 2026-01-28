<h1 align="center">🚀 RAG-Based Question Answering System</h1>

<p align="center">
<b>A clean, production-style Retrieval-Augmented Generation (RAG) system</b><br>
Built with FastAPI, FAISS, and Transformer embeddings
</p>

<hr>

<h2 style="color:#2E86C1;">✨ Key Features</h2>

<ul>
  <li>📄 Upload PDF and TXT documents</li>
  <li>✂️ Intelligent chunking with overlap</li>
  <li>🧠 Semantic search using FAISS</li>
  <li>🤖 Context-aware question answering</li>
  <li>⚡ Background document ingestion</li>
  <li>🛡 Request validation and rate limiting</li>
</ul>

<hr>

<h2 style="color:#27AE60;">🏗 System Architecture</h2>

<pre style="background-color:#F4F6F6; padding:15px; border-radius:8px;">
User
 │
 ▼
FastAPI API
 │
 ├── Document Upload
 │     ├── Text Extraction
 │     ├── Chunking
 │     ├── Embedding Generation
 │     └── FAISS Vector Store
 │
 └── Query
       ├── Query Embedding
       ├── Similarity Search
       └── Answer Generation
</pre>

<hr>

<h2 style="color:#AF7AC5;">✂️ Chunking Strategy</h2>

<pre style="background-color:#FCF3CF; padding:15px; border-radius:8px;">
Chunk Size   : ~2048 characters
Chunk Overlap: ~512 characters
</pre>

<b>Why?</b>

<ul>
  <li>Preserves semantic meaning</li>
  <li>Avoids breaking important concepts</li>
  <li>Improves retrieval accuracy</li>
</ul>

<hr>

<h2 style="color:#E74C3C;">❌ Retrieval Failure Case</h2>

<pre style="background-color:#FADBD8; padding:15px; border-radius:8px;">
Query:
"How do you prevent overfitting in neural networks?"

Failure:
Document only explained what overfitting is,
not how to prevent it.
</pre>

<b>Lesson:</b> Retrieval relevance ≠ intent satisfaction.

<hr>

<h2 style="color:#1ABC9C;">📊 Metric Tracked</h2>

<pre style="background-color:#E8F8F5; padding:15px; border-radius:8px;">
Metric: Query Latency (ms)

Why?
- Directly impacts UX
- Indicates scalability
- Easy to monitor and optimize
</pre>

<hr>

<h2 style="color:#D68910;">⚙️ Setup Instructions</h2>

<pre style="background-color:#1C2833; color:#ECF0F1; padding:15px; border-radius:8px;">
git clone https://github.com/afzalkhan878/rag-based-qa-system.git
cd rag-based-qa-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
</pre>

<hr>

<h2 style="color:#2980B9;">🔌 API Endpoints</h2>

<pre style="background-color:#EBF5FB; padding:15px; border-radius:8px;">
POST /upload   → Upload documents
POST /query    → Ask questions
GET  /health   → System health
</pre>

<hr>

<h2 style="color:#7D3C98;">🎯 Conclusion</h2>

<p>
This project demonstrates a complete and explainable RAG pipeline with
thoughtful design choices, strong API structure, and measurable performance.
</p>

<hr>

<p align="center">
<b>Author:</b> Md Afzal Khan<br>
B.Tech CSE (Data Science), Amity University
</p>
