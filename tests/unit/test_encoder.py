"""Unit tests for the embedding encoder — uses a stub to avoid loading the model."""

import pytest

from drug_discovery.embeddings.encoder import VECTOR_DIM, AbstractEncoder


class StubEncoder(AbstractEncoder):
    """Returns a fixed-length zero vector without loading any model."""

    def encode(self, text: str) -> list[float]:
        return [0.0] * VECTOR_DIM

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * VECTOR_DIM for _ in texts]


class TestAbstractEncoder:
    def test_encode_returns_correct_dimension(self) -> None:
        enc = StubEncoder()
        vec = enc.encode("Metformin reduces hepatic glucose production.")
        assert len(vec) == VECTOR_DIM

    def test_encode_batch_returns_multiple_vectors(self) -> None:
        enc = StubEncoder()
        vecs = enc.encode_batch(["text one", "text two", "text three"])
        assert len(vecs) == 3
        assert all(len(v) == VECTOR_DIM for v in vecs)

    def test_encode_empty_string_returns_vector(self) -> None:
        enc = StubEncoder()
        vec = enc.encode("")
        assert len(vec) == VECTOR_DIM

    def test_encode_batch_empty_list(self) -> None:
        enc = StubEncoder()
        assert enc.encode_batch([]) == []


class TestAPISchemas:
    """Test API request/response schema validation."""

    def test_search_request_requires_query(self) -> None:
        from drug_discovery.api.schemas import SemanticSearchRequest
        with pytest.raises((TypeError, ValueError)):
            SemanticSearchRequest()  # type: ignore[call-arg]

    def test_search_request_valid(self) -> None:
        from drug_discovery.api.schemas import SemanticSearchRequest
        req = SemanticSearchRequest(query="metformin diabetes treatment")
        assert req.query == "metformin diabetes treatment"
        assert req.limit == 10  # default

    def test_compound_response(self) -> None:
        from drug_discovery.api.schemas import CompoundResponse
        from drug_discovery.models.compound import ApprovalStatus
        resp = CompoundResponse(
            compound_id="DB00331",
            name="Metformin",
            approval_status=ApprovalStatus.APPROVED,
            indications=["Type 2 Diabetes"],
        )
        assert resp.compound_id == "DB00331"
