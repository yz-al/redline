import unittest
import json
from fastapi.testclient import TestClient
from main import app

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.base_url = "http://testserver"
        self.created_document_ids = []

    def tearDown(self):
        """Clean up any documents created during tests"""
        for doc_id in self.created_document_ids:
            try:
                self.client.delete(f"/documents/{doc_id}")
            except:
                pass  # Ignore cleanup errors
        self.created_document_ids.clear()

    def create_test_document(self, title="Test Document", text="This is a test document."):
        """Helper method to create a test document and track it for cleanup"""
        document_data = {
            "title": title,
            "text": text
        }
        
        response = self.client.post("/documents", json=document_data)
        self.assertEqual(response.status_code, 201)
        doc_id = response.json()["id"]
        self.created_document_ids.append(doc_id)
        return doc_id

    def test_create_document(self):
        """Test document creation endpoint"""
        doc_id = self.create_test_document("Test Document", "This is a test document for API testing.")
        
        # Verify the document was created correctly
        self.assertIsInstance(doc_id, str)
        self.assertGreater(len(doc_id), 0)

    def test_get_document(self):
        """Test document retrieval endpoint"""
        # First create a document
        doc_id = self.create_test_document("Test Document for Get", "This document will be retrieved.")
        
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
        doc_id = self.create_test_document("Test Document for Range Redline", "This is a test document for range redlining.")
        
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
        doc_id = self.create_test_document("Test Document for Target Redline", "This is a test document with test content for testing.")
        
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
        doc_ids = []
        documents = [
            {"title": "Contract A", "text": "This is a legal contract between parties."},
            {"title": "Contract B", "text": "Another contract with different terms."},
            {"title": "Agreement", "text": "This is an employment agreement."}
        ]
        
        for doc in documents:
            doc_id = self.create_test_document(doc["title"], doc["text"])
            doc_ids.append(doc_id)
        
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
        doc_id = self.create_test_document("Test Document for Search", "This document contains the word contract and agreement.")
        
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
            self.create_test_document(f"Test Document {i}", f"This is test document {i}.")
        
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
        doc_id = self.create_test_document("Test Document for Buffer Search", "This is a test document with the word contract in the middle of this sentence.")
        
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
            self.create_test_document(f"Test Document {i}", f"This is test document {i} with contract terms.")
        
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

    def test_append_to_document(self):
        """Test appending text to a document"""
        # Create a document
        doc_id = self.create_test_document("Test Document for Append", "Original content.")
        
        # Append text to the document
        append_data = {"text": " Appended content."}
        response = self.client.patch(f"/documents/{doc_id}/append", json=append_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], doc_id)
        self.assertEqual(data["version"], 2)  # Version should be incremented
        self.assertIn("message", data)
        
        # Verify the content was actually appended
        get_response = self.client.get(f"/documents/{doc_id}")
        self.assertEqual(get_response.status_code, 200)
        document_data = get_response.json()
        self.assertEqual(document_data["text"], "Original content. Appended content.")
        self.assertEqual(document_data["version"], 2)

    def test_append_to_nonexistent_document(self):
        """Test appending text to a document that doesn't exist"""
        append_data = {"text": "Some text"}
        response = self.client.patch("/documents/nonexistent-id/append", json=append_data)
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)

    def test_delete_document(self):
        """Test document deletion endpoint"""
        # Create a document
        doc_id = self.create_test_document("Test Document for Delete", "This document will be deleted.")
        
        # Verify it exists
        get_response = self.client.get(f"/documents/{doc_id}")
        self.assertEqual(get_response.status_code, 200)
        
        # Delete the document
        delete_response = self.client.delete(f"/documents/{doc_id}")
        self.assertEqual(delete_response.status_code, 200)
        
        # Verify it's deleted
        get_response = self.client.get(f"/documents/{doc_id}")
        self.assertEqual(get_response.status_code, 404)
        
        # Remove from cleanup list since we already deleted it
        self.created_document_ids.remove(doc_id)

    def test_delete_nonexistent_document(self):
        """Test deleting a document that doesn't exist"""
        response = self.client.delete("/documents/nonexistent-id")
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)

if __name__ == '__main__':
    unittest.main() 