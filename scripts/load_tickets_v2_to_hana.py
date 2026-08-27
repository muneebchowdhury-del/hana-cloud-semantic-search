import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from hdbcli import dbapi


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

env_path = PROJECT_ROOT / ".env"
data_path = PROJECT_ROOT / "data" / "support_tickets_v2.csv"

load_dotenv(env_path)


# ------------------------------------------------------------
# Load improved CSV
# ------------------------------------------------------------

df = pd.read_csv(data_path)

df["CREATED_AT"] = pd.to_datetime(
    df["CREATED_AT"]
).dt.date

print(f"Loaded {len(df)} tickets from improved dataset.")


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

    # Check table is empty before loading
    cursor.execute("""
        SELECT COUNT(*)
        FROM SUPPORT_TICKETS
    """)

    existing_rows = cursor.fetchone()[0]

    print(
        f"Existing rows in SUPPORT_TICKETS: "
        f"{existing_rows}"
    )

    if existing_rows != 0:
        raise RuntimeError(
            "SUPPORT_TICKETS is not empty. "
            "Stopping to prevent duplicate loading."
        )


    # --------------------------------------------------------
    # Insert improved records
    # --------------------------------------------------------

    insert_sql = """
        INSERT INTO SUPPORT_TICKETS (
            TICKET_ID,
            TITLE,
            DESCRIPTION,
            PRODUCT_AREA,
            CATEGORY,
            PRIORITY,
            CREATED_AT,
            RESOLUTION_TEXT,
            ISSUE_FAMILY,
            EMBEDDING
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
    """

    records = []

    for row in df.itertuples(index=False):

        records.append(
            (
                int(row.TICKET_ID),
                str(row.TITLE),
                str(row.DESCRIPTION),
                str(row.PRODUCT_AREA),
                str(row.CATEGORY),
                str(row.PRIORITY),
                row.CREATED_AT,
                str(row.RESOLUTION_TEXT),
                str(row.ISSUE_FAMILY)
            )
        )

    cursor.executemany(
        insert_sql,
        records
    )

    connection.commit()


    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM SUPPORT_TICKETS
    """)

    final_count = cursor.fetchone()[0]

    print(
        f"Rows now stored in HANA: "
        f"{final_count}"
    )

    cursor.close()

    print(
        "Improved dataset loaded successfully!"
    )

except Exception as e:

    print("\nLoading failed:")
    print(e)

finally:

    if connection:
        connection.close()