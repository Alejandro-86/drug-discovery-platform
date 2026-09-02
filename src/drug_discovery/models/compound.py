"""Domain model for drug compounds."""

from enum import StrEnum
from pydantic import BaseModel, field_validator


class ApprovalStatus(StrEnum):
    """FDA/regulatory approval status for a compound."""

    APPROVED = "approved"
    INVESTIGATIONAL = "investigational"
    WITHDRAWN = "withdrawn"
    EXPERIMENTAL = "experimental"


class Compound(BaseModel):
    """A drug compound record.

    Stored in PostgreSQL for structured queries and joins.

    Args:
        compound_id: External identifier (e.g. DrugBank ID 'DB00331').
        name: Generic compound name.
        approval_status: Current regulatory status.
        indications: List of approved or investigated indications.
        molecular_formula: Chemical formula if known.
        smiles: SMILES string representation if available.
    """

    compound_id: str
    name: str
    approval_status: ApprovalStatus
    indications: list[str] = []
    molecular_formula: str | None = None
    smiles: str | None = None

    @field_validator("compound_id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        """Reject blank compound IDs."""
        if not v.strip():
            raise ValueError("compound_id cannot be empty")
        return v
