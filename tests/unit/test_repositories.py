"""Unit tests for storage repository interfaces.

Tests use in-memory stubs — no running databases required.
"""

from drug_discovery.models.compound import ApprovalStatus, Compound
from drug_discovery.models.entity import (
    Disease,
    EntityRelationship,
    Protein,
    RelationType,
)
from drug_discovery.models.paper import Paper
from drug_discovery.storage.base import (
    CompoundRepository,
    EntityRepository,
    PaperRepository,
)


def _compound(cid: str = "DB00331") -> Compound:
    return Compound(compound_id=cid, name="Metformin",
                    approval_status=ApprovalStatus.APPROVED)


def _paper(pmid: str = "12345678") -> Paper:
    return Paper(pmid=pmid, title="Metformin study", abstract="Results show...",
                 authors=["Smith J"], journal="Diabetes", year=2023)


def _disease(did: str = "D001") -> Disease:
    return Disease(disease_id=did, name="Type 2 Diabetes", category="metabolic")


def _protein(pid: str = "P001") -> Protein:
    return Protein(protein_id=pid, name="INSR", gene="INSR",
                   function="insulin receptor")


# ─── In-memory stubs ─────────────────────────────────────────────────────────

class InMemoryCompoundRepo(CompoundRepository):
    def __init__(self) -> None:
        self._store: dict[str, Compound] = {}

    async def save(self, compound: Compound) -> None:
        self._store[compound.compound_id] = compound

    async def get(self, compound_id: str) -> Compound | None:
        return self._store.get(compound_id)

    async def list_by_indication(self, indication: str) -> list[Compound]:
        return [c for c in self._store.values() if indication in c.indications]


class InMemoryPaperRepo(PaperRepository):
    def __init__(self) -> None:
        self._store: dict[str, Paper] = {}

    async def save(self, paper: Paper) -> None:
        self._store[paper.pmid] = paper

    async def get(self, pmid: str) -> Paper | None:
        return self._store.get(pmid)

    async def list_by_year(self, year: int) -> list[Paper]:
        return [p for p in self._store.values() if p.year == year]


class InMemoryEntityRepo(EntityRepository):
    def __init__(self) -> None:
        self._diseases: dict[str, Disease] = {}
        self._proteins: dict[str, Protein] = {}
        self._rels: list[EntityRelationship] = []

    async def save_disease(self, disease: Disease) -> None:
        self._diseases[disease.disease_id] = disease

    async def save_protein(self, protein: Protein) -> None:
        self._proteins[protein.protein_id] = protein

    async def save_relationship(self, rel: EntityRelationship) -> None:
        self._rels.append(rel)

    async def get_relationships(
        self, source_id: str, relation_type: RelationType | None = None
    ) -> list[EntityRelationship]:
        rels = [r for r in self._rels if r.source_id == source_id]
        if relation_type:
            rels = [r for r in rels if r.relation_type == relation_type]
        return rels


# ─── Compound repository tests ───────────────────────────────────────────────

class TestCompoundRepository:
    async def test_save_and_retrieve(self) -> None:
        repo = InMemoryCompoundRepo()
        compound = _compound()
        await repo.save(compound)
        result = await repo.get("DB00331")
        assert result is not None
        assert result.name == "Metformin"

    async def test_get_missing_returns_none(self) -> None:
        repo = InMemoryCompoundRepo()
        assert await repo.get("MISSING") is None

    async def test_list_by_indication(self) -> None:
        repo = InMemoryCompoundRepo()
        c = Compound(compound_id="DB00331", name="Metformin",
                     approval_status=ApprovalStatus.APPROVED,
                     indications=["Type 2 Diabetes"])
        await repo.save(c)
        results = await repo.list_by_indication("Type 2 Diabetes")
        assert len(results) == 1

    async def test_save_overwrites_existing(self) -> None:
        repo = InMemoryCompoundRepo()
        await repo.save(_compound())
        updated = Compound(compound_id="DB00331", name="Metformin HCl",
                           approval_status=ApprovalStatus.APPROVED)
        await repo.save(updated)
        result = await repo.get("DB00331")
        assert result is not None
        assert result.name == "Metformin HCl"


# ─── Paper repository tests ───────────────────────────────────────────────────

class TestPaperRepository:
    async def test_save_and_retrieve(self) -> None:
        repo = InMemoryPaperRepo()
        await repo.save(_paper())
        result = await repo.get("12345678")
        assert result is not None
        assert result.title == "Metformin study"

    async def test_list_by_year(self) -> None:
        repo = InMemoryPaperRepo()
        await repo.save(_paper("11111111"))
        await repo.save(Paper(pmid="22222222", title="t2", abstract="a",
                               authors=[], journal="j", year=2022))
        results = await repo.list_by_year(2023)
        assert len(results) == 1


# ─── Entity repository tests ──────────────────────────────────────────────────

class TestEntityRepository:
    async def test_save_and_query_relationships(self) -> None:
        repo = InMemoryEntityRepo()
        await repo.save_disease(_disease())
        await repo.save_protein(_protein())
        rel = EntityRelationship(source_id="DB00331", target_id="P001",
                                  relation_type=RelationType.TARGETS)
        await repo.save_relationship(rel)
        rels = await repo.get_relationships("DB00331")
        assert len(rels) == 1

    async def test_filter_by_relation_type(self) -> None:
        repo = InMemoryEntityRepo()
        await repo.save_relationship(EntityRelationship(
            source_id="DB00331", target_id="P001", relation_type=RelationType.TARGETS))
        await repo.save_relationship(EntityRelationship(
            source_id="DB00331", target_id="D001", relation_type=RelationType.TREATS))
        treats = await repo.get_relationships("DB00331", RelationType.TREATS)
        assert len(treats) == 1
        assert treats[0].relation_type == RelationType.TREATS
