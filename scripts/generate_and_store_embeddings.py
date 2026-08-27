import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from hdbcli import dbapi
from sentence_transformers import SentenceTransformer


# ------------------------------------------------------------
# Paths and environment
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

env_path = PROJECT_ROOT / ".env"
data_path = PROJECT_ROOT / "data" / "support_tickets_v2.csv"

load_dotenv(env_path)


# ------------------------------------------------------------
# Load ticket dataset
# ------------------------------------------------------------

df = pd.read_csv(data_path)

print(f"Loaded {len(df)} tickets.")


# ------------------------------------------------------------
# Create searchable text
# ------------------------------------------------------------

# We combine title + description because both contain useful
# information about the ticket.
search_texts = (
    df["TITLE"].fillna("")
    + " "
    + df["DESCRIPTION"].fillna("")
).tolist()


# ------------------------------------------------------------
# Load pretrained embedding model
# ------------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Generating embeddings...")

embeddings = model.encode(
    search_texts,
    normalize_embeddings=True,
    show_progress_bar=True
)

print("Embeddings generated.")
print("Number of embeddings:", len(embeddings))
print("Vector dimension:", embeddings.shape[1])


# ------------------------------------------------------------
# Connect to SAP HANA Cloud
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

    print("Connected to SAP HANA Cloud.")


    # --------------------------------------------------------
    # Store each vector in HANA
    # --------------------------------------------------------

    update_sql = """
        UPDATE SUPPORT_TICKETS
        SET EMBEDDING = TO_REAL_VECTOR(?)
        WHERE TICKET_ID = ?
    """

    records = []

    for ticket_id, embedding in zip(
        df["TICKET_ID"],
        embeddings
    ):

        # Convert numpy vector into the text format expected
        # by TO_REAL_VECTOR(), e.g. [0.1,0.2,0.3]
        vector_text = "[" + ",".join(
            str(float(value))
            for value in embedding
        ) + "]"

        records.append(
            (
                vector_text,
                int(ticket_id)
            )
        )

    cursor.executemany(
        update_sql,
        records
    )

    connection.commit()


    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM SUPPORT_TICKETS
        WHERE EMBEDDING IS NOT NULL
    """)

    vector_count = cursor.fetchone()[0]

    print(
        f"Tickets with embeddings stored in HANA: "
        f"{vector_count}"
    )

    cursor.close()

    print("Embedding storage completed successfully!")

except Exception as e:

    print("\nEmbedding process failed:")
    print(e)

finally:

    if connection:
        connection.close()