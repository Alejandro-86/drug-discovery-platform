"""Domain model for research papers from PubMed."""

from pydantic import BaseModel, field_validator


class Paper(BaseModel):
    """A research paper record.

    Metadata stored in PostgreSQL; full text stored in MongoDB;
    abstract embedding stored in Qdrant for semantic search.

    Args:
        pmid: PubMed identifier (numeric string).
        title: Paper title.
        abstract: Full abstract text.
        authors: Author list in 'Surname Initial' format.
        journal: Journal name.
        year: Publication year.
        keywords: MeSH or author keywords.
        doi: Digital Object Identifier if available.
        embedding: Abstract embedding vector (set after encoding, not stored here).
    """

    pmid: str
    title: str
    abstract: str
    authors: list[str]
    journal: str
    year: int
    keywords: list[str] = []
    doi: str | None = None
    embedding: list[float] | None = None

    @field_validator("pmid")
    @classmethod
    def pmid_numeric(cls, v: str) -> str:
        """PubMed IDs are numeric strings."""
        if not v.isdigit():
            raise ValueError(f"pmid must be numeric, got '{v}'")
        return v
