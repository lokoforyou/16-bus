from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    DOMAIN_RULE_VIOLATION = "DOMAIN_RULE_VIOLATION"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    CONFLICT = "CONFLICT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class AppError(Exception):
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.NOT_FOUND, details, status_code=404)


class DomainRuleViolationError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.DOMAIN_RULE_VIOLATION, details, status_code=422)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.PERMISSION_DENIED, details, status_code=403)


class InvalidStateTransitionError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_STATE_TRANSITION, details, status_code=400)


class ConflictError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.CONFLICT, details, status_code=409)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.AUTHENTICATION_ERROR, details, status_code=401)
