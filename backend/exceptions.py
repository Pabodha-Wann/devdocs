"""Custom Exceptions"""

class DevDocsError(Exception):
    def __init__(self,message:str,code:str="INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class InvalidRepositoryError(DevDocsError):
    def __init__(self,message: str):
        super().__init__(message,"INVALID_REPO")

class RepositoryCloneError(DevDocsError):
    def __init__(self, message: str):
        super().__init__(message, "CLONE_FAILED")

class RepositoryEmptyError(DevDocsError):
    def __init__(self, message: str):
        super().__init__(message, "REPO_EMPTY")

# Query errors
class InvalidQueryError(DevDocsError):
    def __init__(self, message: str):
        super().__init__(message, "INVALID_QUERY")


class DatabaseError(DevDocsError):
    def __init__(self, message: str):
        super().__init__(message, "DB_ERROR")


class LLMError(DevDocsError):
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR")


ERROR_STATUS_CODES = {
    InvalidRepositoryError: 400,
    RepositoryCloneError: 400,
    RepositoryEmptyError: 400,
    InvalidQueryError: 400,
    DatabaseError: 503,
    LLMError: 503,
}