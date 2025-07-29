# Document Redlining API

A robust, scalable document management system with advanced text redlining capabilities, built with FastAPI and Google Cloud Storage.

## 🚀 Features

- **Document Management**: Upload, retrieve, and manage documents with version control
- **Advanced Redlining**: Two redlining modes - range-based and target-based text replacement
- **Full-Text Search**: Powered by Whoosh with configurable context buffers
- **Concurrent Safety**: Hierarchical locking system prevents deadlocks
- **Cloud Storage**: Google Cloud Storage integration for scalable persistence
- **RESTful API**: Clean, intuitive API design with comprehensive documentation
- **Web Interface**: Beautiful legal pad-themed frontend for easy interaction

## 🏗️ Architecture

### Core Components

1. **Document Store** (`core/document_store.py`)
   - Google Cloud Storage integration
   - RAII-style hierarchical locking
   - Concurrent access safety

2. **Text Replacer** (`core/text_replace.py`)
   - Range-based text replacement
   - Target-based text replacement with occurrence control
   - Batch operation support

3. **Search Engine** (`core/search.py`)
   - Whoosh-based full-text indexing
   - Lazy index building
   - Configurable context extraction

4. **API Layer** (`main.py`)
   - FastAPI REST endpoints
   - Pydantic validation
   - CORS support

## 📋 Prerequisites

- Python 3.8+
- Google Cloud Platform account
- Google Cloud Storage bucket
- Google Cloud credentials

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fullStack
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google Cloud credentials**
   ```bash
   # Option 1: Set environment variable
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   
   # Option 2: Use gcloud CLI
   gcloud auth application-default login
   ```

5. **Configure environment variables**
   ```bash
   export GCS_BUCKET_NAME="your-bucket-name"
   export GCS_PROJECT_ID="your-project-id"  # Optional, uses default if not set
   ```

## 🚀 Quick Start

1. **Start the API server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 5000
   ```

2. **Open the frontend**
   - Open `index.html` in your browser
   - Or serve it with a simple HTTP server:
     ```bash
     python -m http.server 8000
     ```

3. **Access API documentation**
   - Swagger UI: http://localhost:5000/docs
   - ReDoc: http://localhost:5000/redoc

## 📚 API Usage Examples

### Create a Document
```bash
curl -X POST "http://localhost:5000/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Legal Contract",
    "text": "This agreement is between Party A and Party B."
  }'
```

### Get a Document
```bash
curl -X GET "http://localhost:5000/documents/{document_id}"
```

### Redline by Range
```bash
curl -X PATCH "http://localhost:5000/documents/redline/range" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{
      "document_id": "your-doc-id",
      "range": {
        "start": 10,
        "end": 15
      },
      "replacement": "amended"
    }]
  }'
```

### Redline by Target
```bash
curl -X PATCH "http://localhost:5000/documents/redline/target" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{
      "document_id": "your-doc-id",
      "target_text": "agreement",
      "occurrence": 1,
      "replacement": "contract"
    }]
  }'
```

### Global Search
```bash
curl -X GET "http://localhost:5000/documents/search?q=contract&limit=10&buffer=50"
```

### Document-Specific Search
```bash
curl -X GET "http://localhost:5000/documents/{doc_id}/search?q=contract&buffer=50"
```

### Get All Document IDs
```bash
curl -X GET "http://localhost:5000/documents"
```

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests
python -m pytest tests/test_text_replace.py -v
python -m pytest tests/test_search.py -v

# Integration tests
python -m pytest tests/test_api_integration.py -v
```

### Performance Tests
```bash
# Large file performance test
python -m pytest tests/test_text_replace.py::TestTextReplacer::test_large_text_performance -v

# Search performance test
python -m pytest tests/test_search.py::TestSearchEngine::test_search_performance_large_documents -v
```

## 📊 Performance Considerations

### Text Replacement Performance
- **Range-based replacement**: O(1) - Direct string slicing
- **Target-based replacement**: O(n) - Linear search through text
- **Large documents**: Optimized for documents up to 1MB
- **Batch operations**: Sequential processing with automatic index rebuilding

### Search Performance
- **Index building**: O(n) where n is total document size
- **Search queries**: O(log n) with Whoosh indexing
- **Context extraction**: O(1) for buffer-based context
- **Memory usage**: Temporary index files cleaned up automatically

