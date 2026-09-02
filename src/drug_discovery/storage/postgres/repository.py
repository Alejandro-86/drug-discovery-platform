"""PostgreSQL compound and paper metadata repository using SQLAlchemy."""

import json
from typing import Any

from sqlalchemy import Column, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column

from drug_discovery.models.compound import Compound, ApprovalStatus
from drug_discovery.models.paper import Paper
from drug_discovery.storage.base import CompoundRepository, PaperRepository


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""


class CompoundRow(Base):
    """ORM representation of a compound record in PostgreSQL.

    Stores structured metadata suitable for analytical joins and filtering.
    Indications stored as a JSON array for simplicity.
    """

    __tablename__ = "compounds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    compound_id = mapped_column(String(64), unique=True, nullable=False, index=True)
    name = mapped_column(String(256), nullable=False)
    approval_status = mapped_column(String(32), nullable=False)
    indications = mapped_column(Text, nullable=False, default="[]")
    molecular_formula = mapped_column(String(128), nullable=True)
    smiles = mapped_column(Text, nullable=True)


class PaperRow(Base):
    """ORM representation of paper metadata in PostgreSQL.

    Full abstract text is stored in MongoDB; only metadata here for joins.
    """

    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pmid = mapped_column(String(16), unique=True, nullable=False, index=True)
    title = mapped_column(Text, nullable=False)
    journal = mapped_column(String(256), nullable=False)
    year = mapped_column(Integer, nullable=False, index=True)
    doi = mapped_column(String(256), nullable=True)


class PostgresCompoundRepository(CompoundRepository):
    """Compound repository backed by PostgreSQL via SQLAlchemy async.

    Args:
        session: Active AsyncSession — caller owns lifecycle.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, compound: Compound) -> None:
        """Upsert a compound record."""
        existing = await self._session.execute(
            select(CompoundRow).where(CompoundRow.compound_id == compound.compound_id)
        )
        row = existing.scalar_one_or_none()

        if row is None:
            row = CompoundRow(compound_id=compound.compound_id)
            self._session.add(row)

        row.name = compound.name
        row.approval_status = compound.approval_status.value
        row.indications = json.dumps(compound.indications)
        row.molecular_formula = compound.molecular_formula
        row.smiles = compound.smiles
        await self._session.flush()

    async def get(self, compound_id: str) -> Compound | None:
        """Retrieve a compound by ID."""
        result = await self._session.execute(
            select(CompoundRow).where(CompoundRow.compound_id == compound_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _row_to_compound(row)

    async def list_by_indication(self, indication: str) -> list[Compound]:
        """List compounds whose indications contain the given string."""
        result = await self._session.execute(select(CompoundRow))
        rows = result.scalars().all()
        compounds = [_row_to_compound(r) for r in rows]
        return [c for c in compounds if indication in c.indications]


class PostgresPaperRepository(PaperRepository):
    """Paper metadata repository backed by PostgreSQL.

    Args:
        session: Active AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, paper: Paper) -> None:
        """Upsert paper metadata."""
        result = await self._session.execute(
            select(PaperRow).where(PaperRow.pmid == paper.pmid)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = PaperRow(pmid=paper.pmid)
            self._session.add(row)

        row.title = paper.title
        row.journal = paper.journal
        row.year = paper.year
        row.doi = paper.doi
        await self._session.flush()

    async def get(self, pmid: str) -> Paper | None:
        """Retrieve paper metadata by PMID."""
        result = await self._session.execute(
            select(PaperRow).where(PaperRow.pmid == pmid)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return Paper(pmid=row.pmid, title=row.title, abstract="",
                     authors=[], journal=row.journal, year=row.year, doi=row.doi)

    async def list_by_year(self, year: int) -> list[Paper]:
        """List paper metadata for a given publication year."""
        result = await self._session.execute(
            select(PaperRow).where(PaperRow.year == year)
        )
        rows = result.scalars().all()
        return [Paper(pmid=r.pmid, title=r.title, abstract="",
                      authors=[], journal=r.journal, year=r.year, doi=r.doi)
                for r in rows]


def _row_to_compound(row: CompoundRow) -> Compound:
    """Convert a SQLAlchemy ORM row to a domain Compound."""
    return Compound(
        compound_id=row.compound_id,
        name=row.name,
        approval_status=ApprovalStatus(row.approval_status),
        indications=json.loads(row.indications or "[]"),
        molecular_formula=row.molecular_formula,
        smiles=row.smiles,
    )
