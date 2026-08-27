# SAP HANA Cloud Semantic Search Project

## From Keyword Search to Semantic Search

This project evaluates vector-based semantic retrieval for enterprise support tickets in SAP HANA Cloud and compares it with a traditional SQL keyword-search baseline.

The project was developed for the **Database Theory and Management** module of the MS in SAP Engineering and Analytics programme.

## Research Question

To what extent does vector-based semantic search improve the relevance of enterprise support-ticket retrieval compared with traditional keyword-based SQL search?

## Project Overview

The prototype uses a synthetic dataset of 500 support tickets covering ten controlled issue families.

Each ticket contains conventional relational attributes as well as a 384-dimensional semantic embedding stored in an SAP HANA Cloud `REAL_VECTOR` column.

Two retrieval approaches are compared:

1. **Keyword search**
   - SQL-based text matching
   - Simple keyword scoring
   - Transparent lexical baseline

2. **Semantic search**
   - Query embeddings generated with the pretrained `all-MiniLM-L6-v2` Sentence Transformers model
   - Vector embeddings stored in SAP HANA Cloud
   - Ranking performed with `COSINE_SIMILARITY`

## Architecture

Python is used locally for:

- synthetic dataset generation
- preprocessing
- embedding generation
- loading data into SAP HANA Cloud
- generating query embeddings
- automated evaluation
- result analysis and visualisation

SAP HANA Cloud is used for:

- relational ticket storage
- `REAL_VECTOR(384)` storage
- SQL keyword retrieval
- vector similarity retrieval
- ranking search results

This separation keeps SAP HANA Cloud as the database and retrieval engine while using Python for tasks that are more practical outside the SQL layer.

## Dataset

The final dataset contains:

- 500 synthetic support tickets
- 500 unique title-description combinations
- 10 controlled issue families
- 50 tickets per issue family
- no missing values
- no duplicate ticket IDs

The issue-family label is used as controlled ground truth for retrieval evaluation.

## Evaluation

The formal experiment contains 40 predefined queries across five categories:

- Exact Keyword
- Synonym
- Paraphrase
- Natural Language
- Exact Identifier

Both retrieval methods are evaluated using the same database records and the same queries.

Metrics include:

- Precision@5
- Success@5
- First Relevant Rank
- Mean Reciprocal Rank (MRR)
- Database query time
- Query embedding time

## Main Results

Overall results:

| Method | Mean Precision@5 | Success@5 | MRR |
|---|---:|---:|---:|
| Keyword | 0.91 | 0.95 | 0.93 |
| Semantic | 0.99 | 1.00 | 1.00 |

The largest difference occurred for paraphrased queries:

| Method | Paraphrase Precision@5 | Success@5 | MRR |
|---|---:|---:|---:|
| Keyword | 0.689 | 0.778 | 0.689 |
| Semantic | 0.956 | 1.000 | 1.000 |

The experiment therefore indicates that semantic retrieval provides its clearest advantage when the search query expresses the correct concept using vocabulary that differs substantially from the stored ticket text.

Keyword retrieval remained highly effective for exact keywords and technical identifiers.

## Example

Query:

> Staff member lacks permission to use the buying system

The keyword baseline returned five `INTERFACE_FAILURE` tickets.

The semantic search returned five `PROCUREMENT_AUTH` tickets.

This demonstrates how semantic retrieval can identify related meaning even when exact terminology differs.

## Project Structure

```text
data/
    data_dictionary_v2.csv
    evaluation_queries.csv
    support_tickets_v2.csv

scripts/
    create_evaluation_charts.py
    demo_search_comparison.py
    generate_and_store_embeddings.py
    generate_tickets_v2.py
    inspect_evaluation_failures.py
    inspect_failure_rankings.py
    keyword_search.py
    load_tickets_v2_to_hana.py
    run_evaluation.py
    semantic_search.py

sql/
    00_vector_access_validation.sql
    01_create_support_tickets.sql
    02_keyword_search.sql
    03_semantic_search.sql

results/
    evaluation_rankings.csv
    evaluation_summary.csv
    metrics_by_query_type.csv
    overall_metrics.csv

figures/
    evaluation charts