### Concurrency Performance
- **Lock acquisition**: ~100ms average with GCS
- **Lock timeout**: 5 minutes default, configurable
- **Hierarchical locking**: Prevents deadlocks in batch operations
- **Lock stealing**: Automatic cleanup of expired locks

### Scalability Limits
- **Document size**: Recommended < 1MB per document
- **Concurrent users**: Limited by GCS rate limits (~1000 requests/second)
- **Total documents**: Limited by GCS bucket size
- **Search index**: Temporary, rebuilt on demand

## 🔒 Security Considerations

### Authentication & Authorization
- Currently relies on GCS bucket permissions
- No built-in user authentication
- CORS configured for development (should be restricted in production)

### Data Protection
- Documents stored in GCS with standard encryption
- Lock files contain minimal metadata
- No sensitive data in logs

### Production Recommendations
- Implement proper authentication (OAuth2, JWT)
- Restrict CORS origins to your frontend domain
- Use HTTPS in production
- Implement rate limiting
- Add request logging and monitoring

## 🏛️ API Design Rationale

### RESTful Design Principles
- **Resource-based URLs**: `/documents/{id}` for document operations
- **HTTP methods**: POST for creation, PATCH for updates, GET for retrieval
- **Stateless operations**: Each request contains all necessary information
- **Consistent response format**: Standardized JSON responses with error handling

### Redlining Strategy
**Why two separate endpoints?**
- **Range-based** (`/redline/range`): Precise control for legal document editing
- **Target-based** (`/redline/target`): Semantic editing for content changes
- **Separation of concerns**: Different use cases, different validation rules
- **Type safety**: Pydantic models prevent invalid operations

### Concurrency Control
**Why hierarchical locking?**
- **Deadlock prevention**: Consistent lock ordering eliminates deadlocks
- **RAII pattern**: Automatic resource cleanup prevents lock leaks
- **Distributed safety**: GCS-based locks work across multiple server instances
- **Timeout handling**: Prevents indefinite blocking

### Search Architecture
**Why Whoosh + GCS?**
- **Whoosh**: Pure Python, no external dependencies, excellent full-text search
- **GCS**: Scalable, reliable, cost-effective storage
- **Lazy indexing**: Build index on demand, no upfront cost
- **Temporary storage**: Index files cleaned up automatically

### Batch Operations
**Why batch redlining?**
- **Efficiency**: Single API call for multiple documents
- **Atomicity**: All-or-nothing semantics for related changes
- **Error handling**: Detailed reporting of successes and failures
- **Performance**: Reduced network overhead

## 🔧 Configuration

### Environment Variables
```bash
# Required
GCS_BUCKET_NAME=your-bucket-name

# Optional
GCS_PROJECT_ID=your-project-id  # Uses default if not set
```

### GCS Bucket Setup
```bash
# Create bucket
gsutil mb gs://your-bucket-name

# Set permissions (if needed)
gsutil iam ch allUsers:objectViewer gs://your-bucket-name
```

### Performance Tuning
```python
# In main.py, adjust these values based on your needs:
LOCK_TIMEOUT = 300  # 5 minutes
SEARCH_BUFFER_DEFAULT = 50  # characters
SEARCH_LIMIT_DEFAULT = 10  # results
```

## 🐛 Troubleshooting

### Common Issues

**"Document not found" errors**
- Check if document ID exists in GCS bucket
- Verify GCS credentials and permissions
- Check bucket name configuration

**Lock acquisition failures**
- Increase lock timeout if operations are slow
- Check GCS network connectivity
- Verify bucket permissions

**Search returning no results**
- Index may need rebuilding (automatic on document changes)
- Check if search terms exist in documents
- Verify search query format

**Performance issues**
- Monitor GCS request rates
- Consider document size limits
- Check network latency to GCS

### Debug Mode
```bash
# Enable debug logging
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
uvicorn main:app --log-level debug
```

## 📈 Monitoring & Metrics

### Key Metrics to Monitor
- **API response times**: Target < 500ms for most operations
- **GCS request rates**: Stay within quota limits
- **Lock acquisition times**: Should be < 1 second
- **Search performance**: Index rebuild times
- **Error rates**: 4xx and 5xx responses

### Logging
- Application logs include operation timing
- GCS errors are logged with details
- Lock operations are logged for debugging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Open an issue with detailed error information
4. Include environment details and reproduction steps 