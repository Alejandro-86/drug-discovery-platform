"""Entry point for the ingestion pipeline.

Runs PubMed and OpenFDA ingestion for a configurable set of drug queries
and stores results across all four databases.

Usage:
    python -m drug_discovery.ingestion.run
"""

import asyncio
import logging

from drug_discovery.config import settings
from drug_discovery.ingestion.openfda import OpenFDAIngester
from drug_discovery.ingestion.pubmed import PubMedIngester

logger = logging.getLogger(__name__)

QUERIES = [
    "metformin diabetes",
    "donepezil alzheimer",
    "lisinopril hypertension",
    "atorvastatin cholesterol",
]


async def run_ingestion() -> None:
    """Run the full ingestion pipeline for all configured queries."""
    pubmed_ingester  = PubMedIngester(api_key=settings.ncbi_api_key or None)
    openfda_ingester = OpenFDAIngester()

    for query in QUERIES:
        logger.info("ingesting: %s", query)

        papers = await pubmed_ingester.ingest(query, max_results=settings.pubmed_max_results)
        logger.info("  pubmed: %d papers", len(papers))

        compounds = await openfda_ingester.ingest(query.split()[0], limit=10)
        logger.info("  openfda: %d compounds", len(compounds))

        # Storage calls would go here once DB connections are wired
        # e.g. await paper_repo.save(paper) for paper in papers


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingestion())
