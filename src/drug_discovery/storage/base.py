"""Abstract repository interfaces for all four storage layers.

Concrete implementations live in storage/{postgres,mongo,neo4j_db,qdrant_db}/.
Tests use in-memory stubs — no running databases required.
"""

from abc import ABC, abstractmethod

from drug_discovery.models.compound import Compound
from drug_discovery.models.entity import Disease, EntityRelationship, Protein, RelationType
from drug_discovery.models.paper import Paper


class CompoundRepository(ABC):
    """Repository interface for drug compounds (PostgreSQL)."""

    @abstractmethod
    async def save(self, compound: Compound) -> None:
        """Persist a compound record, replacing any existing record with the same ID."""

    @abstractmethod
    async def get(self, compound_id: str) -> Compound | None:
        """Retrieve a compound by ID, or None if not found."""

    @abstractmethod
    async def list_by_indication(self, indication: str) -> list[Compound]:
        """List all compounds with a matching indication."""


class PaperRepository(ABC):
    """Repository interface for research papers.

    Metadata in PostgreSQL; full document in MongoDB; embeddings in Qdrant.
    Implementations may write to one or more backends.
    """

    @abstractmethod
    async def save(self, paper: Paper) -> None:
        """Persist a paper record."""

    @abstractmethod
    async def get(self, pmid: str) -> Paper | None:
        """Retrieve a paper by PMID, or None if not found."""

    @abstractmethod
    async def list_by_year(self, year: int) -> list[Paper]:
        """List papers published in a given year."""


class EntityRepository(ABC):
    """Repository interface for biological entities and relationships (Neo4j)."""

    @abstractmethod
    async def save_disease(self, disease: Disease) -> None:
        """Persist a disease node."""

    @abstractmethod
    async def save_protein(self, protein: Protein) -> None:
        """Persist a protein node."""

    @abstractmethod
    async def save_relationship(self, rel: EntityRelationship) -> None:
        """Persist a directed relationship between two entities."""

    @abstractmethod
    async def get_relationships(
        self,
        source_id: str,
        relation_type: RelationType | None = None,
    ) -> list[EntityRelationship]:
        """Retrieve relationships from a source entity, optionally filtered by type."""


class VectorRepository(ABC):
    """Repository interface for paper embeddings (Qdrant)."""

    @abstractmethod
    async def upsert(self, pmid: str, embedding: list[float], payload: dict[str, object]) -> None:
        """Insert or update an embedding vector with metadata payload."""

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Find the nearest neighbours to a query vector."""
