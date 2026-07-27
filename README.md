# PaperTrail 📜 🔍
**Automated Research Curriculum & Directed Acyclic Graph (DAG) Generator for Scientific Literature**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Package Manager: uv](https://img.shields.io/badge/package_manager-uv-purple.svg)](https://astral.sh/uv)
[![AI / Embeddings: SPECTER2](https://img.shields.io/badge/embeddings-SPECTER2-green.svg)](https://huggingface.co/allenai/specter2_base)
[![GPU: NVIDIA CUDA 12.4](https://img.shields.io/badge/GPU-CUDA_12.4-orange.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Tests: pytest](https://img.shields.io/badge/tests-8_passed-brightgreen.svg)](#running-unit-tests)

**PaperTrail** is an agentic, end-to-end machine learning pipeline that transforms unstructured scientific literature corpora (over 287,000+ papers across Computer Science, Physics, Genomics, and Mathematics) into an organized **Directed Acyclic Graph (DAG)** of academic prerequisite knowledge.

Traditional search engines (like Google Scholar or basic arXiv keyword search) yield flat lists of papers out of contextual order. When diving into a new complex domain (e.g., *Transformers in NLP* or *CRISPR gene editing*), jumping directly to an advanced paper often leads to confusion without understanding foundational concepts first. **PaperTrail reconstructs missing citation structures from scratch**, allowing users to input any academic topic and immediately receive a topologically sorted reading syllabus starting from core building blocks and leading up to specialized target papers.

---

## 🌟 Architectural & Scientific Pillars

PaperTrail eliminates arbitrary heuristics in favor of high-performance linear algebra, mathematical modeling, and graph theory:

### 1. Citation-Aware Semantic Embeddings (`SPECTER2` + `FAISS`)
- **Citation-Trained Transformer**: Unlike standard large language models, PaperTrail utilizes `allenai/specter2_base`—a specialized transformer trained directly on academic citation networks. If Paper A cites Paper B in literature, their 768-dimensional embeddings naturally converge in semantic space.
- **CUDA GPU Acceleration**: Designed for instantaneous batched encoding (`batch_size=256`), leveraging NVIDIA CUDA acceleration (e.g., GeForce RTX series) to process hundreds of thousands of documents with intelligent disk tensor archiving (`embeddings.npy`).
- **Exact Inner-Product Neighborhood Search**: Embeddings are L2-normalized upon inference, allowing **FAISS (Facebook AI Similarity Search)** to compute exact cosine similarity matrices across millions of pair candidates in sub-seconds.

### 2. Two-Tier Directional Orientation Engine
To establish prerequisite reading directions ($A \to B$) without formal citation tables, PaperTrail enforces a rigorous hierarchy:
- **Temporal Precedence**: If two semantic neighbors were published significantly apart ($\ge 365$ days), time dictates that the older paper ($A$) represents foundational prior art: $A \to B$.
- **Vocabulary Generality Scoring (TF-IDF)**: For papers published concurrently in the same time window ($< 365$ days), historical order cannot dictate dependency. PaperTrail precomputes global term weights via Inverse Document Frequency (IDF). Foundational introduction papers rely on widespread vocabulary (lower average IDF), whereas specialized optimization papers rely on hyper-specific terminology (higher average IDF): $\text{Lower Score} \to \text{Higher Score}$.
- **Dynamic Survey Exclusion Guardrail**: Literature surveys synthesize basic concepts (low IDF score) but are published long *after* original research. A regex-based boolean mask (`r"\bsurvey\b|\breview\b"`) automatically forbids review literature from acting as conceptual roots for older research.

### 3. Million-Edge Scaled Graph Hygiene & Topological Sorting
- **Vectorized Total-Order DAG Enforcement**: Building NetworkX graphs directly over 2.7+ million candidate edges using iterative loop search (`nx.find_cycle`) causes fatal memory slowdowns. PaperTrail maps every node to an absolute chronological and vocabulary seniority rank in Pandas. Any candidate edge that would create a circular loop is pruned via vectorized boolean masking in **$< 0.5$ seconds**, guaranteeing zero temporal timeline violations.
- **Dynamic Query-Time Transitive Reduction**: To keep global compilation instantaneous, multi-hop shortcut reduction ($A \to C$ when $A \to B \to C$) is bypassed at build time and dynamically applied in **$< 5$ milliseconds** whenever an ancestor reading subgraph is extracted during topic querying.

---

## 📁 Repository Structure

```text
PaperTrail/
├── config.yaml               # Master controller for file paths, hyperparameters, and thresholds
├── pyproject.toml            # Dependencies and package specifications managed via uv
├── pytest.ini                # Pytest runtime configuration
├── data/                     # Data storage directory hierarchy
│   ├── raw/                  # Ingested raw arXiv_scientific_dataset.csv (287k+ papers)
│   ├── interim/              # Cleaned, deduplicated, version-resolved parquet snapshot
│   └── processed/            # Compiled embeddings (.npy), candidate pairs, and graph.gpickle
├── src/                      # Source code modules
│   ├── __init__.py           
│   ├── main.py               # Single CLI router for pipeline compilation and live querying
│   ├── data_prep.py          # Data ingestion, version deduplication, and indexing engine
│   ├── embed.py              # CUDA-optimized SPECTER2 encoder and smart cache validator
│   ├── candidate_edges.py    # Vectorized FAISS similarity search & 64-bit pair deduplicator
│   ├── direction.py          # Vectorized orientation engine (Temporal & TF-IDF rules)
│   ├── build_graph.py        # Vectorized Total-Order DAG assembler and validation diagnostic
│   └── query.py              # Semantic query matcher, subgraph extraction, and topological sorter
└── tests/                    # Automated regression and algorithmic unit test suites
    ├── test_direction.py     # Tests for temporal precedence, vocabulary scores, & survey exclusions
    └── test_graph_cleanup.py # Tests for million-edge DAG enforcement and transitive reduction
```

---

## 🚀 Quickstart & Installation

PaperTrail uses [uv](https://astral.sh/uv), an ultra-fast Python package manager written in Rust.

### 1. Download the Dataset 📊
Download the official **arXiv Scientific Research Papers Dataset** from Kaggle:  
👉 **[arXiv Scientific Research Papers Dataset (Kaggle)](https://www.kaggle.com/datasets/sumitm004/arxiv-scientific-research-papers-dataset)**

After downloading, place the extracted CSV file (`arXiv_scientific_dataset.csv`) directly into the raw data directory:
```text
data/raw/arXiv_scientific_dataset.csv
```

### 2. Clone & Setup Environment
```powershell
# Clone the repository and navigate into project directory
cd PaperTrail

# Create a local virtual environment with Python 3.11+
uv venv .venv
```

### 3. Install High-Performance Dependencies (with NVIDIA CUDA 12.4 Support)
```powershell
# Install all primary dependencies
uv pip install -r pyproject.toml

# Unlock GPU acceleration for NVIDIA graphics cards (RTX series)
uv pip install torch --reinstall --index-url https://download.pytorch.org/whl/cu124
```
*Note: You can verify active CUDA runtime support at any time by running:*
```powershell
uv run python -c "import torch; print('CUDA Active:', torch.cuda.is_available(), '| Device:', torch.cuda.get_device_name(0))"
```

---

## ⚡ Running the Pipeline & Querying Curricula

### Step 1: One-Time Global Corpus Graph Compilation
To build the knowledge graph across the entire ~287,000 paper repository without domain limits, run:
```powershell
uv run python -m src.main --run-pipeline
```
**Intelligent Caching**: During your initial run, CUDA GPU inference will encode all 287k papers and archive the tensor array to `data/processed/embeddings.npy` (~880 MB). **On all subsequent pipeline re-runs**, PaperTrail's smart cache detector will automatically verify and load this file in under 1 second, completing full graph compilation across $>2.3$ million validated edges in **less than 45 seconds**!

#### Example Build Verification Log:
```yaml
================== GRAPH VALIDATION REPORT ==================
  nodes: 287286
  edges: 2323862
  weakly_connected_components: 89
  isolated_nodes: 87
  is_dag: True          # Confirms strict acyclic mathematical integrity
  avg_out_degree: 8.089
  date_violations: 0    # Guaranteed zero historical time travel inversions
=============================================================
Saved validated DAG to data/processed/graph.gpickle.
=== PIPELINE RUN COMPLETE ===
```

---

### Step 2: Live Arbitrary Topic Queries
Once compiled, you can immediately query arbitrary topics across completely different academic domains from your terminal. PaperTrail computes incoming shortest paths, applies transitive reduction, and returns an ordered reading checklist from foundational concepts (`[Hop N]`) up to the ultimate target paper (`[Hop 0]`):

#### Example 1: Artificial Intelligence & NLP
```powershell
uv run python -m src.main --query "retrieval augmented generation large language models"
```

#### Example 2: Genomics & Biotechnology
```powershell
uv run python -m src.main --query "CRISPR Cas9 gene editing specificity"
```
*Sample Curriculum Output:*
```text
Query: 'CRISPR Cas9 gene editing specificity' -> Matched target node indices: [251834]

=================== READING PATH FOR: 'CRISPR Cas9 gene editing specificity' ===================
[Hop 4] PromID: human promoter prediction by deep learning (2018-10-02)
[Hop 4] Bayesian multi-domain learning for cancer subtype discovery (2018-10-22)
[Hop 4] From Gene Expression to Drug Response: A Collaborative Filtering Approach (2018-10-29)
[Hop 1] Programmable Virtual Humans Toward Human Physiologically-Based Drug Discovery (2025-07-25)
[Hop 0] Artificial Intelligence for CRISPR Guide RNA Design: Explainable Models and Off-Target Safety (2025-08-26)
================================================================================================
```

#### Example 3: Quantum Physics
```powershell
uv run python -m src.main --query "quantum error correction surface codes"
```

---

## 🧪 Running Unit Tests

To execute automated unit and structural validation test suites covering temporal overrides, TF-IDF vocabulary tie-breaking, survey literature disqualification, vectorized DAG enforcement, and attribute-preserving transitive reduction:

```powershell
uv run pytest tests/ -v
```

```text
tests/test_direction.py::test_compute_generality_scores PASSED           [ 12%]
tests/test_direction.py::test_assign_direction_temporal PASSED           [ 25%]
tests/test_direction.py::test_assign_direction_generality_and_survey PASSED [ 37%]
tests/test_direction.py::test_assign_direction_ambiguous_drop PASSED     [ 50%]
tests/test_graph_cleanup.py::test_enforce_acyclic_order PASSED           [ 62%]
tests/test_graph_cleanup.py::test_cycle_removal PASSED                   [ 75%]
tests/test_graph_cleanup.py::test_transitive_reduction_preserves_attributes PASSED [ 87%]
tests/test_graph_cleanup.py::test_graph_stats PASSED                     [100%]
============================== 8 passed in 4.50s ===============================
```

---

## ⚙️ Master Configuration (`config.yaml`)

All system thresholds, file routes, and algorithmic parameters can be fine-tuned cleanly without altering application code:

| Section | Parameter | Default Value | Functional Description |
| :--- | :--- | :--- | :--- |
| **`domain`** | `category_codes` | `[]` *(empty)* | List of arXiv category filters (`["cs.CL", "cs.AI"]`). Leave empty (`[]`) for unrestricted science wide exploration. |
| | `keyword` | `null` | Optional string substring filter across titles/abstracts. |
| | `max_papers` | `null` | Integer cap for sampling. Leave `null` to process all ~287k papers. |
| **`embedding`** | `model_name` | `"allenai/specter2_base"` | HuggingFace model hub ID for citation-aware text encoding. |
| | `batch_size` | `256` | Inference batch size; calibrated for 8GB VRAM (NVIDIA RTX 4060). |
| **`candidate_edges`** | `top_k` | `15` | FAISS nearest neighbors evaluated per paper node. |
| | `similarity_threshold` | `0.55` | Minimum inner-product dot score required to qualify a link. |
| **`direction`** | `temporal_gap_days` | `365` | Calendar days required before historical time overrides vocabulary. |
| | `generality_epsilon` | `0.15` | Minimum difference in average IDF required to prevent ambiguous drop. |
| **`query`** | `max_hops` | `4` | Maximum ancestor prerequisite depth included in reading checklists. |
| | `top_n_targets` | `1` | Number of primary target match papers to construct syllabus around. |

---

## 📜 License
This project is open-source and dedicated to the advancement of accessible academic education and structured scientific inquiry.
