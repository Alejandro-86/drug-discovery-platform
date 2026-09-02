"""OpenFDA drug ingestion pipeline.

Fetches approved drug records from the FDA drug label API and converts
them into Compound domain objects.

API docs: https://open.fda.gov/apis/drug/label/
"""

import logging

import httpx

from drug_discovery.models.compound import ApprovalStatus, Compound

logger = logging.getLogger(__name__)

_DRUG_LABEL_URL = "https://api.fda.gov/drug/label.json"


class OpenFDAIngester:
    """Ingests drug compound records from the OpenFDA drug label endpoint.

    Args:
        timeout: HTTP request timeout in seconds.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    async def ingest(self, query: str, limit: int = 20) -> list[Compound]:
        """Fetch drug label records matching a search query.

        Args:
            query: Search term (e.g. 'metformin', 'diabetes').
            limit: Maximum number of records to retrieve.

        Returns:
            List of Compound objects with name, indications, and approval status.
        """
        params = {
            "search": f"openfda.generic_name:{query}",
            "limit": str(limit),
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(_DRUG_LABEL_URL, params=params)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()

        data = resp.json()
        results = data.get("results", [])
        compounds = [self._parse_record(r) for r in results]
        logger.info("openfda: ingested %d compounds for query '%s'", len(compounds), query)
        return [c for c in compounds if c is not None]

    def _parse_record(self, record: dict[str, object]) -> Compound | None:
        """Parse a single drug label record into a Compound.

        Args:
            record: Raw OpenFDA drug label JSON record.

        Returns:
            Compound, or None if required fields are missing.
        """
        openfda = record.get("openfda", {})
        if not isinstance(openfda, dict):
            return None

        generic_names: list[str] = list(openfda.get("generic_name") or [])
        brand_names: list[str] = list(openfda.get("brand_name") or [])
        app_numbers: list[str] = list(openfda.get("application_number") or [])

        name = (generic_names[0] if generic_names else brand_names[0] if brand_names else "")
        name = name.lower()
        if not name:
            return None

        compound_id = app_numbers[0] if app_numbers else f"fda_{name.replace(' ', '_')}"

        indications_raw: list[str] = list(record.get("indications_and_usage") or [])
        indications = [i[:200] for i in indications_raw[:3]]  # cap length

        return Compound(
            compound_id=compound_id,
            name=name.title(),
            approval_status=ApprovalStatus.APPROVED,
            indications=indications,
        )
