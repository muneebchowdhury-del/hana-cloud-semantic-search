import os
from pathlib import Path

from dotenv import load_dotenv
from hdbcli import dbapi


# Load .env file
env_path = Path(__file__).with_name(".env")
load_dotenv(env_path)

# Safe checks — values themselves are NOT displayed
print("Host found:", bool(os.getenv("HANA_HOST")))
print("Port found:", bool(os.getenv("HANA_PORT")))
print("User found:", bool(os.getenv("HANA_USER")))
print("Password found:", bool(os.getenv("HANA_PASSWORD")))

connection = None

try:
    connection = dbapi.connect(
        address=os.getenv("HANA_HOST"),
        port=int(os.getenv("HANA_PORT", "443")),
        user=os.getenv("HANA_USER"),
        password=os.getenv("HANA_PASSWORD")
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT CURRENT_USER, CURRENT_DATE
        FROM DUMMY
    """)

    result = cursor.fetchone()

    print("\nConnection successful!")
    print("Current user:", result[0])
    print("Database date:", result[1])

    cursor.close()

except Exception as e:
    print("\nConnection failed:")
    print(e)

finally:
    if connection:
        connection.close()