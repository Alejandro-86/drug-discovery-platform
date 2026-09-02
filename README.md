# drug-discovery-platform

An end-to-end data engineering platform for drug discovery, demonstrating
production patterns across four complementary database technologies.

## Architecture

```
PubMed API ──┐
             ├──► Ingestion layer ──► PostgreSQL  (structured metadata)
OpenFDA  ────┘                   ──► MongoDB      (full documents)
                                 ──► Neo4j        (knowledge graph)
                                 ──► Qdrant       (semantic search)
                                          │
                                 FastAPI unified query layer
```

## Why four databases?

| Database   | Technology     | What it stores                          | Why this DB                        |
|------------|----------------|-----------------------------------------|------------------------------------|
| SQL        | PostgreSQL     | Compounds, trials, structured metadata  | ACID, joins, analytical queries    |
| NoSQL      | MongoDB        | Full paper abstracts, documents         | Flexible schema, document storage  |
| Graph      | Neo4j          | Drug→Protein→Disease relationships      | Traversal, knowledge graph queries |
| Vector     | Qdrant         | Paper embeddings for semantic search    | Similarity search, RAG retrieval   |

## Quickstart

```bash
# Start all databases
make up

# Install dependencies
make install

# Run database migrations (PostgreSQL)
make migrate

# Run ingestion pipeline
make ingest

# Start API
make run
# → http://localhost:8000/docs
```

## Data sources

- **PubMed** — NCBI E-utilities API (free, no key required for basic use)
- **OpenFDA** — FDA drug data API (free, no key required)

## Project structure

```
src/drug_discovery/
├── models/      Pydantic domain models
├── storage/
│   ├── postgres/   SQLAlchemy ORM + Alembic migrations
│   ├── mongo/      pymongo document repository
│   ├── neo4j_db/   Neo4j graph repository
│   └── qdrant_db/  Qdrant vector repository + encoder
├── ingestion/   PubMed + OpenFDA ingestion pipelines
├── embeddings/  sentence-transformers encoder (all-MiniLM-L6-v2)
└── api/         FastAPI unified query layer
```
