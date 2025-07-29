import unittest
import tempfile
import shutil
from unittest.mock import Mock, patch
from core.search import SearchEngine
from core.document_store import DocumentStore
from core.models import Document

class TestSearchEngine(unittest.TestCase):
    def setUp(self):
        # Create a mock document store
        self.mock_document_store = Mock(spec=DocumentStore)
        self.search_engine = SearchEngine(self.mock_document_store)
        
        # Sample documents for testing
        self.doc1 = Document(
            id="doc1",
            title="Legal Contract",
            text="This is a legal contract between Party A and Party B. The contract contains important terms and conditions.",
            version=1,
            created_at=None,
            updated_at=None
        )
        
        self.doc2 = Document(
            id="doc2", 
            title="Employment Agreement",
            text="Employment agreement for John Doe. This agreement outlines the terms of employment including salary and benefits.",
            version=1,
            created_at=None,
            updated_at=None
        )

    def tearDown(self):
        # Clean up temporary index directory
        if hasattr(self.search_engine, 'index_dir'):
            try:
                shutil.rmtree(self.search_engine.index_dir)
            except:
                pass

    def test_search_all_basic(self):
        """Test basic search functionality"""
        # Mock the document store to return our test documents
        self.mock_document_store.get_all.return_value = [self.doc1, self.doc2]
        
        # Mock get_without_lock to return documents
        def mock_get_without_lock(doc_id):
            if doc_id == "doc1":
                return self.doc1
            elif doc_id == "doc2":
                return self.doc2
            return None
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test search
        results = self.search_engine.search_all("contract", limit=10)
        
        # Should find "contract" in doc1
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['document_id'], "doc1")

    def test_search_document_specific(self):
        """Test document-specific search"""
        # Mock the document store
        self.mock_document_store.get_all.return_value = [self.doc1, self.doc2]
        
        def mock_get_without_lock(doc_id):
            if doc_id == "doc1":
                return self.doc1
            elif doc_id == "doc_id":
                return self.doc2
            return None
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test document-specific search
        results = self.search_engine.search_document(self.doc1, "contract")
        
        # Should find "contract" in doc1
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['document_id'], "doc1")

    def test_search_with_buffer(self):
        """Test search with custom buffer size"""
        self.mock_document_store.get_all.return_value = [self.doc1]
        
        def mock_get_without_lock(doc_id):
            return self.doc1
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test search with small buffer
        results = self.search_engine.search_all("contract", buffer=5)
        
        self.assertGreater(len(results), 0)
        # Context should be limited by buffer size
        context = results[0]['context']
        self.assertLess(len(context), 50)  # Should be much smaller than default buffer

    def test_search_no_results(self):
        """Test search with no matching results"""
        self.mock_document_store.get_all.return_value = [self.doc1]
        
        def mock_get_without_lock(doc_id):
            return self.doc1
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Search for non-existent term
        results = self.search_engine.search_all("nonexistent", limit=10)
        
        # Should return empty results
        self.assertEqual(len(results), 0)

    def test_search_with_offset(self):
        """Test search with offset parameter"""
        # Create multiple documents with the same search term
        docs = []
        for i in range(5):
            doc = Document(
                id=f"doc{i}",
                title=f"Document {i}",
                text=f"This is document {i} with the word contract in it.",
                version=1,
                created_at=None,
                updated_at=None
            )
            docs.append(doc)
        
        self.mock_document_store.get_all.return_value = docs
        
        def mock_get_without_lock(doc_id):
            for doc in docs:
                if doc.id == doc_id:
                    return doc
            return None
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test search with offset
        results = self.search_engine.search_all("contract", limit=2, offset=2)
        
        # Should return 2 results starting from offset 2
        self.assertEqual(len(results), 2)

    def test_search_performance_large_documents(self):
        """Test search performance with large documents"""
        # Create a large document
        large_text = "This is a large document. " * 1000  # ~25,000 characters
        large_doc = Document(
            id="large_doc",
            title="Large Document",
            text=large_text + "The word contract appears here.",
            version=1,
            created_at=None,
            updated_at=None
        )
        
        self.mock_document_store.get_all.return_value = [large_doc]
        
        def mock_get_without_lock(doc_id):
            return large_doc
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test search performance
        import time
        start_time = time.time()
        results = self.search_engine.search_all("contract", limit=10)
        end_time = time.time()
        
        # Should complete within 2 seconds
        self.assertLess(end_time - start_time, 2.0)
        
        # Should find the result
        self.assertGreater(len(results), 0)

    def test_search_special_characters(self):
        """Test search with special characters"""
        special_doc = Document(
            id="special_doc",
            title="Special Document",
            text="This document contains special characters: @#$%^&*() and numbers 12345.",
            version=1,
            created_at=None,
            updated_at=None
        )
        
        self.mock_document_store.get_all.return_value = [special_doc]
        
        def mock_get_without_lock(doc_id):
            return special_doc
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test search for special characters
        results = self.search_engine.search_all("12345", limit=10)
        self.assertGreater(len(results), 0)

    def test_search_case_insensitive(self):
        """Test that search is case insensitive"""
        case_doc = Document(
            id="case_doc",
            title="Case Document",
            text="This document has CONTRACT, Contract, and contract in different cases.",
            version=1,
            created_at=None,
            updated_at=None
        )
        
        self.mock_document_store.get_all.return_value = [case_doc]
        
        def mock_get_without_lock(doc_id):
            return case_doc
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test search with different cases
        results1 = self.search_engine.search_all("CONTRACT", limit=10)
        results2 = self.search_engine.search_all("contract", limit=10)
        results3 = self.search_engine.search_all("Contract", limit=10)
        
        # All should return the same document
        self.assertEqual(len(results1), len(results2))
        self.assertEqual(len(results2), len(results3))

    def test_rebuild_index(self):
        """Test index rebuilding functionality"""
        self.mock_document_store.get_all.return_value = [self.doc1, self.doc2]
        
        # Initially index should not be built
        self.assertFalse(self.search_engine._index_built)
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Index should now be built
        self.assertTrue(self.search_engine._index_built)

    def test_context_extraction(self):
        """Test context extraction around matches"""
        self.mock_document_store.get_all.return_value = [self.doc1]
        
        def mock_get_without_lock(doc_id):
            return self.doc1
        
        self.mock_document_store.get_without_lock.side_effect = mock_get_without_lock
        
        # Rebuild index
        self.search_engine.rebuild_index()
        
        # Test search with context
        results = self.search_engine.search_all("contract", buffer=10)
        
        if len(results) > 0:
            context = results[0]['context']
            # Context should contain the search term
            self.assertIn("contract", context.lower())

if __name__ == '__main__':
    unittest.main() 