# Document Redlining API

A robust, scalable document management system with advanced text redlining capabilities, built with FastAPI and Google Cloud Storage.

##  Quickstart!

in this directory.
RUN:
pythom -m venv venv
pip install -r requirements.txt
venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 5000

Open index.html(in this directory) with a browser(preferably chrome)

RUN TESTS:
python -m pytest tests/ -v

## 🚀 Features

- **Document Management**: Upload, retrieve, and manage documents with version control
- **Advanced Redlining**: Two redlining modes - range-based and target-based text replacement
- **Full-Text Search**: Powered by Whoosh with configurable context buffers
- **Concurrent Safety**: Hierarchical locking system prevents deadlocks
- **Cloud Storage**: Google Cloud Storage integration for scalable persistence
- **RESTful API**: Clean, intuitive API design with comprehensive documentation
- **Web Interface**: Legal pad-themed frontend for easy interaction

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

### Append to a Document
```bash
curl -X PATCH "http://localhost:5000/documents/{document_id}/append" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This text will be appended to the end of the document."
  }'
```

### Delete a Document
```bash
curl -X DELETE "http://localhost:5000/documents/{document_id}"
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
- **Range-based** (`/redline/range`