from typing import Dict, Optional, List, Set
from core.models import Document
import json
import os
from datetime import datetime, timedelta, timezone
import uuid
import threading
from contextlib import contextmanager
from google.cloud import storage
from google.cloud.exceptions import NotFound, Conflict
import time

class DocumentLock:
    """RAII-style document lock for Google Cloud Storage"""
    
    def __init__(self, bucket, document_id: str, lock_timeout: int = 300):
        self.bucket = bucket
        self.document_id = document_id
        self.lock_blob_name = f"locks/{document_id}.lock"
        self.lock_timeout = lock_timeout
        self.lock_blob = None
        self.lock_acquired = False
        self.lock_id = str(uuid.uuid4())
        
    def __enter__(self):
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        
    def acquire(self) -> bool:
        """Acquire a lock on the document"""
        try:
            # Create lock metadata
            lock_data = {
                'lock_id': self.lock_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'timeout': self.lock_timeout
            }
            
            # Try to create the lock blob
            self.lock_blob = self.bucket.blob(self.lock_blob_name)
            self.lock_blob.upload_from_string(
                json.dumps(lock_data),
                content_type='application/json',
                if_generation_match=0  # Only create if it doesn't exist
            )
            
            self.lock_acquired = True
            return True
            
        except Conflict:
            # Lock already exists, check if it's expired
            try:
                existing_blob = self.bucket.blob(self.lock_blob_name)
                existing_data = json.loads(existing_blob.download_as_text())
                
                lock_time = datetime.fromisoformat(existing_data['timestamp'])
                if datetime.now(timezone.utc) - lock_time > timedelta(seconds=existing_data['timeout']):
                    # Lock is expired, try to steal it
                    return self._steal_lock()
                else:
                    return False
                    
            except Exception:
                # If we can't read the lock, assume it's invalid and steal it
                return self._steal_lock()
                
        except Exception as e:
            print(f"Error acquiring lock for {self.document_id}: {e}")
            return False
    
    def _steal_lock(self) -> bool:
        """Steal an expired or invalid lock"""
        try:
            lock_data = {
                'lock_id': self.lock_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'timeout': self.lock_timeout
            }
            
            self.lock_blob = self.bucket.blob(self.lock_blob_name)
            self.lock_blob.upload_from_string(
                json.dumps(lock_data),
                content_type='application/json'
            )
            
            self.lock_acquired = True
            return True
            
        except Exception as e:
            print(f"Error stealing lock for {self.document_id}: {e}")
            return False
    
    def release(self):
        """Release the lock"""
        if self.lock_acquired and self.lock_blob:
            try:
                # Only delete if it's our lock
                existing_data = json.loads(self.lock_blob.download_as_text())
                if existing_data.get('lock_id') == self.lock_id:
                    self.lock_blob.delete()
            except Exception as e:
                print(f"Error releasing lock for {self.document_id}: {e}")
            finally:
                self.lock_acquired = False

class HierarchicalLock:
    """Manages hierarchical locking for document operations"""
    
    def __init__(self, bucket):
        self.bucket = bucket
        self._local_locks: Set[str] = set()
        self._lock_thread = threading.current_thread()
        
    @contextmanager
    def lock_document(self, document_id: str, lock_timeout: int = 300):
        """RAII-style document locking"""
        lock = DocumentLock(self.bucket, document_id, lock_timeout)
        try:
            if lock.acquire():
                self._local_locks.add(document_id)
                yield lock
            else:
                raise RuntimeError(f"Could not acquire lock for document {document_id}")
        finally:
            lock.release()
            self._local_locks.discard(document_id)
    
    @contextmanager
    def lock_hierarchy(self, document_ids: List[str], lock_timeout: int = 300):
        """Lock multiple documents in hierarchical order (by ID)"""
        document_ids = sorted(document_ids)  # Ensure consistent ordering
        locks = []
        
        try:
            # Acquire all locks in order
            for doc_id in document_ids:
                lock = DocumentLock(self.bucket, doc_id, lock_timeout)
                if lock.acquire():
                    locks.append(lock)
                    self._local_locks.add(doc_id)
                else:
                    # Release all acquired locks
                    for acquired_lock in locks:
                        acquired_lock.release()
                        self._local_locks.discard(acquired_lock.document_id)
                    raise RuntimeError(f"Could not acquire lock for document {doc_id}")
            
            yield locks
            
        finally:
            # Release all locks
            for lock in locks:
                lock.release()
                self._local_locks.discard(lock.document_id)

