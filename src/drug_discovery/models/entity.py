"""Domain models for biological entities and their relationships.

Entities (diseases, proteins) and their relationships are stored in Neo4j
as a knowledge graph, enabling traversal queries for drug repurposing and
target identification.
"""

from enum import StrEnum

from pydantic import BaseModel, field_validator


class RelationType(StrEnum):
    """Type of relationship between two biological entities."""

    TARGETS = "targets"
    TREATS = "treats"
    ASSOCIATED_WITH = "associated_with"
    COMORBID_WITH = "comorbid_with"
    INHIBITS = "inhibits"
    ACTIVATES = "activates"


class Disease(BaseModel):
    """A disease or condition.

    Args:
        disease_id: Internal identifier (e.g. 'D001').
        name: Disease name.
        category: Broad disease category (e.g. 'metabolic', 'neurological').
        mesh_id: MeSH ontology ID if available.
    """

    disease_id: str
    name: str
    category: str
    mesh_id: str | None = None

    @field_validator("disease_id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        """Reject blank entity IDs."""
        if not v.strip():
            raise ValueError("disease_id cannot be empty")
        return v


class Protein(BaseModel):
    """A protein or gene target.

    Args:
        protein_id: Internal identifier.
        name: Protein name.
        gene: Gene symbol (e.g. 'INSR', 'ACE').
        function: Short description of protein function.
        uniprot_id: UniProt accession if available.
    """

    protein_id: str
    name: str
    gene: str
    function: str
    uniprot_id: str | None = None


class EntityRelationship(BaseModel):
    """A directed relationship between two biological entities.

    Stored as a Neo4j edge with properties.

    Args:
        source_id: ID of the source entity (compound, disease, or protein).
        target_id: ID of the target entity.
        relation_type: Type of biological relationship.
        evidence_score: Confidence score in [0.0, 1.0].
        source_pmids: PMIDs of papers supporting this relationship.
    """

    source_id: str
    target_id: str
    relation_type: RelationType
    evidence_score: float = 1.0
    source_pmids: list[str] = []

    @field_validator("evidence_score")
    @classmethod
    def score_bounded(cls, v: float) -> float:
        """Evidence score must be in [0, 1]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"evidence_score must be in [0, 1], got {v}")
        return v
