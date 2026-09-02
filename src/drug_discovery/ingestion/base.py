"""Abstract base class for data ingesters."""

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class BaseIngester(ABC):
    """Base class for all ingestion sources.

    Concrete ingesters pull data from an external API and return
    a list of domain model objects ready for storage.
    """

    @abstractmethod
    async def ingest(self, query: str, **kwargs: object) -> list[object]:
        """Fetch and parse records matching the given query.

        Args:
            query: Search query or term to ingest.
            **kwargs: Source-specific parameters (limit, max_results, etc.).

        Returns:
            List of domain model objects.
        """
