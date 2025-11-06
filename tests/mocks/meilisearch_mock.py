"""
Mock implementation of Meilisearch client for testing

Provides a simple in-memory search index that simulates
Meilisearch behavior without requiring a running server.
"""

from typing import Any, Dict, List, Optional


class MockIndex:
    """Mock Meilisearch index"""

    def __init__(self, uid: str):
        self.uid = uid
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.settings: Dict[str, Any] = {
            "searchableAttributes": ["*"],
            "filterableAttributes": [],
            "sortableAttributes": [],
        }

    def add_documents(
        self, documents: List[Dict[str, Any]], primary_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add documents to mock index"""
        for doc in documents:
            doc_id = str(doc.get(primary_key or "id", len(self.documents)))
            self.documents[doc_id] = doc

        return {
            "taskUid": 1,
            "indexUid": self.uid,
            "status": "enqueued",
            "type": "documentAdditionOrUpdate",
        }

    def update_documents(
        self, documents: List[Dict[str, Any]], primary_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update documents in mock index"""
        return self.add_documents(documents, primary_key)

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete document from mock index"""
        if document_id in self.documents:
            del self.documents[document_id]

        return {
            "taskUid": 2,
            "indexUid": self.uid,
            "status": "enqueued",
            "type": "documentDeletion",
        }

    def delete_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple documents"""
        for doc_id in document_ids:
            self.documents.pop(doc_id, None)

        return {
            "taskUid": 3,
            "indexUid": self.uid,
            "status": "enqueued",
            "type": "documentDeletion",
        }

    def delete_all_documents(self) -> Dict[str, Any]:
        """Delete all documents from index"""
        self.documents.clear()
        return {
            "taskUid": 4,
            "indexUid": self.uid,
            "status": "enqueued",
            "type": "documentDeletion",
        }

    def search(
        self,
        query: str,
        opt_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Simple mock search implementation

        Returns documents that contain the query string in any field.
        In real Meilisearch, this would be much more sophisticated.
        """
        opt_params = opt_params or {}
        limit = opt_params.get("limit", 20)
        offset = opt_params.get("offset", 0)

        # Simple substring search across all fields
        results = []
        query_lower = query.lower()

        for doc_id, doc in self.documents.items():
            # Check if query appears in any field
            for value in doc.values():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(doc)
                    break

        # Apply pagination
        total_hits = len(results)
        paginated_results = results[offset : offset + limit]

        return {
            "hits": paginated_results,
            "offset": offset,
            "limit": limit,
            "estimatedTotalHits": total_hits,
            "processingTimeMs": 1,
            "query": query,
        }

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get a specific document by ID"""
        if document_id not in self.documents:
            raise KeyError(f"Document {document_id} not found")
        return self.documents[document_id]

    def get_documents(
        self, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get all documents with pagination"""
        parameters = parameters or {}
        limit = parameters.get("limit", 20)
        offset = parameters.get("offset", 0)

        docs = list(self.documents.values())
        paginated = docs[offset : offset + limit]

        return {
            "results": paginated,
            "offset": offset,
            "limit": limit,
            "total": len(docs),
        }

    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update index settings"""
        self.settings.update(settings)
        return {
            "taskUid": 5,
            "indexUid": self.uid,
            "status": "enqueued",
            "type": "settingsUpdate",
        }

    def get_settings(self) -> Dict[str, Any]:
        """Get current index settings"""
        return self.settings.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "numberOfDocuments": len(self.documents),
            "isIndexing": False,
            "fieldDistribution": {},
        }


class MockMeilisearchClient:
    """
    Mock Meilisearch client for testing

    Usage in tests:
        from tests.mocks import MockMeilisearchClient

        @pytest.fixture
        def mock_search(monkeypatch):
            mock_client = MockMeilisearchClient("http://localhost:7700")
            monkeypatch.setattr("meilisearch.Client", lambda *args: mock_client)
            return mock_client

        def test_search(mock_search):
            index = mock_search.index("posts")
            index.add_documents([{"id": 1, "title": "Test"}])
            results = index.search("Test")
            assert len(results["hits"]) == 1
    """

    def __init__(self, url: str, api_key: Optional[str] = None):
        self.url = url
        self.api_key = api_key
        self.indexes: Dict[str, MockIndex] = {}

    def index(self, uid: str) -> MockIndex:
        """Get or create an index"""
        if uid not in self.indexes:
            self.indexes[uid] = MockIndex(uid)
        return self.indexes[uid]

    def get_index(self, uid: str) -> MockIndex:
        """Get an existing index"""
        if uid not in self.indexes:
            raise KeyError(f"Index {uid} not found")
        return self.indexes[uid]

    def create_index(
        self, uid: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new index"""
        if uid in self.indexes:
            raise ValueError(f"Index {uid} already exists")

        self.indexes[uid] = MockIndex(uid)
        return {
            "taskUid": 10,
            "indexUid": uid,
            "status": "enqueued",
            "type": "indexCreation",
        }

    def delete_index(self, uid: str) -> Dict[str, Any]:
        """Delete an index"""
        if uid in self.indexes:
            del self.indexes[uid]

        return {
            "taskUid": 11,
            "indexUid": uid,
            "status": "enqueued",
            "type": "indexDeletion",
        }

    def get_indexes(self) -> List[Dict[str, Any]]:
        """Get all indexes"""
        return [{"uid": uid, "primaryKey": None} for uid in self.indexes.keys()]

    def health(self) -> Dict[str, str]:
        """Mock health check"""
        return {"status": "available"}

    def is_healthy(self) -> bool:
        """Check if mock client is healthy"""
        return True

    def get_version(self) -> Dict[str, str]:
        """Get mock version info"""
        return {"commitSha": "mock", "commitDate": "2024-01-01", "pkgVersion": "1.0.0"}
