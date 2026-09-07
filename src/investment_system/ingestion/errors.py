"""Shared exception hierarchy for ingestion adapters."""

from __future__ import annotations


class IngestionError(Exception):
    """Base class for every error an ingestion adapter raises."""


class IngestionConfigError(IngestionError):
    """Missing or invalid configuration/credentials (e.g. an unset API key)."""


class IngestionRequestError(IngestionError):
    """The HTTP request itself failed: a network error or a non-2xx status."""


class IngestionRateLimitError(IngestionRequestError):
    """The provider returned a rate-limit response (e.g. HTTP 429)."""


class IngestionResponseError(IngestionError):
    """The response was not valid, complete data for what was requested."""


class IngestionStaleDataError(IngestionError):
    """The data's own as-of timestamp is older than the configured maximum age."""
