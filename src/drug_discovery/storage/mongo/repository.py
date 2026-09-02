"""MongoDB paper document repository using pymongo.

Full paper abstracts and complete document data are stored here.
PostgreSQL holds only the searchable metadata (title, year, journal).
"""

import logging
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from drug_discovery.models.paper import Paper
from drug_discovery.storage.base import PaperRepository

logger = logging.getLogger(__name__)

COLLECTION_NAME = "papers"


class MongoPaperRepository(PaperRepository):
    """Paper full-document repository backed by MongoDB.

    Stores the complete paper record including full abstract, authors,
    and keywords — data that doesn't benefit from SQL constraints.

    Args:
        mongo_url: MongoDB connection string.
        db_name: Target database name.
    """

    def __init__(self, mongo_url: str, db_name: str = "drug_discovery") -> None:
        self._client: MongoClient[Any] = MongoClient(mongo_url)
        self._col: Collection[Any] = self._client[db_name][COLLECTION_NAME]
        self._col.create_index("pmid", unique=True, background=True)

    async def save(self, paper: Paper) -> None:
        """Upsert a full paper document.

        Args:
            paper: Paper domain model including abstract and authors.
        """
        doc = {
            "pmid": paper.pmid,
            "title": paper.title,
            "abstract": paper.abstract,
            "authors": paper.authors,
            "journal": paper.journal,
            "year": paper.year,
            "keywords": paper.keywords,
            "doi": paper.doi,
        }
        self._col.replace_one({"pmid": paper.pmid}, doc, upsert=True)
        logger.debug("mongo: upserted paper PMID %s", paper.pmid)

    async def get(self, pmid: str) -> Paper | None:
        """Retrieve a full paper document by PMID.

        Args:
            pmid: PubMed identifier.

        Returns:
            Paper with all fields populated, or None if not found.
        """
        doc = self._col.find_one({"pmid": pmid}, {"_id": 0})
        if doc is None:
            return None
        return Paper(**doc)

    async def list_by_year(self, year: int) -> list[Paper]:
        """List all papers published in a given year.

        Args:
            year: Publication year.

        Returns:
            List of Paper objects.
        """
        cursor = self._col.find({"year": year}, {"_id": 0})
        return [Paper(**doc) for doc in cursor]

    def close(self) -> None:
        """Close the MongoDB connection."""
        self._client.close()