class GCSDocumentStore:
    """Google Cloud Storage-based document storage with locking"""
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        """
        Initialize the document store
        
        Args:
            bucket_name: Name of the GCS bucket
            project_id: Google Cloud project ID (optional, uses default if not provided)
        """
        self.bucket_name = bucket_name
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
        self.lock_manager = HierarchicalLock(self.bucket)
        
        # Ensure bucket exists
        if not self.bucket.exists():
            self.bucket.create()
    
    def save(self, document: Document) -> None:
        """
        Save a document to GCS with locking
        
        Args:
            document: Document to save
        """
        with self.lock_manager.lock_document(document.id):
            self.save_without_lock(document)
    
    def save_without_lock(self, document: Document) -> None:
        """
        Save a document to GCS without locking
        
        Args:
            document: Document to save
        """
        # Serialize document
        doc_data = document.to_dict()
        doc_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Save to GCS
        blob = self.bucket.blob(f"documents/{document.id}.json")
        blob.upload_from_string(
            json.dumps(doc_data, indent=2),
            content_type='application/json'
        )
    
    def get(self, doc_id: str) -> Optional[Document]:
        """
        Retrieve a document by ID with locking
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        with self.lock_manager.lock_document(doc_id):
            return self.get_without_lock(doc_id)
    
    def get_without_lock(self, doc_id: str) -> Optional[Document]:
        """
        Retrieve a document by ID without locking
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        try:
            blob = self.bucket.blob(f"documents/{doc_id}.json")
            doc_data = json.loads(blob.download_as_text())
            return Document.from_dict(doc_data)
        except NotFound:
            return None
        except Exception as e:
            print(f"Error loading document {doc_id}: {e}")
            return None
    
    def get_all(self) -> List[Document]:
        """
        Get all documents (without locking individual documents)
        
        Returns:
            List of all documents
        """
        documents = []
        blobs = self.bucket.list_blobs(prefix="documents/")
        
        for blob in blobs:
            if blob.name.endswith('.json'):
                try:
                    doc_data = json.loads(blob.download_as_text())
                    documents.append(Document.from_dict(doc_data))
                except Exception as e:
                    print(f"Error loading document from {blob.name}: {e}")
                    continue
        
        return documents
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document with locking
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if document was deleted, False if not found
        """
        with self.lock_manager.lock_document(doc_id):
            try:
                # Delete document
                doc_blob = self.bucket.blob(f"documents/{doc_id}.json")
                doc_blob.delete()
                
                # Try to delete lock (ignore if it doesn't exist)
                try:
                    lock_blob = self.bucket.blob(f"locks/{doc_id}.lock")
                    lock_blob.delete()
                except NotFound:
                    pass
                
                return True
            except NotFound:
                return False
            except Exception as e:
                print(f"Error deleting document {doc_id}: {e}")
                return False
    
    def exists(self, doc_id: str) -> bool:
        """
        Check if a document exists
        
        Args:
            doc_id: Document ID to check
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            blob = self.bucket.blob(f"documents/{doc_id}.json")
            return blob.exists()
        except Exception as e:
            print(f"Error checking existence of document {doc_id}: {e}")
            return False
    
    def append(self, doc_id: str, text_to_append: str) -> bool:
        """
        Append text to a document with locking
        
        Args:
            doc_id: Document ID to append to
            text_to_append: Text to append
            
        Returns:
            True if document was updated, False if not found
        """
        with self.lock_manager.lock_document(doc_id):
            document = self.get_without_lock(doc_id)
            if not document:
                return False
            
            # Append the text
            document.text += text_to_append
            document.version += 1
            document.updated_at = datetime.now(timezone.utc)
            
            # Save the updated document
            self.save_without_lock(document)
            return True
    
    def count(self) -> int:
        """
        Get the total number of documents
        
        Returns:
            Number of documents in storage
        """
        try:
            blobs = list(self.bucket.list_blobs(prefix="documents/"))
            return len([b for b in blobs if b.name.endswith('.json')])
        except Exception as e:
            print(f"Error counting documents: {e}")
            return 0
    
    def batch_save(self, documents: List[Document]) -> None:
        """
        Save multiple documents with hierarchical locking
        
        Args:
            documents: List of documents to save
        """
        doc_ids = [doc.id for doc in documents]
        
        with self.lock_manager.lock_hierarchy(doc_ids):
            for document in documents:
                # Serialize document
                doc_data = document.to_dict()
                doc_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # Save to GCS
                blob = self.bucket.blob(f"documents/{document.id}.json")
                blob.upload_from_string(
                    json.dumps(doc_data, indent=2),
                    content_type='application/json'
                )
    
    def cleanup_expired_locks(self) -> int:
        """
        Clean up expired locks
        
        Returns:
            Number of locks cleaned up
        """
        cleaned_count = 0
        blobs = self.bucket.list_blobs(prefix="locks/")
        
        for blob in blobs:
            if blob.name.endswith('.lock'):
                try:
                    lock_data = json.loads(blob.download_as_text())
                    lock_time = datetime.fromisoformat(lock_data['timestamp'])
                    
                    if datetime.now(timezone.utc) - lock_time > timedelta(seconds=lock_data['timeout']):
                        blob.delete()
                        cleaned_count += 1
                        
                except Exception as e:
                    print(f"Error processing lock {blob.name}: {e}")
                    # Delete corrupted locks
                    try:
                        blob.delete()
                        cleaned_count += 1
                    except Exception:
                        pass
        
        return cleaned_count

# Backward compatibility - alias the new class
DocumentStore = GCSDocumentStore 