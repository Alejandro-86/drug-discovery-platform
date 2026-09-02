"""FastAPI application — unified query layer over all four databases."""

from fastapi import FastAPI, HTTPException

from drug_discovery.api.schemas import (
    CompoundResponse,
    HealthResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    PaperSummary,
)

app = FastAPI(
    title="drug-discovery-platform",
    description=(
        "Unified query layer over PostgreSQL, MongoDB, Neo4j, and Qdrant "
        "for drug discovery data."
    ),
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health.

    In production this would ping each database.
    """
    return HealthResponse(
        status="ok",
        databases={
            "postgres": "configured",
            "mongodb": "configured",
            "neo4j": "configured",
            "qdrant": "configured",
        },
    )


@app.post("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest) -> SemanticSearchResponse:
    """Semantic search over paper abstracts via Qdrant vector similarity.

    Encodes the query with sentence-transformers (all-MiniLM-L6-v2) and
    returns the nearest papers by cosine similarity.
    """
    # In production: inject encoder and qdrant_repo via dependency injection
    # Stub response for API contract demonstration
    return SemanticSearchResponse(
        query=request.query,
        results=[],
        total=0,
    )


@app.get("/compounds/{compound_id}", response_model=CompoundResponse)
async def get_compound(compound_id: str) -> CompoundResponse:
    """Retrieve a compound by ID from PostgreSQL.

    Args:
        compound_id: DrugBank or OpenFDA application number.
    """
    # In production: inject postgres_repo via dependency injection
    raise HTTPException(status_code=404, detail=f"compound '{compound_id}' not found")
