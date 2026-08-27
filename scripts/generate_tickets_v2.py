from pathlib import Path
from datetime import date, timedelta
from itertools import product
import random

import pandas as pd


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

OUTPUT_FILE = DATA_DIR / "support_tickets_v2.csv"
DICTIONARY_FILE = DATA_DIR / "data_dictionary_v2.csv"

TICKETS_PER_FAMILY = 50


# ------------------------------------------------------------
# Issue families
# ------------------------------------------------------------

ISSUES = [
    {
        "category": "Authorization and Access",
        "product_area": "Procurement",
        "family": "PROCUREMENT_AUTH",
        "titles": [
            "User cannot access purchasing application",
            "Procurement application access denied",
            "Missing authorization for purchasing",
            "Employee unable to open procurement app",
        ],
        "descriptions": [
            "The employee cannot open the purchasing application and receives an authorization error.",
            "A user is unable to access procurement functions although the application is available.",
            "The purchasing application denies access because the required business role appears to be missing.",
            "The employee is not permitted to enter the procurement application.",
        ],
        "resolutions": [
            "Assigned the required procurement authorization role.",
            "Updated the user's business-role assignment.",
            "Corrected the missing authorization and verified access.",
        ],
    },

    {
        "category": "Authorization and Access",
        "product_area": "Identity and Access",
        "family": "HTTP_401",
        "titles": [
            "HTTP 401 when opening application",
            "Application returns unauthorized error",
            "401 authorization error after login",
            "User receives HTTP 401",
        ],
        "descriptions": [
            "The application returns HTTP 401 even though the user successfully authenticated.",
            "A user receives an unauthorized response when opening the application.",
            "Login succeeds but access to the requested service fails with status code 401.",
            "The service rejects the request because the user's authorization is insufficient.",
        ],
        "resolutions": [
            "Corrected the role assignment.",
            "Updated the application authorization configuration.",
            "Assigned the required access role and verified the application.",
        ],
    },

    {
        "category": "Finance",
        "product_area": "Financial Accounting",
        "family": "INVOICE_POSTING",
        "titles": [
            "Invoice cannot be posted",
            "Finance posting fails for supplier invoice",
            "Supplier invoice posting error",
            "Accounting document not created",
        ],
        "descriptions": [
            "The supplier invoice cannot be posted because the accounting configuration is incomplete.",
            "Finance users receive an error while posting an incoming invoice.",
            "The invoice process stops before an accounting document is generated.",
            "Posting fails when the user attempts to save the supplier invoice.",
        ],
        "resolutions": [
            "Corrected the accounting configuration.",
            "Updated the relevant finance settings.",
            "Resolved the posting configuration issue.",
        ],
    },

    {
        "category": "Integration and Interface",
        "product_area": "Integration",
        "family": "INTERFACE_FAILURE",
        "titles": [
            "Interface messages are failing",
            "Integration flow cannot deliver messages",
            "Outbound interface failure",
            "Messages stuck in integration flow",
        ],
        "descriptions": [
            "Messages between the source and target systems are failing during integration processing.",
            "The integration flow receives data but cannot deliver it to the target system.",
            "Outbound interface messages remain in an error state.",
            "The connected systems are not exchanging messages successfully.",
        ],
        "resolutions": [
            "Corrected the target endpoint configuration.",
            "Updated the integration credentials.",
            "Fixed the interface configuration and reprocessed messages.",
        ],
    },

    {
        "category": "Performance",
        "product_area": "Analytics",
        "family": "SLOW_REPORT",
        "titles": [
            "Report execution is extremely slow",
            "Analytics report performance degraded",
            "Closing report takes too long",
            "Long response time when running report",
        ],
        "descriptions": [
            "The financial closing report now takes significantly longer to execute than usual.",
            "Users report that the analytics report has become extremely slow.",
            "The report completes successfully but response time has degraded substantially.",
            "A previously fast reporting query now requires several minutes to return results.",
        ],
        "resolutions": [
            "Optimized the database query.",
            "Adjusted the query filters and database operation.",
            "Improved the underlying query performance.",
        ],
    },

    {
        "category": "Reporting and Analytics",
        "product_area": "Business Intelligence",
        "family": "MISSING_REPORT_DATA",
        "titles": [
            "Dashboard is missing recent data",
            "Report does not show current records",
            "Analytics dashboard incomplete",
            "Latest transactions absent from report",
        ],
        "descriptions": [
            "The dashboard loads successfully but recent business transactions are not displayed.",
            "Users can open the report, but the latest records are missing.",
            "The analytics application shows incomplete data after the latest load.",
            "Recent transactions are absent even though older report data is available.",
        ],
        "resolutions": [
            "Corrected the failed data refresh.",
            "Restarted the data-loading process.",
            "Fixed the extraction issue and refreshed the dataset.",
        ],
    },

    {
        "category": "Master Data",
        "product_area": "Master Data Management",
        "family": "MASTER_DATA_DUPLICATE",
        "titles": [
            "Duplicate customer master records",
            "Customer exists multiple times",
            "Duplicate master data detected",
            "Multiple records created for same customer",
        ],
        "descriptions": [
            "Multiple customer master records exist for the same business partner.",
            "The system contains duplicate records representing one customer.",
            "Users discovered that the same customer was created more than once.",
            "Duplicate master data is causing inconsistent downstream processing.",
        ],
        "resolutions": [
            "Merged the duplicate customer records.",
            "Removed the duplicate entry and retained the valid record.",
            "Cleaned the duplicate master data.",
        ],
    },

    {
        "category": "Procurement",
        "product_area": "Procurement",
        "family": "PO_APPROVAL",
        "titles": [
            "Manager cannot approve purchase order",
            "Purchase order approval blocked",
            "PO workflow does not allow approval",
            "Purchase order remains awaiting approval",
        ],
        "descriptions": [
            "The manager cannot approve the purchase order even though it is waiting for approval.",
            "A purchase order remains pending because the approver cannot complete the workflow.",
            "The approval step fails when the manager attempts to release the purchase order.",
            "The purchasing workflow does not permit the responsible manager to approve the order.",
        ],
        "resolutions": [
            "Corrected the workflow-agent assignment.",
            "Updated the purchase-order approval configuration.",
            "Assigned the correct approver and restarted the workflow.",
        ],
    },

    {
        "category": "Database and Connection",
        "product_area": "SAP HANA",
        "family": "DB_CONNECTION",
        "titles": [
            "Application cannot connect to database",
            "Database connection unavailable",
            "HANA connection fails",
            "Application loses database connectivity",
        ],
        "descriptions": [
            "The application cannot establish a connection to the SAP HANA database.",
            "Database connectivity fails even though the application itself is running.",
            "The application reports that the database server cannot be reached.",
            "Connections to SAP HANA repeatedly fail during application startup.",
        ],
        "resolutions": [
            "Corrected the database connection configuration.",
            "Updated the connection credentials.",
            "Fixed the network and database configuration.",
        ],
    },

    {
        "category": "Database and Connection",
        "product_area": "SAP HANA",
        "family": "SQL_ERROR_257",
        "titles": [
            "SQL error 257 during query execution",
            "Database returns SQL 257",
            "Query fails with error code 257",
            "SQL statement rejected with error 257",
        ],
        "descriptions": [
            "The SQL statement fails with error code 257 when executed against SAP HANA.",
            "Database processing stops because the query returns SQL error 257.",
            "A user receives error 257 while attempting to execute the SQL statement.",
            "The database rejects the SQL command and returns technical identifier 257.",
        ],
        "resolutions": [
            "Corrected the SQL syntax.",
            "Fixed the invalid SQL statement.",
            "Adjusted the query syntax and reran the statement.",
        ],
    },
]


