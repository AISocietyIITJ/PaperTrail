# PaperTrail

PaperTrail is a research-professor discovery pipeline. It extracts research interests from a user query, searches matching research-topic vectors in Pinecone, and returns connected professors from a Neo4j Aura knowledge graph.

```text
User query
   -> Local LLM extracts research topics
   -> SentenceTransformer creates query embedding
   -> Pinecone finds matching research-topic vectors
   -> Neo4j returns professors connected to those topics
```

## Highlights

- Natural-language research query input
- Local Ollama-based topic extraction
- Research-interest alias generation
- SentenceTransformer embeddings
- Pinecone vector search
- Neo4j Aura graph ingestion and professor lookup
- CSV-backed professor and research-topic data

## Tech Stack

| Layer | Tool |
| --- | --- |
| Language | Python |
| LLM runtime | Ollama |
| Embeddings | sentence-transformers |
| Vector database | Pinecone |
| Graph database | Neo4j Aura |
| Data files | CSV |

## Project Structure

```text
.
|-- main.py                         # Interactive professor discovery console
|-- setup.py                        # End-to-end data setup pipeline
|-- config.py                       # Environment variable loading
|-- requirements.txt                # Python dependencies
|-- data/
|   |-- professor_updated1.csv      # Professor source data
|   `-- interests_with_aliases.csv  # Generated interests, aliases, vector IDs
`-- src/
    |-- embedding/
    |   |-- generate_alias.py
    |   |-- generate_embedding.py
    |   `-- generate_embedding_prof.py
    |-- ingestion/
    |   |-- load_reaseach_node.py
    |   |-- load_proffesor.py
    |   `-- test_queries.py
    |-- local_llm/
    |   |-- client.py
    |   |-- extractor.py
    |   |-- prompts.py
    |   `-- query.py
    `-- utils/
        |-- get_prof_info.py
        `-- vec_query_search.py
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
PINECONE_API=your_pinecone_api_key
AURA_URI=neo4j+s://your_instance_id.databases.neo4j.io
AURA_USER=your_neo4j_username
AURA_PASSWORD=your_neo4j_password
```

### 4. Start Ollama

The main query flow uses the local Ollama client at `http://localhost:11434` with the `qwen2.5:3b` model.

```bash
ollama serve
ollama pull qwen2.5:3b
```

## Build The Data Pipeline

Run the setup script to generate aliases, create embeddings, upsert vectors to Pinecone, and ingest graph data into Neo4j.

```bash
python setup.py
```

The setup flow runs these stages:

| Step | Action |
| --- | --- |
| 1 | Generate aliases for research interests |
| 2 | Generate research-topic embeddings |
| 3 | Generate professor-profile embeddings |
| 4 | Ingest research-topic nodes into Neo4j |
| 5 | Ingest professor nodes and `WORKS_IN` edges |

## Run The Discovery Console

```bash
python main.py
```

Example query:

```text
Suggest professors working in computer vision, biometrics, and deep learning.
```

PaperTrail will:

1. Extract the research topics from the query.
2. Search similar research vectors in Pinecone.
3. Query Neo4j for professors connected to those topics.
4. Print matching professor profiles in the terminal.

## Data Flow

### Alias generation

`src/embedding/generate_alias.py` reads professor interests from `data/professor_updated1.csv`, normalizes unique topics, generates aliases, and writes them to `data/interests_with_aliases.csv`.

### Embedding generation

`src/embedding/generate_embedding.py` embeds research interests and aliases into the `academic-interests` Pinecone index.

`src/embedding/generate_embedding_prof.py` embeds professor profiles into the `prof-profile` Pinecone index.

### Graph ingestion

`src/ingestion/load_reaseach_node.py` creates `ResearchTopic` nodes.

`src/ingestion/load_proffesor.py` creates `Professor` nodes and connects them to matching research topics with `WORKS_IN` relationships.

### Querying

`main.py` uses:

- `src/local_llm/extractor.py` to extract topics
- `src/utils/vec_query_search.py` to search Pinecone
- `src/utils/get_prof_info.py` to query Neo4j

## Verify Ingestion

After running setup, you can check graph counts with:

```bash
python src/ingestion/test_queries.py
```

This prints the number of professor nodes, research-topic nodes, graph edges, and unconnected topics.

## Troubleshooting

| Problem | Check |
| --- | --- |
| Ollama connection fails | Make sure `ollama serve` is running |
| Model not found | Run `ollama pull qwen2.5:3b` |
| Pinecone errors | Confirm `PINECONE_API` is set in `.env` |
| Neo4j authentication errors | Confirm `AURA_URI`, `AURA_USER`, and `AURA_PASSWORD` |
| Empty professor results | Run `python setup.py` and verify graph ingestion |
| Missing CSV columns | Check the files in `data/` match the expected column names |

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
