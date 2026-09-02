"""Request and response schemas for the FastAPI application."""

from pydantic import BaseModel, field_validator

from drug_discovery.models.compound import ApprovalStatus


class SemanticSearchRequest(BaseModel):
    """Request body for POST /search/semantic.

    Args:
        query: Natural language search query (encoded to a vector).
        limit: Maximum number of results to return.
    """

    query: str
    limit: int = 10

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Reject blank queries."""
        if not v.strip():
            raise ValueError("query cannot be empty")
        return v


class PaperSummary(BaseModel):
    """Lightweight paper summary returned from search results."""

    pmid: str
    title: str
    journal: str
    year: int
    score: float


class SemanticSearchResponse(BaseModel):
    """Response body for POST /search/semantic."""

    query: str
    results: list[PaperSummary]
    total: int


class CompoundResponse(BaseModel):
    """Response body for GET /compounds/{compound_id}."""

    compound_id: str
    name: str
    approval_status: ApprovalStatus
    indications: list[str]
    molecular_formula: str | None = None


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str = "ok"
    databases: dict[str, str] = {}
