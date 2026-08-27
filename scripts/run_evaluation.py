import os
import re
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from hdbcli import dbapi
from sentence_transformers import SentenceTransformer


# ============================================================
# Paths and environment
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

env_path = PROJECT_ROOT / ".env"
queries_path = PROJECT_ROOT / "data" / "evaluation_queries.csv"

results_dir = PROJECT_ROOT / "results"
results_dir.mkdir(parents=True, exist_ok=True)

load_dotenv(env_path)


# ============================================================
# Load predefined evaluation queries
# ============================================================

queries_df = pd.read_csv(queries_path)

print(f"Loaded {len(queries_df)} evaluation queries.")


# ============================================================
# Load the SAME embedding model used for stored ticket vectors
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model ready.")


# ============================================================
# Keyword baseline configuration
# ============================================================

STOPWORDS = {
    "a", "an", "the",
    "is", "are", "was", "were",
    "to", "of", "in", "on", "for",
    "and", "or", "but",
    "can", "cannot",
    "be", "been",
    "with", "from",
    "this", "that",
    "it",
    "not",
    "use"
}


def extract_keywords(query):
    words = re.findall(
        r"[A-Za-z0-9]+",
        query.lower()
    )

    return [
        word
        for word in words
        if word not in STOPWORDS
    ]


# ============================================================
# Semantic search
# ============================================================

def semantic_search(cursor, query):

    # Measure embedding generation separately
    embedding_start = time.perf_counter()

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    embedding_time_ms = (
        time.perf_counter() - embedding_start
    ) * 1000

    vector_text = "[" + ",".join(
        str(float(value))
        for value in query_embedding
    ) + "]"

    sql = """
        SELECT TOP 5
            TICKET_ID,
            ISSUE_FAMILY,
            COSINE_SIMILARITY(
                EMBEDDING,
                TO_REAL_VECTOR(?)
            ) AS SCORE
        FROM SUPPORT_TICKETS
        WHERE EMBEDDING IS NOT NULL
        ORDER BY SCORE DESC
    """

    # Measure database-query time separately
    db_start = time.perf_counter()

    cursor.execute(
        sql,
        (vector_text,)
    )

    rows = cursor.fetchall()

    db_time_ms = (
        time.perf_counter() - db_start
    ) * 1000

    return rows, embedding_time_ms, db_time_ms


# ============================================================
# Keyword search
# ============================================================

def keyword_search(cursor, query):

    keywords = extract_keywords(query)

    if not keywords:
        return [], 0.0

    score_parts = []
    score_parameters = []

    where_parts = []
    where_parameters = []

    for keyword in keywords:

        pattern = f"%{keyword}%"

        score_parts.append(
            """
            CASE
                WHEN LOWER(TITLE) LIKE ? THEN 1
                ELSE 0
            END
            +
            CASE
                WHEN LOWER(DESCRIPTION) LIKE ? THEN 1
                ELSE 0
            END
            """
        )

        score_parameters.extend(
            [pattern, pattern]
        )

        where_parts.append(
            """
            (
                LOWER(TITLE) LIKE ?
                OR LOWER(DESCRIPTION) LIKE ?
            )
            """
        )

        where_parameters.extend(
            [pattern, pattern]
        )

    score_sql = " + ".join(score_parts)
    where_sql = " OR ".join(where_parts)

    parameters = (
        score_parameters
        + where_parameters
    )

    sql = f"""
        SELECT TOP 5
            TICKET_ID,
            ISSUE_FAMILY,
            ({score_sql}) AS SCORE
        FROM SUPPORT_TICKETS
        WHERE {where_sql}
        ORDER BY
            SCORE DESC,
            TICKET_ID ASC
    """

    db_start = time.perf_counter()

    cursor.execute(
        sql,
        tuple(parameters)
    )

    rows = cursor.fetchall()

    db_time_ms = (
        time.perf_counter() - db_start
    ) * 1000

    return rows, db_time_ms


# ============================================================
# Evaluation metric calculation
# ============================================================

def calculate_metrics(
    rows,
    expected_family
):

    relevant_flags = [
        row[1] == expected_family
        for row in rows
    ]

    relevant_count = sum(relevant_flags)

    # Top 5 is always the denominator so methods returning
    # fewer than five results are not artificially rewarded.
    precision_at_5 = relevant_count / 5

    success_at_5 = (
        1 if relevant_count > 0 else 0
    )

    first_relevant_rank = None

    for rank, is_relevant in enumerate(
        relevant_flags,
        start=1
    ):
        if is_relevant:
            first_relevant_rank = rank
            break

    reciprocal_rank = (
        1 / first_relevant_rank
        if first_relevant_rank
        else 0
    )

    return {
        "PRECISION_AT_5": precision_at_5,
        "SUCCESS_AT_5": success_at_5,
        "FIRST_RELEVANT_RANK": first_relevant_rank,
        "RECIPROCAL_RANK": reciprocal_rank,
    }


# ============================================================
# Connect to SAP HANA Cloud
# ============================================================

connection = None

summary_records = []
ranking_records = []

