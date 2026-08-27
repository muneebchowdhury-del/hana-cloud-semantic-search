import os
import re
from pathlib import Path

from dotenv import load_dotenv
from hdbcli import dbapi
from sentence_transformers import SentenceTransformer


# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# ------------------------------------------------------------
# Load embedding model
# ------------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Model ready.")


# ------------------------------------------------------------
# Keyword preprocessing
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Keyword search
# ------------------------------------------------------------

def keyword_search(cursor, query):

    keywords = extract_keywords(query)

    if not keywords:
        return []

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
            TITLE,
            ISSUE_FAMILY,
            ({score_sql}) AS SCORE
        FROM SUPPORT_TICKETS
        WHERE {where_sql}
        ORDER BY
            SCORE DESC,
            TICKET_ID ASC
    """

    cursor.execute(
        sql,
        tuple(parameters)
    )

    return cursor.fetchall()


# ------------------------------------------------------------
# Semantic search
# ------------------------------------------------------------

def semantic_search(cursor, query):

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    vector_text = "[" + ",".join(
        str(float(value))
        for value in query_embedding
    ) + "]"

    sql = """
        SELECT TOP 5
            TICKET_ID,
            TITLE,
            ISSUE_FAMILY,
            COSINE_SIMILARITY(
                EMBEDDING,
                TO_REAL_VECTOR(?)
            ) AS SCORE
        FROM SUPPORT_TICKETS
        WHERE EMBEDDING IS NOT NULL
        ORDER BY SCORE DESC
    """

    cursor.execute(
        sql,
        (vector_text,)
    )

    return cursor.fetchall()


# ------------------------------------------------------------
# Display helper
# ------------------------------------------------------------

def print_results(title, rows):

    print("\n")
    print("=" * 80)
    print(title)
    print("=" * 80)

    if not rows:
        print("No results.")
        return

    for rank, row in enumerate(
        rows,
        start=1
    ):

        ticket_id = row[0]
        ticket_title = row[1]
        issue_family = row[2]
        score = row[3]

        print(
            f"{rank}. "
            f"Ticket {ticket_id} | "
            f"{issue_family} | "
            f"Score: {score:.4f}"
        )

        print(
            f"   {ticket_title}"
        )


# ------------------------------------------------------------
# Main demo
# ------------------------------------------------------------

query = input(
    "\nEnter support-ticket query: "
).strip()

if not query:
    raise ValueError(
        "Query cannot be empty."
    )


connection = None

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

    keyword_results = keyword_search(
        cursor,
        query
    )

    semantic_results = semantic_search(
        cursor,
        query
    )

    print_results(
        "KEYWORD SEARCH — TOP 5",
        keyword_results
    )

    print_results(
        "SEMANTIC SEARCH — TOP 5",
        semantic_results
    )

    cursor.close()

finally:

    if connection:
        connection.close()