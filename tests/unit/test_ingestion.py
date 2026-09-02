"""Unit tests for ingestion pipelines — PubMed and OpenFDA.

All HTTP calls mocked with pytest-httpx.
"""

from pytest_httpx import HTTPXMock

from drug_discovery.ingestion.openfda import OpenFDAIngester
from drug_discovery.ingestion.pubmed import PubMedIngester

PUBMED_SEARCH = """<?xml version="1.0"?>
<eSearchResult>
  <Count>1</Count>
  <IdList><Id>12345678</Id></IdList>
</eSearchResult>"""

PUBMED_FETCH = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Metformin reduces glucose in type 2 diabetes</ArticleTitle>
        <Abstract><AbstractText>Metformin is first-line treatment.</AbstractText></Abstract>
        <AuthorList>
          <Author><LastName>Smith</LastName><Initials>J</Initials></Author>
        </AuthorList>
        <Journal>
          <Title>Diabetes Care</Title>
          <JournalIssue><PubDate><Year>2023</Year></PubDate></JournalIssue>
        </Journal>
        <ELocationID EIdType="doi">10.1234/dc.2023</ELocationID>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""

OPENFDA_RESPONSE = """{
  "results": [{
    "openfda": {
      "brand_name": ["GLUCOPHAGE"],
      "generic_name": ["METFORMIN HYDROCHLORIDE"],
      "application_number": ["NDA020357"]
    },
    "indications_and_usage": ["For the treatment of type 2 diabetes."]
  }]
}"""


class TestPubMedIngester:
    async def test_ingest_returns_papers(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(text=PUBMED_SEARCH)
        httpx_mock.add_response(text=PUBMED_FETCH)
        ingester = PubMedIngester()
        papers = await ingester.ingest(query="metformin diabetes", max_results=1)
        assert len(papers) == 1
        assert papers[0].pmid == "12345678"
        assert papers[0].year == 2023

    async def test_ingest_empty_query_returns_empty(self, httpx_mock: HTTPXMock) -> None:
        empty_xml = (
            "<?xml version='1.0'?>"
            "<eSearchResult><Count>0</Count><IdList></IdList></eSearchResult>"
        )
        httpx_mock.add_response(text=empty_xml)
        ingester = PubMedIngester()
        papers = await ingester.ingest(query="zzz_nonexistent_zzz")
        assert papers == []

    async def test_paper_has_required_fields(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(text=PUBMED_SEARCH)
        httpx_mock.add_response(text=PUBMED_FETCH)
        ingester = PubMedIngester()
        papers = await ingester.ingest(query="metformin", max_results=1)
        p = papers[0]
        assert p.title != ""
        assert p.abstract != ""
        assert p.journal == "Diabetes Care"


class TestOpenFDAIngester:
    async def test_ingest_returns_compounds(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(text=OPENFDA_RESPONSE)
        ingester = OpenFDAIngester()
        compounds = await ingester.ingest(query="metformin", limit=1)
        assert len(compounds) == 1
        assert "metformin" in compounds[0].name.lower()

    async def test_compound_has_indication(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(text=OPENFDA_RESPONSE)
        ingester = OpenFDAIngester()
        compounds = await ingester.ingest(query="metformin", limit=1)
        assert len(compounds[0].indications) > 0

    async def test_ingest_handles_empty_results(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(text='{"results": []}')
        ingester = OpenFDAIngester()
        compounds = await ingester.ingest(query="xyz_nonexistent")
        assert compounds == []
