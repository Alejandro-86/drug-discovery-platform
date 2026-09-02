"""Unit tests for domain models — written before implementation."""

import pytest

from drug_discovery.models.compound import ApprovalStatus, Compound
from drug_discovery.models.entity import (
    Disease,
    EntityRelationship,
    Protein,
    RelationType,
)
from drug_discovery.models.paper import Paper


class TestCompound:
    def test_compound_stores_core_fields(self) -> None:
        c = Compound(
            compound_id="DB00331",
            name="Metformin",
            approval_status=ApprovalStatus.APPROVED,
            indications=["Type 2 Diabetes"],
            molecular_formula="C4H11N5",
        )
        assert c.compound_id == "DB00331"
        assert c.approval_status == ApprovalStatus.APPROVED
        assert len(c.indications) == 1

    def test_compound_id_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError):
            Compound(compound_id="", name="x",
                     approval_status=ApprovalStatus.APPROVED)

    def test_approval_status_enum_values(self) -> None:
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.INVESTIGATIONAL == "investigational"
        assert ApprovalStatus.WITHDRAWN == "withdrawn"

    def test_indications_default_empty(self) -> None:
        c = Compound(compound_id="DB00001", name="x",
                     approval_status=ApprovalStatus.INVESTIGATIONAL)
        assert c.indications == []

    def test_molecular_formula_optional(self) -> None:
        c = Compound(compound_id="DB00001", name="x",
                     approval_status=ApprovalStatus.APPROVED)
        assert c.molecular_formula is None


class TestPaper:
    def test_paper_stores_pmid_and_abstract(self) -> None:
        p = Paper(
            pmid="12345678",
            title="Metformin mechanisms",
            abstract="Metformin reduces hepatic glucose output.",
            authors=["Smith J"],
            journal="Diabetes",
            year=2023,
        )
        assert p.pmid == "12345678"
        assert "Metformin" in p.abstract

    def test_pmid_must_be_numeric(self) -> None:
        with pytest.raises(ValueError, match="pmid"):
            Paper(pmid="not-numeric", title="t", abstract="a",
                  authors=[], journal="j", year=2020)

    def test_keywords_default_empty(self) -> None:
        p = Paper(pmid="12345678", title="t", abstract="a",
                  authors=[], journal="j", year=2020)
        assert p.keywords == []

    def test_embedding_initially_none(self) -> None:
        p = Paper(pmid="12345678", title="t", abstract="a",
                  authors=[], journal="j", year=2020)
        assert p.embedding is None


class TestDisease:
    def test_disease_stores_name_and_category(self) -> None:
        d = Disease(disease_id="D001", name="Type 2 Diabetes", category="metabolic")
        assert d.disease_id == "D001"
        assert d.category == "metabolic"

    def test_disease_id_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError):
            Disease(disease_id="", name="x", category="y")


class TestProtein:
    def test_protein_stores_gene_and_function(self) -> None:
        p = Protein(protein_id="P001", name="INSR", gene="INSR",
                    function="insulin receptor")
        assert p.gene == "INSR"
        assert p.function == "insulin receptor"


class TestEntityRelationship:
    def test_relationship_stores_source_target_type(self) -> None:
        r = EntityRelationship(
            source_id="DB00331",
            target_id="P001",
            relation_type=RelationType.TARGETS,
            evidence_score=0.95,
        )
        assert r.relation_type == RelationType.TARGETS
        assert r.evidence_score == pytest.approx(0.95)

    def test_relation_type_enum_values(self) -> None:
        assert RelationType.TARGETS == "targets"
        assert RelationType.TREATS == "treats"
        assert RelationType.ASSOCIATED_WITH == "associated_with"

    def test_evidence_score_bounded(self) -> None:
        with pytest.raises(ValueError):
            EntityRelationship(source_id="a", target_id="b",
                               relation_type=RelationType.TREATS,
                               evidence_score=1.5)
