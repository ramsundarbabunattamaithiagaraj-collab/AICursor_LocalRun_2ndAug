"""Domain-specific exception hierarchy.

Using explicit exception types (instead of bare Exception / silent passes)
lets API layers translate errors into precise HTTP responses and keeps
business logic free of HTTP concerns (separation of concerns).
"""
from __future__ import annotations


class RetailIQError(Exception):
    """Base class for all application-raised errors."""


class NotFoundError(RetailIQError):
    def __init__(self, resource: str, identifier: object):
        super().__init__(f"{resource} with identifier '{identifier}' was not found.")
        self.resource = resource
        self.identifier = identifier


class DuplicateResourceError(RetailIQError):
    def __init__(self, resource: str, field: str, value: object):
        super().__init__(f"{resource} with {field}='{value}' already exists.")


class ValidationError(RetailIQError):
    def __init__(self, message: str):
        super().__init__(message)


class InsufficientStockError(RetailIQError):
    def __init__(self, sku: str, requested: int, available: int):
        super().__init__(
            f"Insufficient stock for SKU '{sku}': requested {requested}, available {available}."
        )


class AuthenticationError(RetailIQError):
    def __init__(self, message: str = "Invalid credentials."):
        super().__init__(message)


class AuthorizationError(RetailIQError):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(message)


class ConfigurationError(RetailIQError):
    def __init__(self, message: str):
        super().__init__(message)


class RagUnavailableError(RetailIQError):
    def __init__(self, message: str = "RAG subsystem is currently unavailable."):
        super().__init__(message)


class AgentExecutionError(RetailIQError):
    def __init__(self, agent_name: str, message: str):
        super().__init__(f"Agent '{agent_name}' failed: {message}")
