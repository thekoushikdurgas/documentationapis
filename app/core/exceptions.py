"""Custom exceptions for the documentation API."""


class DocumentationAPIException(Exception):
    """Base exception for documentation API."""
    pass


class DocumentationNotFoundError(DocumentationAPIException):
    """Raised when a documentation page is not found."""
    pass


class EndpointDocumentationNotFoundError(DocumentationAPIException):
    """Raised when an endpoint documentation is not found."""
    pass


class InvalidDocumentationIDError(DocumentationAPIException):
    """Raised when an invalid documentation ID is provided."""
    pass


class ValidationError(DocumentationAPIException):
    """Raised when request validation fails."""
    pass


class DatabaseError(DocumentationAPIException):
    """Raised when a database operation fails."""
    pass


class AuthenticationError(DocumentationAPIException):
    """Raised when authentication fails."""
    pass


class S3Error(DocumentationAPIException):
    """Raised when an S3 operation fails."""
    pass

