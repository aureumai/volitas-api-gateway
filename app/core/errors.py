from fastapi import HTTPException, status


class VolitsAPIError(HTTPException):
    """Base class for all API errors."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class DatabaseError(VolitsAPIError):
    """Raised when a database operation fails."""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class NotFoundError(VolitsAPIError):
    """Raised when a requested resource is not found."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class BadRequestError(VolitsAPIError):
    """Raised when a request is malformed or invalid."""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class UnauthorizedError(VolitsAPIError):
    """Raised when a request is unauthorized."""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(VolitsAPIError):
    """Raised when a request is forbidden."""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ServiceUnavailableError(VolitsAPIError):
    """Raised when a service is unavailable."""
    def __init__(self, detail: str = "Service unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
