"""PubMed ingestion pipeline using the NCBI E-utilities API.

Fetches research papers matching a query, parses the XML response,
and returns Paper domain objects ready for multi-DB storage.
"""

import logging
import xml.etree.ElementTree as ET

import httpx

from drug_discovery.models.paper import Paper

logger = logging.getLogger(__name__)

_BASE     = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_ESEARCH  = f"{_BASE}/esearch.fcgi"
_EFETCH   = f"{_BASE}/efetch.fcgi"


class PubMedIngester:
    """Ingests biomedical papers from PubMed E-utilities.

    Args:
        api_key: Optional NCBI API key for higher rate limits.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(self, api_key: str | None = None, timeout: float = 15.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    async def ingest(self, query: str, max_results: int = 20) -> list[Paper]:
        """Search PubMed and fetch full records for matching papers.

        Args:
            query: PubMed query string.
            max_results: Maximum number of papers to fetch.

        Returns:
            List of Paper objects with titles, abstracts, authors, and metadata.
        """
        pmids = await self._search(query, max_results)
        if not pmids:
            return []

        papers = await self._fetch(pmids)
        logger.info("pubmed: ingested %d papers for query '%s'", len(papers), query)
        return papers

    async def _search(self, query: str, max_results: int) -> list[str]:
        """Call esearch and return a list of PMIDs."""
        params: dict[str, str] = {
            "retmode": "xml", "db": "pubmed",
            "term": query, "retmax": str(max_results),
        }
        if self._api_key:
            params["api_key"] = self._api_key

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(_ESEARCH, params=params)
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        return [el.text for el in root.findall(".//Id") if el.text]

    async def _fetch(self, pmids: list[str]) -> list[Paper]:
        """Call efetch for a list of PMIDs and parse the results."""
        params: dict[str, str] = {
            "retmode": "xml", "db": "pubmed",
            "id": ",".join(pmids), "rettype": "abstract",
        }
        if self._api_key:
            params["api_key"] = self._api_key

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(_EFETCH, params=params)
            resp.raise_for_status()

        return self._parse_fetch(resp.text)

    def _parse_fetch(self, xml_text: str) -> list[Paper]:
        """Parse efetch XML response into Paper objects."""
        root = ET.fromstring(xml_text)
        papers: list[Paper] = []

        for article_el in root.findall(".//PubmedArticle"):
            citation = article_el.find("MedlineCitation")
            if citation is None:
                continue

            pmid_el = citation.find("PMID")
            if pmid_el is None or not pmid_el.text:
                continue

            art = citation.find("Article")
            if art is None:
                continue

            title = art.findtext("ArticleTitle") or ""
            abstract_parts = [
                el.text or "" for el in art.findall(".//AbstractText")
            ]
            abstract = " ".join(p for p in abstract_parts if p).strip()
            if not abstract:
                abstract = "No abstract available."

            authors: list[str] = []
            for a in art.findall(".//Author"):
                last  = a.findtext("LastName") or ""
                init  = a.findtext("Initials") or ""
                if last:
                    authors.append(f"{last} {init}".strip())

            journal  = art.findtext(".//Journal/Title") or ""
            year_str = art.findtext(".//JournalIssue/PubDate/Year") or "1900"
            doi      = art.findtext(".//ELocationID[@EIdType='doi']")

            papers.append(Paper(
                pmid=pmid_el.text,
                title=title,
                abstract=abstract,
                authors=authors,
                journal=journal,
                year=int(year_str),
                doi=doi,
            ))

        return papers