# ------------------------------------------------------------
# Context variations
# ------------------------------------------------------------

CONTEXTS = [
    "The issue was first reported by a business user during normal daily processing.",
    "The problem started after a recent configuration change.",
    "Several users reported the same behaviour during morning operations.",
    "The issue occurs consistently when the affected function is executed.",
    "The problem was reproduced in the development environment.",
    "The behaviour occurs intermittently but affects normal business processing.",
    "The issue became visible after the user's latest login.",
    "The problem affects an important business process and requires investigation.",
]


PRIORITIES = ["Low", "Medium", "High", "Critical"]


# ------------------------------------------------------------
# Generate 50 unique tickets per issue family
# ------------------------------------------------------------

tickets = []

start_date = date(2025, 1, 1)
end_date = date(2026, 8, 1)
date_range_days = (end_date - start_date).days

ticket_id = 1

for issue in ISSUES:

    candidates = []

    for title, description, context in product(
        issue["titles"],
        issue["descriptions"],
        CONTEXTS
    ):
        full_description = f"{description} {context}"

        candidates.append(
            (title, full_description)
        )

    random.shuffle(candidates)

    selected = candidates[:TICKETS_PER_FAMILY]

    for title, description in selected:

        priority = random.choices(
            PRIORITIES,
            weights=[20, 45, 25, 10],
            k=1
        )[0]

        created_at = start_date + timedelta(
            days=random.randint(0, date_range_days)
        )

        resolution = random.choice(issue["resolutions"])

        tickets.append(
            {
                "TICKET_ID": ticket_id,
                "TITLE": title,
                "DESCRIPTION": description,
                "PRODUCT_AREA": issue["product_area"],
                "CATEGORY": issue["category"],
                "PRIORITY": priority,
                "CREATED_AT": created_at.isoformat(),
                "RESOLUTION_TEXT": resolution,
                "ISSUE_FAMILY": issue["family"],
            }
        )

        ticket_id += 1


