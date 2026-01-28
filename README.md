<h1 align="center">🚀 RAG-Based Question Answering System</h1>

<p align="center">
<b>A clean, production-style Retrieval-Augmented Generation (RAG) system</b><br>
Built with FastAPI, FAISS, and Transformer embeddings
</p>

<hr>

## 🎯 Objective

The objective of this project is to design and implement an **applied AI system** that allows users to upload documents and ask questions whose answers are generated using a **Retrieval-Augmented Generation (RAG)** approach.

The system demonstrates practical use of **embeddings, vector similarity search, background jobs, and APIs**, while maintaining transparency and explainability.

---

## 🧠 What is RAG?

**Retrieval-Augmented Generation (RAG)** combines:

- 🔍 **Information Retrieval** (finding relevant document chunks)
- 🤖 **Answer Generation** (using retrieved context)

Instead of relying on parametric memory alone, the system grounds answers in **actual uploaded documents**, reducing hallucinations.

---

## ✨ Key Features

<ul>
  <li>📄 Upload <b>PDF</b> and <b>TXT</b> documents</li>
  <li>✂️ Intelligent chunking with overlap</li>
  <li>🧠 Semantic similarity search using <b>FAISS</b></li>
  <li>🤖 Context-aware question answering</li>
  <li>⚡ Background document ingestion</li>
  <li>🛡 Request validation and rate limiting</li>
</ul>

---

## 🏗 System Architecture

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

📌 See <b>architecture_diagram.png</b> for a visual diagram.

---

## ✂️ Chunking Strategy

<pre style="background-color:#FCF3CF; padding:15px; border-radius:8px;">
Chunk Size   : ~2048 characters
Chunk Overlap: ~512 characters
</pre>

### Why this chunk size?

- Preserves semantic coherence
- Avoids breaking important concepts
- Balances context size and retrieval precision
- Aligns with embedding model limitations

This strategy improves retrieval quality while maintaining performance.

---

## ❌ Retrieval Failure Case

<pre style="background-color:#FADBD8; padding:15px; border-radius:8px;">
Query:
"How do you prevent overfitting in neural networks?"

Observed Failure:
The retrieved document only explained what overfitting is,
but did not include prevention techniques.
</pre>

### Insight

Semantic similarity alone does not guarantee **intent satisfaction**.
This highlights the limitation of retrieval-only approaches and motivates future improvements such as intent-aware retrieval.

---

## 📊 Metric Tracked

<pre style="background-color:#E8F8F5; padding:15px; border-radius:8px;">
Metric: Query Latency (milliseconds)

Why?
- Directly affects user experience
- Indicates system scalability
- Easy to measure and optimize
</pre>

Latency includes:

- Query embedding generation
- Vector similarity search
- Answer construction

---

## ⚙️ Technical Stack

| Layer           | Technology                 |
| --------------- | -------------------------- |
| API Framework   | FastAPI                    |
| Embeddings      | sentence-transformers      |
| Vector Store    | FAISS                      |
| LLM             | F-LAN T5 QA Transformer |
| Validation      | Pydantic                   |
| Background Jobs | FastAPI BackgroundTasks    |
| Rate Limiting   | Custom in-memory limiter   |

---
<p> <b>For answer generation, the system uses a lightweight open-source Large Language Model (FLAN-T5) to generate coherent, context-aware, and human-readable answers from the retrieved document chunks.</b> </p>
## 🔌 API Endpoints

<pre style="background-color:#EBF5FB; padding:15px; border-radius:8px;">
POST /upload   → Upload PDF or TXT document
POST /query    → Ask a question
GET  /health   → System health check
</pre>

---

## ⚙️ Setup & Usage

<pre style="background-color:#1C2833; color:#ECF0F1; padding:15px; border-radius:8px;">
git clone https://github.com/afzalkhan878/rag-based-qa-system.git
cd rag-based-qa-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
</pre>

📍 Swagger UI: http://localhost:8000/docs
📍 Health Check: http://localhost:8000/health

---

## 🛡 Rate Limiting & Validation

- Requests are validated using **Pydantic models**
- A basic **rate limiter** restricts excessive API usage
- Ensures system stability and fair access

---

## 📌 Assignment Requirement Mapping

<ul>
  <li><b>Document Upload:</b> Supports PDF and TXT formats</li>
  <li><b>Chunking:</b> Semantic chunking with overlap</li>
  <li><b>Vector Store:</b> FAISS-based local storage</li>
  <li><b>Retrieval:</b> Cosine similarity over embeddings</li>
  <li><b>Answer Generation:</b> Transformer-based LLM</li>
  <li><b>Background Jobs:</b> FastAPI BackgroundTasks</li>
  <li><b>Validation:</b> Pydantic request models</li>
  <li><b>Rate Limiting:</b> Custom in-memory limiter</li>
</ul>

---

## ⚠️ Known Limitations

<ul>
  <li>Answer quality depends on document coverage</li>
  <li>No explicit intent classification (definition vs how-to)</li>
  <li>Local vector store is not distributed</li>
</ul>

---

## 🚀 Future Improvements

<ul>
  <li>Intent-aware retrieval</li>
  <li>Cross-encoder re-ranking</li>
  <li>Persistent vector databases</li>
  <li>Plug-in support for external LLMs (OpenAI / Ollama)</li>
</ul>

---

## 🎯 Conclusion

This project delivers a **complete, explainable, and modular RAG-based Question Answering system**.
It demonstrates strong understanding of **chunking strategy, retrieval quality, API design, and metrics awareness**, while intentionally avoiding heavy frameworks for transparency.

---

<p align="center">
<b>Author:</b> Md Afzal Khan<br>
B.Tech CSE (Data Science), Amity University
</p>
