"""
from app.constants.error_messages import ChromaErrors
from app.schemas.response_schemas import StandardResponse

def get_collection(collection_id: str):
    # Fake example
    if collection_id != "123":
        return StandardResponse(
            status="error",
            message=ChromaErrors.CHROM_COLLECTION_NOT_FOUND,  # "Collection not found"
            data=None
        )
"""
from enum import Enum
from .messages import Status

class ChromaInfo(str, Enum):
    #-------------------chroma----------------------
    CHROMA_STATUS_SUCCESS = Status.SUCCESS
    CHROMA_RETRIVED_TENANT = "Chroma tenant retrieved successfully"
    CHROMA_STATUS_NOT_FOUND = "Chroma status not found"
    CHROMA_CREATE_TENANT = "Chroma tenant created successfully"
    CHROMA_UPDATE_TENANT = "Chroma tenant updated successfully"
    CHROMA_DELETE_TENANT = "Chroma tenant deleted successfully"
    CHROMA_CREATE_DATABASE = "Chroma database created successfully"
    CHROMA_UPDATE_DATABASE = "Chroma database updated successfully"
    CHROMA_DELETE_DATABASE = "Chroma database deleted successfully"
    CHROMA_CREATE_COLLECTION = "Chroma collection created successfully"
    CHROMA_UPDATE_COLLECTION = "Chroma collection updated successfully"
    CHROMA_DELETE_COLLECTION = "Chroma collection deleted successfully"
    CHROMA_CREATE_DOCUMENT = "Chroma document created successfully"
    CHROMA_UPDATE_DOCUMENT = "Chroma document updated successfully"
    CHROMA_DELETE_DOCUMENT = "Chroma document deleted successfully"