# ------------------------------------------------------------
# Create dataframe
# ------------------------------------------------------------

df = pd.DataFrame(tickets)

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Data-quality checks
# ------------------------------------------------------------

total_tickets = len(df)

unique_search_texts = (
    df["TITLE"] + "|" + df["DESCRIPTION"]
).nunique()

duplicate_ticket_ids = df["TICKET_ID"].duplicated().sum()

missing_values = df.isnull().sum().sum()


print("DATA QUALITY CHECK")
print("=" * 60)

print("Total tickets:", total_tickets)
print("Unique TITLE + DESCRIPTION combinations:", unique_search_texts)
print("Duplicate ticket IDs:", duplicate_ticket_ids)
print("Total missing values:", missing_values)

print("\nTickets per issue family:")
print(df["ISSUE_FAMILY"].value_counts().sort_index())


# ------------------------------------------------------------
# Stop automatically if quality conditions fail
# ------------------------------------------------------------

if total_tickets != 500:
    raise RuntimeError(
        f"Expected 500 tickets but found {total_tickets}."
    )

if unique_search_texts != 500:
    raise RuntimeError(
        f"Expected 500 unique search texts but found "
        f"{unique_search_texts}."
    )

if duplicate_ticket_ids != 0:
    raise RuntimeError(
        "Duplicate ticket IDs detected."
    )

if missing_values != 0:
    raise RuntimeError(
        "Missing values detected."
    )


# ------------------------------------------------------------
# Save final candidate dataset
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ------------------------------------------------------------
# Data dictionary
# ------------------------------------------------------------

data_dictionary = pd.DataFrame(
    [
        [
            "TICKET_ID",
            "Integer",
            "Unique identifier for each synthetic support ticket."
        ],
        [
            "TITLE",
            "Text",
            "Short summary of the reported issue."
        ],
        [
            "DESCRIPTION",
            "Text",
            "Main searchable problem description."
        ],
        [
            "PRODUCT_AREA",
            "Text",
            "SAP or business product area related to the issue."
        ],
        [
            "CATEGORY",
            "Text",
            "High-level issue category."
        ],
        [
            "PRIORITY",
            "Text",
            "Low, Medium, High or Critical priority."
        ],
        [
            "CREATED_AT",
            "Date",
            "Synthetic ticket creation date."
        ],
        [
            "RESOLUTION_TEXT",
            "Text",
            "Synthetic resolution associated with the issue."
        ],
        [
            "ISSUE_FAMILY",
            "Text",
            "Controlled ground-truth label used for retrieval evaluation."
        ],
    ],
    columns=[
        "FIELD",
        "TYPE",
        "DESCRIPTION"
    ]
)

data_dictionary.to_csv(
    DICTIONARY_FILE,
    index=False,
    encoding="utf-8"
)


print("\nDataset passed all checks.")
print(f"Saved to: {OUTPUT_FILE}")