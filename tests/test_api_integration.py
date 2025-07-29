import unittest
import json
from fastapi.testclient import TestClient
from main import app

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.base_url = "http://testserver"

    def test_create_document(self):
        """Test document creation endpoint"""
        document_data = {
            "title": "Test Document",
            "text": "This is a test document for API testing."
        }
        
        response = self.client.post("/documents", json=document_data)
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("version", data)
        self.assertIn("created_at", data)
        self.assertEqual(data["version"], 1)

    def test_get_document(self):
        """Test document retrieval endpoint"""
        # First create a document
        document_data = {
            "title": "Test Document for Get",
            "text": "This document will be retrieved."
        }
        
        create_response = self.client.post("/documents", json=document_data)
        doc_id = create_response.json()["id"]
        
        # Now get the document
        response = self.client.get(f"/documents/{doc_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], doc_id)
        self.assertEqual(data["title"], "Test Document for Get")
        self.assertEqual(data["text"], "This document will be retrieved.")

    def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist"""
        response = self.client.get("/documents/nonexistent-id")
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)

    def test_redline_range(self):
        """Test range-based redlining"""
        # Create a document
        document_data = {
            "title": "Test Document for Range Redline",
            "text": "This is a test document for range redlining."
        }
        
        create_response = self.client.post("/documents", json=document_data)
        doc_id = create_response.json()["id"]
        
        # Apply range redline
        redline_data = {
            "documents": [{
                "document_id": doc_id,
                "range": {
                    "start": 10,
                    "end": 14
                },
                "replacement": "was"
            }]
        }
        
        response = self.client.patch("/documents/redline/range", json=redline_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("documents", data)
        self.assertIn("skipped", data)
        
        # Verify the document was updated
        get_response = self.client.get(f"/documents/{doc_id}")
        updated_text = get_response.json()["text"]
        self.assertIn("was", updated_text)

    def test_redline_target(self):
        """Test target-based redlining"""
        # Create a document
        document_data = {
            "title": "Test Document for Target Redline",
            "text": "This is a test document with test content for testing."
        }
        
        create_response = self.client.post("/documents", json=document_data)
        doc_id = create_response.json()["id"]
        
        # Apply target redline
        redline_data = {
            "documents": [{
                "document_id": doc_id,
                "target_text": "test",
                "occurrence": 1,
                "replacement": "sample"
            }]
        }
        
        response = self.client.patch("/documents/redline/target", json=redline_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("documents", data)
        self.assertIn("skipped", data)
        
        # Verify the document was updated
        get_response = self.client.get(f"/documents/{doc_id}")
        updated_text = get_response.json()["text"]
        self.assertIn("sample", updated_text)

    def test_global_search(self):
        """Test global search functionality"""
        # Create multiple documents
        documents = [
            {"title": "Contract A", "text": "This is a legal contract between parties."},
            {"title": "Contract B", "text": "Another contract with different terms."},
            {"title": "Agreement", "text": "This is an employment agreement."}
        ]
        
        doc_ids = []
        for doc in documents:
            response = self.client.post("/documents", json=doc)
            doc_ids.append(response.json()["id"])
        
        # Search for "contract"
        response = self.client.get("/documents/search?q=contract&limit=10")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        
        # Should find documents containing "contract"
        results = data["results"]
        self.assertGreater(len(results), 0)

    def test_document_search(self):
        """Test document-specific search"""
        # Create a document
        document_data = {
            "title": "Test Document for Search",
            "text": "This document contains the word contract and agreement."
        }
        
        create_response = self.client.post("/documents", json=document_data)
        doc_id = create_response.json()["id"]
        
        # Search within the document
        response = self.client.get(f"/documents/{doc_id}/search?q=contract")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        
        # Should find the word "contract"
        results = data["results"]
        self.assertGreater(len(results), 0)

    def test_get_all_document_ids(self):
        """Test getting all document IDs"""
        # Create some documents
        for i in range(3):
            document_data = {
                "title": f"Test Document {i}",
                "text": f"This is test document {i}."
            }
            self.client.post("/documents", json=document_data)
        
        # Get all document IDs
        response = self.client.get("/documents")
        
        self.assertEqual(response.status_code, 200)
        doc_ids = response.json()
        self.assertIsInstance(doc_ids, list)
        self.assertGreater(len(doc_ids), 0)

    def test_redline_nonexistent_document(self):
        """Test redlining a document that doesn't exist"""
        redline_data = {
            "documents": [{
                "document_id": "nonexistent-id",
                "range": {
                    "start": 0,
                    "end": 5
                },
                "replacement": "test"
            }]
        }
        
        response = self.client.patch("/documents/redline/range", json=redline_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["documents"]), 0)
        self.assertEqual(len(data["skipped"]), 1)
        self.assertEqual(data["skipped"][0]["reason"], "not_found")

    def test_search_with_buffer(self):
        """Test search with custom buffer parameter"""
        # Create a document
        document_data = {
            "title": "Test Document for Buffer Search",
            "text": "This is a test document with the word contract in the middle of this sentence."
        }
        
        create_response = self.client.post("/documents", json=document_data)
        doc_id = create_response.json()["id"]
        
        # Search with small buffer
        response = self.client.get(f"/documents/{doc_id}/search?q=contract&buffer=5")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if len(data["results"]) > 0:
            context = data["results"][0]["context"]
            # Context should be limited by buffer size
            self.assertLess(len(context), 50)

    def test_search_with_limit_and_offset(self):
        """Test search with limit and offset parameters"""
        # Create multiple documents with the same search term
        for i in range(5):
            document_data = {
                "title": f"Test Document {i}",
                "text": f"This is test document {i} with contract terms."
            }
            self.client.post("/documents", json=document_data)
        
        # Search with limit and offset
        response = self.client.get("/documents/search?q=contract&limit=2&offset=1")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data["results"]
        
        # Should return limited results
        self.assertLessEqual(len(results), 2)

    def test_invalid_redline_request(self):
        """Test redlining with invalid request data"""
        # Test with missing required fields
        invalid_data = {
            "documents": [{
                "document_id": "test-id"
                # Missing range and replacement
            }]
        }
        
        response = self.client.patch("/documents/redline/range", json=invalid_data)
        
        # Should return validation error
        self.assertEqual(response.status_code, 422)

    def test_search_without_query(self):
        """Test search without providing a query parameter"""
        response = self.client.get("/documents/search")
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("version", data)
        self.assertEqual(data["message"], "Document Redlining API")

if __name__ == '__main__':
    unittest.main() 