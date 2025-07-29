from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from core.models import Document
from core.text_replace import TextReplacer
from core.search import SearchEngine
from core.document_store import DocumentStore
import uuid
from datetime import datetime
import uvicorn

app = FastAPI(
    title="Document Redlining API",
    description="A clean, RESTful API for document management with advanced text redlining capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class CreateDocumentRequest(BaseModel):
    title: str = Field(..., description="Document title")
    text: str = Field(..., description="Document content")

class CreateDocumentResponse(BaseModel):
    id: str = Field(..., description="Document UUID")
    version: int = Field(..., description="Document version")
    created_at: str = Field(..., description="Creation timestamp")



# Range-based replacement - specify exact character positions
class Range(BaseModel):
    start: int = Field(..., description="Start position (inclusive)")
    end: int = Field(..., description="End position (exclusive)")

class RangeRedlineRequest(BaseModel):
    document_id: str = Field(..., description="Document UUID")
    range: Range = Field(..., description="Range specification with start and end positions")
    replacement: str = Field(..., description="Replacement text")

class TargetRedlineRequest(BaseModel):
    document_id: str = Field(..., description="Document UUID")
    target_text: str = Field(..., description="Text to find and replace")
    replacement: str = Field(..., description="Replacement text")
    occurrence: int = Field(1, description="Which occurrence to replace (default: 1)")

class BatchRangeRedlineRequest(BaseModel):
    documents: List[RangeRedlineRequest] = Field(..., description="List of documents to redline with ranges")

class BatchTargetRedlineRequest(BaseModel):
    documents: List[TargetRedlineRequest] = Field(..., description="List of documents to redline with targets")

class DocumentSummary(BaseModel):
    id: str = Field(..., description="Document UUID")
    version: int = Field(..., description="Document version")
    
class SkippedDocument(BaseModel):
    document: str = Field(..., description="Document UUID that was skipped")
    reason: str = Field(..., description="Reason for skipping (not_found, version_conflict)")

class RedlineResponse(BaseModel):
    documents: List[DocumentSummary] = Field(..., description="Results for each successfully redlined document")
    skipped: List[SkippedDocument] = Field(default=[], description="Documents that were skipped")

class DocumentResponse(BaseModel):
    id: str = Field(..., description="Document UUID")
    title: str = Field(..., description="Document title")
    text: str = Field(..., description="Document content")
    version: int = Field(..., description="Document version")

class SearchResult(BaseModel):
    document_id: str = Field(..., description="Document ID")
    context: str = Field(..., description="Context around the match")
    position: int = Field(..., description="Position of the match")

class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(..., description="Search results")

# Initialize core components
# You can configure these via environment variables
import os
bucket_name = os.getenv('GCS_BUCKET_NAME', 'document-redlining-bucket')
project_id = os.getenv('GCS_PROJECT_ID', None)

document_store = DocumentStore(bucket_name=bucket_name, project_id=project_id)
text_replacer = TextReplacer()
search_engine = SearchEngine(document_store)

@app.post("/documents", response_model=CreateDocumentResponse, status_code=201)
async def create_document(request: CreateDocumentRequest):
    """Upload / Create Document"""
    try:
        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            title=request.title,
            text=request.text,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        document_store.save(document)
        
        # Rebuild search index after adding new document
        search_engine.rebuild_index()
        
        return CreateDocumentResponse(
            id=doc_id,
            version=1,
            created_at=document.created_at.isoformat() + 'Z'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/documents/redline/range", response_model=RedlineResponse)
async def redline_documents_by_range(request: BatchRangeRedlineRequest):
    """Redline documents by character range"""
    try:
        results = []
        skipped = []
        
        # Process each document with proper locking
        for doc_request in request.documents:
            # Check if document exists first (without locking)
            if not document_store.exists(doc_request.document_id):
                skipped.append(SkippedDocument(
                    document=doc_request.document_id,
                    reason="not_found"
                ))
                continue
            
            # Lock the document and get it
            try:
                with document_store.lock_manager.lock_document(doc_request.document_id):
                    document = document_store.get_without_lock(doc_request.document_id)
                    if not document:
                        skipped.append(SkippedDocument(
                            document=doc_request.document_id,
                            reason="not_found"
                        ))
                        continue
                    

                    
                    # Create change dict for text replacer
                    change_dict = {
                        'operation': 'replace',
                        'range': doc_request.range.dict(),
                        'text': doc_request.replacement
                    }
                    
                    # Apply changes
                    updated_text = text_replacer.apply_changes(document.text, [change_dict])
                    
                    # Update document
                    document.text = updated_text
                    document.version += 1
                    document.updated_at = datetime.utcnow()
                    
                    # Save the document (still within the lock)
                    document_store.save_without_lock(document)
                    
                    # Add to results
                    results.append(DocumentSummary(
                        id=document.id,
                        version=document.version
                    ))
                    
            except Exception as e:
                # If processing fails, skip the document
                skipped.append(SkippedDocument(
                    document=doc_request.document_id,
                    reason="processing_error"
                ))
        
        # Rebuild search index after redlining documents
        if results:
            search_engine.rebuild_index()
        
        return RedlineResponse(
            documents=results,
            skipped=skipped
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/documents/redline/target", response_model=RedlineResponse)
async def redline_documents_by_target(request: BatchTargetRedlineRequest):
    """Redline documents by target text"""
    try:
        results = []
        skipped = []
        
        # Process each document with proper locking
        for doc_request in request.documents:
            # Check if document exists first (without locking)
            if not document_store.exists(doc_request.document_id):
                skipped.append(SkippedDocument(
                    document=doc_request.document_id,
                    reason="not_found"
                ))
                continue
            
            # Lock the document and get it
            try:
                with document_store.lock_manager.lock_document(doc_request.document_id):
                    document = document_store.get_without_lock(doc_request.document_id)
                    if not document:
                        skipped.append(SkippedDocument(
                            document=doc_request.document_id,
                            reason="not_found"
                        ))
                        continue
                    
                    # Create change dict for text replacer
                    change_dict = {
                        'operation': 'replace',
                        'target': {
                            'text': doc_request.target_text,
                            'occurrence': doc_request.occurrence
                        },
                        'replacement': doc_request.replacement
                    }
                    
                    # Apply changes
                    updated_text = text_replacer.apply_changes(document.text, [change_dict])
                    
                    # Update document
                    document.text = updated_text
                    document.version += 1
                    document.updated_at = datetime.utcnow()
                    
                    # Save the document (still within the lock)
                    document_store.save_without_lock(document)
                    
                    # Add to results
                    results.append(DocumentSummary(
                        id=document.id,
                        version=document.version
                    ))
                    
            except Exception as e:
                # If processing fails, skip the document
                skipped.append(SkippedDocument(
                    document=doc_request.document_id,
                    reason="processing_error"
                ))
        
        # Rebuild search index after redlining documents
        if results:
            search_engine.rebuild_index()
        
        return RedlineResponse(
            documents=results,
            skipped=skipped
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/search", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip"),
    buffer: int = Query(50, description="Number of characters to show around each match")
):
    """Global Search"""
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Missing query parameter: q")
        results = search_engine.search_all(q, limit, offset, buffer)
        
        # Convert to Pydantic models
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                document_id=result['document_id'],
                context=result['context'],
                position=result['position']
            ))
        
        return SearchResponse(results=search_results)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}/search", response_model=SearchResponse)
async def document_search(
    doc_id: str,
    q: str = Query(..., description="Search query"),
    buffer: int = Query(50, description="Number of characters to show around each match")
):
    """Search Within Document"""
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Missing query parameter: q")
        
        document = document_store.get_without_lock(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        results = search_engine.search_document(document, q, buffer)
        
        # Convert to Pydantic models
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                document_id=result['document_id'],
                context=result['context'],
                position=result['position']
            ))
        
        return SearchResponse(results=search_results)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Full Document Retrieval"""
    try:
        document = document_store.get(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            text=document.text,
            version=document.version
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/documents", response_model=List[str])
async def get_all_document_ids():
    """Get all document IDs"""
    try:
        documents = document_store.get_all()
        return [doc.id for doc in documents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Document Redlining API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000) 