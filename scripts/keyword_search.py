import os
import re
from pathlib import Path

from dotenv import load_dotenv
from hdbcli import dbapi


# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_path = PROJECT_ROOT / ".env"

load_dotenv(env_path)


# ------------------------------------------------------------
# User query
# ------------------------------------------------------------

query = input("\nEnter a support-ticket search query: ").strip()

if not query:
    raise ValueError("Search query cannot be empty.")


# ------------------------------------------------------------
# Simple keyword preprocessing
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

words = re.findall(r"[A-Za-z0-9]+", query.lower())

keywords = [
    word
    for word in words
    if word not in STOPWORDS
]

if not keywords:
    raise ValueError(
        "No meaningful search keywords were found."
    )

print("\nKeywords used:", keywords)


# ------------------------------------------------------------
# Build keyword scoring SQL
# ------------------------------------------------------------

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
        [
            pattern,
            pattern
        ]
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
        [
            pattern,
            pattern
        ]
    )


score_sql = " + ".join(score_parts)
where_sql = " OR ".join(where_parts)

# IMPORTANT:
# Parameters must follow the exact order
# of placeholders in the SQL statement.
parameters = score_parameters + where_parameters


sql = f"""
    SELECT TOP 5
        TICKET_ID,
        TITLE,
        DESCRIPTION,
        PRODUCT_AREA,
        CATEGORY,
        ISSUE_FAMILY,
        ({score_sql}) AS KEYWORD_SCORE
    FROM SUPPORT_TICKETS
    WHERE {where_sql}
    ORDER BY
        KEYWORD_SCORE DESC,
        TICKET_ID ASC
"""


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

    cursor.execute(
        sql,
        tuple(parameters)
    )

    results = cursor.fetchall()


    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print("\nTop 5 keyword matches")
    print("=" * 80)

    if not results:

        print("No keyword matches found.")

    else:

        for rank, row in enumerate(
            results,
            start=1
        ):

            (
                ticket_id,
                title,
                description,
                product_area,
                category,
                issue_family,
                keyword_score
            ) = row

            print(f"\nRank: {rank}")
            print(f"Ticket ID: {ticket_id}")
            print(f"Title: {title}")
            print(f"Description: {description}")
            print(f"Product Area: {product_area}")
            print(f"Category: {category}")
            print(f"Issue Family: {issue_family}")
            print(f"Keyword Score: {keyword_score}")

    cursor.close()

except Exception as e:

    print("\nKeyword search failed:")
    print(e)

finally:

    if connection:
        connection.close()