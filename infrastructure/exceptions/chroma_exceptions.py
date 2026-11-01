
class ChromaException(Exception):
    pass

class ChromaRequestError(ChromaException):
    pass

class ChromaTenantAPIError(ChromaException):
    pass

class ChromaDatabaseAPIError(ChromaException):
    pass

class ChromaCollectionAPIError(ChromaException):
    pass

class ChromaRecordAPIError(ChromaException):
    pass

class ChromaSystemAPIError(ChromaException):
    pass
