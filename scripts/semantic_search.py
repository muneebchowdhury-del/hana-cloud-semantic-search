import os
from pathlib import Path

from dotenv import load_dotenv
from hdbcli import dbapi
from sentence_transformers import SentenceTransformer


# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_path = PROJECT_ROOT / ".env"

load_dotenv(env_path)


# ------------------------------------------------------------
# Load the SAME embedding model used for the tickets
# ------------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ------------------------------------------------------------
# User query
# ------------------------------------------------------------

query = input("\nEnter a support-ticket search query: ").strip()

if not query:
    raise ValueError("Search query cannot be empty.")


# ------------------------------------------------------------
# Convert query into a 384-dimensional embedding
# ------------------------------------------------------------

query_embedding = model.encode(
    query,
    normalize_embeddings=True
)

vector_text = "[" + ",".join(
    str(float(value))
    for value in query_embedding
) + "]"


# ------------------------------------------------------------
# Connect to HANA Cloud
# ------------------------------------------------------------

connection = None

try:
    connection = dbapi.connect(
        address=os.getenv("HANA_HOST"),
        port=int(os.getenv("HANA_PORT", "443")),
        user=os.getenv("HANA_USER"),
        password=os.getenv("HANA_PASSWORD")
    )

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Semantic vector search executed IN SAP HANA Cloud
    # --------------------------------------------------------

    sql = """
        SELECT TOP 5
            TICKET_ID,
            TITLE,
            DESCRIPTION,
            PRODUCT_AREA,
            CATEGORY,
            ISSUE_FAMILY,
            COSINE_SIMILARITY(
                EMBEDDING,
                TO_REAL_VECTOR(?)
            ) AS SIMILARITY_SCORE
        FROM SUPPORT_TICKETS
        WHERE EMBEDDING IS NOT NULL
        ORDER BY SIMILARITY_SCORE DESC
    """

    cursor.execute(sql, (vector_text,))

    results = cursor.fetchall()


    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print("\nTop 5 semantic matches")
    print("=" * 80)

    for rank, row in enumerate(results, start=1):

        (
            ticket_id,
            title,
            description,
            product_area,
            category,
            issue_family,
            similarity_score
        ) = row

        print(f"\nRank: {rank}")
        print(f"Ticket ID: {ticket_id}")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Product Area: {product_area}")
        print(f"Category: {category}")
        print(f"Issue Family: {issue_family}")
        print(f"Similarity Score: {similarity_score:.4f}")

    cursor.close()

except Exception as e:
    print("\nSemantic search failed:")
    print(e)

finally:
    if connection:
        connection.close()