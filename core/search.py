from typing import List, Dict, Any, Optional
from core.models import Document
from core.document_store import DocumentStore
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.analysis import StandardAnalyzer
import os
import tempfile

class SearchEngine:
    """Search engine using Whoosh for full-text search"""
    
    def __init__(self, document_store: DocumentStore):
        self.document_store = document_store
        self.index_dir = tempfile.mkdtemp()
        self.schema = Schema(
            doc_id=ID(stored=True),
            title=TEXT(stored=True),
            content=TEXT(stored=True)
        )
        self.index = create_in(self.index_dir, self.schema)
        self._index_built = False
    
    def search_all(self, query: str, limit: int = 10, offset: int = 0, buffer: int = 50) -> List[Dict[str, Any]]:
        """
        Search across all documents
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of search results with context
        """
        # Ensure index is built
        if not self._index_built:
            self.rebuild_index()
        
        searcher = self.index.searcher()

        query_parser = QueryParser("content", self.index.schema)
        # Use wildcard search for partial matching
        wildcard_query = f"*{query}*"
        q = query_parser.parse(wildcard_query)

        results = []
        search_results = searcher.search(q, limit=limit + offset)
        # Apply offset
        for result in search_results[offset:]:
            doc_id = result['doc_id']
            document = self.document_store.get_without_lock(doc_id)
            if document:
                # Get context around the match
                context = self._get_context(document.text, query, result.highlights("content"), buffer)
                results.append({
                    'document_id': doc_id,
                    'context': context,
                    'position': result.rank
                })

        searcher.close()
        return results
    
    def search_document(self, document: Document, query: str, buffer: int = 50) -> List[Dict[str, Any]]:
        """
        Search within a specific document
        
        Args:
            document: Document to search in
            query: Search query
            
        Returns:
            List of search results with context
        """
        # Use the same search approach as search_all but filter results for this document
        all_results = self.search_all(query, limit=100, offset=0, buffer=buffer)
        
        # Filter results to only include this document
        document_results = []
        for result in all_results:
            if result['document_id'] == document.id:
                document_results.append(result)
        
        return document_results
    
    def _get_context(self, text: str, query: str, highlights: str, buffer: int = 50) -> str:
        """Extract context around search matches"""
        import re
        
        if highlights:
            # Strip HTML tags from Whoosh highlights and extract just the matched text
            clean_highlights = re.sub(r'<[^>]+>', '', highlights)
            
            # Find the position of the matched text in the original text
            query_lower = query.lower()
            text_lower = text.lower()
            pos = text_lower.find(query_lower)
            
            if pos != -1:
                # Calculate context around the match
                context_start = max(0, pos - buffer)
                context_end = min(len(text), pos + len(query_lower) + buffer)
                context = text[context_start:context_end]
                
                if context_start > 0:
                    context = "..." + context
                if context_end < len(text):
                    context = context + "..."
                
                return context
            else:
                return clean_highlights
        
        # Fallback: find query in text and get context
        query_lower = query.lower()
        text_lower = text.lower()
        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:100] + "..." if len(text) > 100 else text
        
        context_start = max(0, pos - buffer)
        context_end = min(len(text), pos + len(query_lower) + buffer)
        context = text[context_start:context_end]
        
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        return context
    
    def rebuild_index(self):
        """Rebuild the entire index from documents in the bucket"""
        writer = self.index.writer()
        
        # Load all documents from bucket
        documents = self.document_store.get_all()
        
        # Index each document
        for document in documents:
            writer.add_document(
                doc_id=document.id,
                title=document.title,
                content=document.text
            )
        
        writer.commit()
        self._index_built = True
    
    def __del__(self):
        """Cleanup temporary index directory"""
        try:
            import shutil
            shutil.rmtree(self.index_dir, ignore_errors=True)
        except:
            pass 