try:

    connection = dbapi.connect(
        address=os.getenv("HANA_HOST"),
        port=int(
            os.getenv(
                "HANA_PORT",
                "443"
            )
        ),
        user=os.getenv("HANA_USER"),
        password=os.getenv("HANA_PASSWORD")
    )

    cursor = connection.cursor()

    print("Connected to SAP HANA Cloud.")
    print("\nRunning evaluation...\n")


    # ========================================================
    # Run every predefined query
    # ========================================================

    for index, row in queries_df.iterrows():

        query_id = row["QUERY_ID"]
        query_type = row["QUERY_TYPE"]
        query = row["QUERY"]
        expected_family = row[
            "EXPECTED_ISSUE_FAMILY"
        ]

        print(
            f"{index + 1}/{len(queries_df)} "
            f"{query_id}: {query}"
        )


        # ----------------------------------------------------
        # Semantic search
        # ----------------------------------------------------

        (
            semantic_rows,
            embedding_time_ms,
            semantic_db_time_ms
        ) = semantic_search(
            cursor,
            query
        )

        semantic_metrics = calculate_metrics(
            semantic_rows,
            expected_family
        )


        # Save each semantic ranking result
        for rank, result in enumerate(
            semantic_rows,
            start=1
        ):

            ranking_records.append(
                {
                    "QUERY_ID": query_id,
                    "QUERY_TYPE": query_type,
                    "METHOD": "Semantic",
                    "RANK": rank,
                    "TICKET_ID": result[0],
                    "RETURNED_ISSUE_FAMILY": result[1],
                    "EXPECTED_ISSUE_FAMILY": expected_family,
                    "RELEVANT": (
                        result[1]
                        == expected_family
                    ),
                    "SCORE": result[2],
                }
            )


        summary_records.append(
            {
                "QUERY_ID": query_id,
                "QUERY_TYPE": query_type,
                "QUERY": query,
                "EXPECTED_ISSUE_FAMILY": expected_family,
                "METHOD": "Semantic",
                **semantic_metrics,
                "DB_QUERY_TIME_MS": semantic_db_time_ms,
                "EMBEDDING_TIME_MS": embedding_time_ms,
            }
        )


        # ----------------------------------------------------
        # Keyword search
        # ----------------------------------------------------

        (
            keyword_rows,
            keyword_db_time_ms
        ) = keyword_search(
            cursor,
            query
        )

        keyword_metrics = calculate_metrics(
            keyword_rows,
            expected_family
        )


        # Save each keyword ranking result
        for rank, result in enumerate(
            keyword_rows,
            start=1
        ):

            ranking_records.append(
                {
                    "QUERY_ID": query_id,
                    "QUERY_TYPE": query_type,
                    "METHOD": "Keyword",
                    "RANK": rank,
                    "TICKET_ID": result[0],
                    "RETURNED_ISSUE_FAMILY": result[1],
                    "EXPECTED_ISSUE_FAMILY": expected_family,
                    "RELEVANT": (
                        result[1]
                        == expected_family
                    ),
                    "SCORE": result[2],
                }
            )


        summary_records.append(
            {
                "QUERY_ID": query_id,
                "QUERY_TYPE": query_type,
                "QUERY": query,
                "EXPECTED_ISSUE_FAMILY": expected_family,
                "METHOD": "Keyword",
                **keyword_metrics,
                "DB_QUERY_TIME_MS": keyword_db_time_ms,
                "EMBEDDING_TIME_MS": 0.0,
            }
        )


    cursor.close()


except Exception as e:

    print("\nEvaluation failed:")
    print(e)

    raise


finally:

    if connection:
        connection.close()


# ============================================================
# Save detailed results
# ============================================================

summary_df = pd.DataFrame(
    summary_records
)

ranking_df = pd.DataFrame(
    ranking_records
)


summary_output = (
    results_dir
    / "evaluation_summary.csv"
)

ranking_output = (
    results_dir
    / "evaluation_rankings.csv"
)


summary_df.to_csv(
    summary_output,
    index=False
)

ranking_df.to_csv(
    ranking_output,
    index=False
)


# ============================================================
# Overall method comparison
# ============================================================

overall = (
    summary_df
    .groupby("METHOD")
    .agg(
        MEAN_PRECISION_AT_5=(
            "PRECISION_AT_5",
            "mean"
        ),
        SUCCESS_AT_5_RATE=(
            "SUCCESS_AT_5",
            "mean"
        ),
        MRR=(
            "RECIPROCAL_RANK",
            "mean"
        ),
        MEAN_DB_QUERY_TIME_MS=(
            "DB_QUERY_TIME_MS",
            "mean"
        ),
        MEAN_EMBEDDING_TIME_MS=(
            "EMBEDDING_TIME_MS",
            "mean"
        ),
    )
    .reset_index()
)


# ============================================================
# Performance by query type
# ============================================================

by_query_type = (
    summary_df
    .groupby(
        [
            "METHOD",
            "QUERY_TYPE"
        ]
    )
    .agg(
        MEAN_PRECISION_AT_5=(
            "PRECISION_AT_5",
            "mean"
        ),
        SUCCESS_AT_5_RATE=(
            "SUCCESS_AT_5",
            "mean"
        ),
        MRR=(
            "RECIPROCAL_RANK",
            "mean"
        ),
        MEAN_DB_QUERY_TIME_MS=(
            "DB_QUERY_TIME_MS",
            "mean"
        ),
    )
    .reset_index()
)


overall.to_csv(
    results_dir
    / "overall_metrics.csv",
    index=False
)

by_query_type.to_csv(
    results_dir
    / "metrics_by_query_type.csv",
    index=False
)


# ============================================================
# Display final results
# ============================================================

print("\n")
print("=" * 80)
print("EVALUATION COMPLETE")
print("=" * 80)

print("\nOverall results:")
print(
    overall.to_string(
        index=False
    )
)

print("\nResults by query type:")
print(
    by_query_type.to_string(
        index=False
    )
)

print("\nFiles created:")
print(summary_output)
print(ranking_output)
print(
    results_dir
    / "overall_metrics.csv"
)
print(
    results_dir
    / "metrics_by_query_type.csv"
)