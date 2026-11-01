# test_build_path.py
import pytest
from unittest.mock import patch
import logging
from infrastructure.chroma_api.base import ChromaBaseClient

class TestBuildPath:
    """Test only the _build_path method"""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance"""
        return ChromaBaseClient(base_url="https://test.com", token="test-token")
    
    def test_build_path_single_part(self, client):
        """Test building path with single part"""
        path = client._build_path("collections")
        assert path == "/api/v2/collections"
    
    def test_build_path_multiple_parts(self, client):
        """Test building path with multiple parts"""
        path = client._build_path("tenants", "test-tenant", "databases", "test-db")
        assert path == "/api/v2/tenants/test-tenant/databases/test-db"
    
    def test_build_path_with_leading_trailing_slashes(self, client):
        """Test building path with parts that have leading/trailing slashes"""
        path = client._build_path("/tenants/", "/test-tenant/", "databases/")
        assert path == "/api/v2/tenants/test-tenant/databases"
    
    def test_build_path_empty_parts(self, client):
        """Test building path with empty parts"""
        path = client._build_path("tenants", "", "databases")
        assert path == "/api/v2/tenants/databases"
    
    def test_build_path_numeric_parts(self, client):
        """Test building path with numeric parts"""
        path = client._build_path("tenants", 123, "databases", 456)
        assert path == "/api/v2/tenants/123/databases/456"
    
    def test_build_path_no_parts(self, client):
        """Test building path with no parts"""
        path = client._build_path()
        assert path == "/api/v2/"
    
    def test_build_path_logging(self, client, caplog):
        """Test that the method logs the built path"""
        with caplog.at_level(logging.DEBUG):
            path = client._build_path("tenants", "test-tenant", "databases")
        
        # Check that the path was logged
        assert "[ChromaBaseClient] Build path: /api/v2/tenants/test-tenant/databases" in caplog.text
        assert path == "/api/v2/tenants/test-tenant/databases"

    def test_improved_build_path(self, client):
        """Test the improved _build_path method"""
        # With the improved implementation, these would work correctly:
        assert client._build_path("tenants", "", "databases") == "/api/v2/tenants/databases"
        assert client._build_path("tenants", "   ", "databases") == "/api/v2/tenants/databases"
        assert client._build_path("/tenants/", "/test/") == "/api/v2/tenants/test"
        assert client._build_path() == "/api/v2/"
        assert client._build_path("") == "/api/v2/"

# Example usage patterns from the actual files
def test_actual_usage_patterns():
    """Test the actual usage patterns found in the client classes"""
    client = ChromaBaseClient(base_url="https://test.com", token="test-token")
    
    # Test patterns from databases.py
    path1 = client._build_path("tenants", "my-tenant", "databases")
    assert path1 == "/api/v2/tenants/my-tenant/databases"
    
    path2 = client._build_path("tenants", "my-tenant", "databases", "my-db")
    assert path2 == "/api/v2/tenants/my-tenant/databases/my-db"
    
    # Test patterns from system.py
    path3 = client._build_path("auth", "identity")
    assert path3 == "/api/v2/auth/identity"
    
    path4 = client._build_path("healthcheck")
    assert path4 == "/api/v2/healthcheck"
    
    # Test patterns from collections.py
    path5 = client._build_path("tenants", "tenant1", "databases", "db1", "collections")
    assert path5 == "/api/v2/tenants/tenant1/databases/db1/collections"
    
    # Test patterns from records.py
    path6 = client._build_path("tenants", "tenant1", "databases", "db1", "collections", "coll1", "upsert")
    assert path6 == "/api/v2/tenants/tenant1/databases/db1/collections/coll1/upsert"
    
    # Test patterns from tenants.py
    path7 = client._build_path("tenants")
    assert path7 == "/api/v2/tenants"
    
    path8 = client._build_path("tenants", "test-tenant")
    assert path8 == "/api/v2/tenants/test-tenant"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])