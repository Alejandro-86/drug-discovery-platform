"""Neo4j knowledge graph repository for biological entities and relationships.

Models the drug discovery knowledge graph:
  (:Drug)-[:TARGETS]->(:Protein)
  (:Drug)-[:TREATS]->(:Disease)
  (:Disease)-[:ASSOCIATED_WITH]->(:Protein)
  (:Disease)-[:COMORBID_WITH]->(:Disease)
"""

import logging
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from drug_discovery.models.entity import (
    Disease,
    EntityRelationship,
    Protein,
    RelationType,
)
from drug_discovery.storage.base import EntityRepository

logger = logging.getLogger(__name__)


class Neo4jEntityRepository(EntityRepository):
    """Entity and relationship repository backed by Neo4j.

    Uses MERGE throughout so the loader is idempotent — safe to re-run.

    Args:
        uri: Neo4j Bolt URI (e.g. 'bolt://localhost:7687').
        user: Neo4j username.
        password: Neo4j password.
    """

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            uri, auth=(user, password)
        )

    async def save_disease(self, disease: Disease) -> None:
        """MERGE a Disease node into the graph.

        Args:
            disease: Disease domain model.
        """
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (d:Disease {id: $id})
                SET d.name     = $name,
                    d.category = $category,
                    d.mesh_id  = $mesh_id
                """,
                id=disease.disease_id,
                name=disease.name,
                category=disease.category,
                mesh_id=disease.mesh_id,
            )

    async def save_protein(self, protein: Protein) -> None:
        """MERGE a Protein node into the graph.

        Args:
            protein: Protein domain model.
        """
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (p:Protein {id: $id})
                SET p.name      = $name,
                    p.gene      = $gene,
                    p.function  = $function,
                    p.uniprot   = $uniprot
                """,
                id=protein.protein_id,
                name=protein.name,
                gene=protein.gene,
                function=protein.function,
                uniprot=protein.uniprot_id,
            )

    async def save_relationship(self, rel: EntityRelationship) -> None:
        """MERGE a directed relationship between two entities.

        Args:
            rel: EntityRelationship with source, target, type, and evidence score.
        """
        async with self._driver.session() as session:
            await session.run(
                f"""
                MATCH (src {{id: $source_id}})
                MATCH (tgt {{id: $target_id}})
                MERGE (src)-[r:{rel.relation_type.upper()}]->(tgt)
                SET r.evidence_score = $score,
                    r.source_pmids   = $pmids
                """,
                source_id=rel.source_id,
                target_id=rel.target_id,
                score=rel.evidence_score,
                pmids=rel.source_pmids,
            )

    async def get_relationships(
        self,
        source_id: str,
        relation_type: RelationType | None = None,
    ) -> list[EntityRelationship]:
        """Retrieve outgoing relationships from a source node.

        Args:
            source_id: ID of the source entity.
            relation_type: Optional filter by relationship type.

        Returns:
            List of EntityRelationship objects.
        """
        rel_filter = (
            f":{relation_type.upper()}"
            if relation_type
            else ""
        )
        query = f"""
            MATCH (src {{id: $source_id}})-[r{rel_filter}]->(tgt)
            RETURN type(r) AS rel_type,
                   tgt.id  AS target_id,
                   r.evidence_score AS score,
                   r.source_pmids   AS pmids
        """
        async with self._driver.session() as session:
            result = await session.run(query, source_id=source_id)
            records = await result.data()

        return [
            EntityRelationship(
                source_id=source_id,
                target_id=rec["target_id"],
                relation_type=RelationType(rec["rel_type"].lower()),
                evidence_score=rec.get("score", 1.0),
                source_pmids=rec.get("pmids") or [],
            )
            for rec in records
        ]

    async def close(self) -> None:
        """Close the Neo4j driver connection."""
        await self._driver.close()
