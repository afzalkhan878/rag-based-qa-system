# Deployment Guide

## Quick Start with Docker

### 1. Build and Run
```bash
docker-compose up --build
```

The API will be available at `http://localhost:5000`

### 2. Test the Deployment
```bash
# Health check
curl http://localhost:5000/health

# Ingest a document
curl -X POST http://localhost:5000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "test1",
        "text": "This is a test document about machine learning and AI."
      }
    ]
  }'

# Query
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 3
  }'
```

## Production Deployment

### AWS EC2 Deployment

1. **Launch EC2 Instance**
   - Use Ubuntu 22.04 LTS
   - t3.medium or larger (2+ vCPU, 4GB+ RAM)
   - Open port 5000 in security group

2. **Install Dependencies**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker $USER
```

3. **Clone and Deploy**
```bash
git clone <your-repo>
cd advanced-rag-system
docker-compose up -d
```

4. **Setup Nginx Reverse Proxy** (recommended)
```bash
sudo apt install -y nginx

# Create nginx config
sudo tee /etc/nginx/sites-available/rag-api << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/rag-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Google Cloud Run Deployment

1. **Build Container**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/rag-api
```

2. **Deploy**
```bash
gcloud run deploy rag-api \
  --image gcr.io/PROJECT_ID/rag-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi
```

### Heroku Deployment

1. **Create Heroku App**
```bash
heroku create your-rag-app
```

2. **Add Buildpack**
```bash
heroku buildpacks:set heroku/python
```

3. **Create Procfile**
```
web: python api.py
```

4. **Deploy**
```bash
git push heroku main
```

## Local Development Setup

### Without Docker

1. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Run API**
```bash
python api.py
```

4. **Run Tests**
```bash
python test_rag.py
```

## Environment Variables

Create a `.env` file:

```bash
PORT=5000
FLASK_ENV=development
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./chroma_db
```

## Monitoring

### Metrics Endpoint
Monitor system health via `/metrics`:
```bash
curl http://localhost:5000/metrics
```

### Logging
Add logging configuration in `api.py`:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Resource Monitoring
Monitor resource usage:
```bash
docker stats rag-api
```

## Scaling Considerations

### Horizontal Scaling
- Use shared vector store (Milvus, Weaviate)
- Implement Redis caching
- Load balancer (nginx, AWS ALB)

### Vertical Scaling
- Increase memory for larger document sets
- More CPU cores for parallel processing
- SSD storage for ChromaDB

### Optimization
1. Enable query caching
2. Batch document ingestion
3. Use approximate nearest neighbor search
4. Implement connection pooling

## Backup and Recovery

### Backup ChromaDB
```bash
# Create backup
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Restore backup
tar -xzf chroma_backup_20260127.tar.gz
```

## Security

### API Authentication
Add API key authentication:
```python
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/query', methods=['POST'])
@require_api_key
def query():
    # ...
```

### HTTPS
Use Let's Encrypt for SSL:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Troubleshooting

### Issue: Out of Memory
**Solution**: Increase Docker memory limit or use smaller embedding model

### Issue: Slow Queries
**Solution**: 
- Enable caching
- Use approximate search for large datasets
- Profile with `/metrics` endpoint

### Issue: ChromaDB Corruption
**Solution**: Delete and reingest
```bash
rm -rf chroma_db/
python -c "from rag_system import AdvancedRAGSystem; rag = AdvancedRAGSystem()"
```

## Performance Benchmarks

| Scale | Query Time | Memory | Storage |
|-------|-----------|--------|---------|
| 100 docs | 50-100ms | 500MB | 50MB |
| 1K docs | 100-200ms | 1GB | 500MB |
| 10K docs | 200-500ms | 2GB | 5GB |

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/advanced-rag-system
- Documentation: See README.md and EXPLANATION.md