class ChromaErrors(str, Enum):

    # ---------------- Status ----------------
    CHROMA_STATUS_FAILED = Status.FAILED

    # ---------------- Connection / Availability ----------------
    CHROM_CONNECTION_FAILED = "ChromaDB connection failed"
    CHROM_SERVICE_UNAVAILABLE = "ChromaDB service unavailable"
    CHROM_REQUEST_TIMED_OUT = "ChromaDB request timed out"
    CHROM_HEARTBEAT_FAILED = "ChromaDB heartbeat failed"
    CHROM_UNHEALTHY_STATUS = "ChromaDB unhealthy status"

    # ---------------- Authentication / Authorization ----------------
    CHROM_AUTHENTICATION_FAILED = "ChromaDB authentication failed"
    CHROM_AUTHORIZATION_DENIED = "ChromaDB authorization denied"
    CHROM_API_KEY_MISSING = "ChromaDB API key missing"
    CHROM_API_KEY_INVALID = "ChromaDB API key invalid"
    CHROM_ACCESS_FORBIDDEN = "ChromaDB access forbidden"

    # ---------------- Database / Collection ----------------
    CHROM_DATABASE_NOT_FOUND = "Database not found in ChromaDB"
    CHROM_DATABASE_ALREADY_EXISTS = "Database already exists"
    CHROM_DATABASE_CREATION_FAILED = "Database creation failed"
    CHROM_DATABASE_DELETION_FAILED = "Database deletion failed"
    CHROM_DATABASE_RENAME_FAILED = "Database rename failed"

    # ---------------- Collections ----------------
    CHROM_COLLECTION_NOT_FOUND = "Collection not found"
    CHROM_COLLECTION_ALREADY_EXISTS = "Collection already exists"
    CHROM_COLLECTION_CREATION_FAILED = "Collection creation failed"
    CHROM_COLLECTION_DELETION_FAILED = "Collection deletion failed"
    CHROM_COLLECTION_RENAME_FAILED = "Collection rename failed"
    CHROM_INVALID_COLLECTION_METADATA = "Invalid collection metadata"
    CHROM_COLLECTION_LOCKED = "Collection locked"
    CHROM_COLLECTION_CORRUPTED = "Collection corrupted"

    # ---------------- Documents / Embeddings ----------------
    CHROM_DOCUMENT_NOT_FOUND = "Document not found"
    CHROM_DOCUMENT_ALREADY_EXISTS = "Document already exists"
    CHROM_DOCUMENT_CREATION_FAILED = "Document creation failed"
    CHROM_DOCUMENT_UPDATE_FAILED = "Document update failed"
    CHROM_DOCUMENT_DELETION_FAILED = "Document deletion failed"
    CHROM_DOCUMENT_CORRUPTED = "Document corrupted"
    CHROM_DOCUMENT_ID_MISSING = "Document ID missing"
    CHROM_DOCUMENT_ID_INVALID = "Document ID invalid"
    CHROM_TOO_MANY_DOCUMENTS = "Too many documents in request"
    CHROM_DOCUMENT_BATCH_SIZE_EXCEEDED = "Document batch size exceeded"

    # ---------------- Embeddings ----------------
    CHROM_EMBEDDING_NOT_FOUND = "Embedding not found"
    CHROM_EMBEDDING_CREATION_FAILED = "Embedding creation failed"
    CHROM_EMBEDDING_UPDATE_FAILED = "Embedding update failed"
    CHROM_EMBEDDING_DELETION_FAILED = "Embedding deletion failed"
    CHROM_EMBEDDING_DIMENSION_MISMATCH = "Embedding dimension mismatch"
    CHROM_EMBEDDING_VECTOR_INVALID = "Embedding vector invalid"
    CHROM_EMBEDDING_LIMIT_EXCEEDED = "Embedding limit exceeded"
    CHROM_EMPTY_EMBEDDING_PAYLOAD = "Empty embedding payload"
    CHROM_DUPLICATE_EMBEDDINGS_DETECTED = "Duplicate embeddings detected"
    CHROM_EMBEDDING_ENCODING_ERROR = "Embedding encoding error"

    # ---------------- Queries / Search ----------------
    CHROM_QUERY_EXECUTION_FAILED = "Query execution failed"
    CHROM_INVALID_QUERY_PARAMETERS = "Invalid query parameters"
    CHROM_QUERY_VECTOR_DIMENSION_MISMATCH = "Query vector dimension mismatch"
    CHROM_QUERY_TIMEOUT = "Query timeout"
    CHROM_QUERY_NO_RESULTS = "Query returned no results"
    CHROM_QUERY_LIMIT_EXCEEDED = "Query limit exceeded"
    CHROM_INVALID_SIMILARITY_METRIC = "Invalid similarity metric"
    CHROM_DISTANCE_COMPUTATION_FAILED = "Distance computation failed"
    CHROM_ANN_INDEX_NOT_AVAILABLE = "ANN index not available"
    CHROM_QUERY_INDEX_CORRUPTED = "Query index corrupted"

    # ---------------- Index / Storage ----------------
    CHROM_INDEX_BUILD_FAILED = "Index build failed"
    CHROM_INDEX_UPDATE_FAILED = "Index update failed"
    CHROM_INDEX_DELETION_FAILED = "Index deletion failed"
    CHROM_INDEX_CORRUPTED = "Index corrupted"
    CHROM_INDEX_LOCK_FAILED = "Index lock failed"
    CHROM_INDEX_STORAGE_UNAVAILABLE = "Index storage unavailable"
    CHROM_INDEX_COMPACTION_FAILED = "Index compaction failed"
    CHROM_INDEX_TOO_LARGE = "Index too large"
    CHROM_INDEX_INCONSISTENCY_DETECTED = "Index inconsistency detected"
    CHROM_INDEX_SCHEMA_MISMATCH = "Index schema mismatch"

    # ---------------- Metadata / Schema ----------------
    CHROM_INVALID_METADATA_FORMAT = "Invalid metadata format"
    CHROM_MISSING_REQUIRED_METADATA = "Missing required metadata"
    CHROM_METADATA_TOO_LARGE = "Metadata too large"
    CHROM_INVALID_SCHEMA_DEFINITION = "Invalid schema definition"
    CHROM_SCHEMA_VERSION_MISMATCH = "Schema version mismatch"
    CHROM_SCHEMA_VALIDATION_FAILED = "Schema validation failed"
    CHROM_SCHEMA_MIGRATION_FAILED = "Schema migration failed"
    CHROM_UNSUPPORTED_SCHEMA_TYPE = "Unsupported schema type"
    CHROM_CORRUPTED_METADATA = "Corrupted metadata"
    CHROM_METADATA_CONFLICT_DETECTED = "Metadata conflict detected"

    # ---------------- Performance / Limits ----------------
    CHROM_MEMORY_LIMIT_EXCEEDED = "ChromaDB memory limit exceeded"
    CHROM_DISK_LIMIT_EXCEEDED = "ChromaDB disk limit exceeded"
    CHROM_REQUEST_RATE_LIMIT_EXCEEDED = "ChromaDB request rate limit exceeded"
    CHROM_TOO_MANY_CONCURRENT_CONNECTIONS = "ChromaDB too many concurrent connections"
    CHROM_OPERATION_TOO_SLOW = "ChromaDB operation too slow"
    CHROM_BATCH_REQUEST_TOO_LARGE = "Batch request too large"
    CHROM_STREAMING_RESPONSE_INTERRUPTED = "Streaming response interrupted"
    CHROM_RESOURCE_CONTENTION_DETECTED = "Resource contention detected"
    CHROM_DEADLOCK_DETECTED = "Deadlock detected in ChromaDB"
    CHROM_UNKNOWN_INTERNAL_ERROR = "Unknown internal ChromaDB error"

