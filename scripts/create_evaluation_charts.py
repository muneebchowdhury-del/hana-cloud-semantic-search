from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Load results
# ------------------------------------------------------------

overall = pd.read_csv(
    RESULTS_DIR / "overall_metrics.csv"
)

by_type = pd.read_csv(
    RESULTS_DIR / "metrics_by_query_type.csv"
)


# ------------------------------------------------------------
# Desired query-type order
# ------------------------------------------------------------

query_order = [
    "Exact Keyword",
    "Synonym",
    "Paraphrase",
    "Natural Language",
    "Exact Identifier",
]


# ============================================================
# Chart 1 — Overall Precision@5
# ============================================================

chart1 = overall[
    ["METHOD", "MEAN_PRECISION_AT_5"]
].copy()

plt.figure(figsize=(7, 5))

plt.bar(
    chart1["METHOD"],
    chart1["MEAN_PRECISION_AT_5"]
)

plt.ylim(0, 1.05)

plt.ylabel("Mean Precision@5")
plt.xlabel("Retrieval Method")

plt.title(
    "Overall Retrieval Precision: "
    "Keyword vs Semantic Search"
)

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "01_overall_precision_at_5.png",
    dpi=300
)

plt.close()


# ============================================================
# Chart 2 — Precision@5 by query type
# ============================================================

precision = (
    by_type
    .pivot(
        index="QUERY_TYPE",
        columns="METHOD",
        values="MEAN_PRECISION_AT_5"
    )
    .reindex(query_order)
)

plt.figure(figsize=(10, 6))

precision.plot(
    kind="bar",
    ax=plt.gca()
)

plt.ylim(0, 1.05)

plt.ylabel("Mean Precision@5")
plt.xlabel("Query Type")

plt.title(
    "Precision@5 by Query Type"
)

plt.xticks(
    rotation=25,
    ha="right"
)

plt.legend(
    title="Method"
)

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "02_precision_by_query_type.png",
    dpi=300
)

plt.close()


# ============================================================
# Chart 3 — Success@5 by query type
# ============================================================

success = (
    by_type
    .pivot(
        index="QUERY_TYPE",
        columns="METHOD",
        values="SUCCESS_AT_5_RATE"
    )
    .reindex(query_order)
)

plt.figure(figsize=(10, 6))

success.plot(
    kind="bar",
    ax=plt.gca()
)

plt.ylim(0, 1.05)

plt.ylabel("Success@5 Rate")
plt.xlabel("Query Type")

plt.title(
    "Success@5 by Query Type"
)

plt.xticks(
    rotation=25,
    ha="right"
)

plt.legend(
    title="Method"
)

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "03_success_by_query_type.png",
    dpi=300
)

plt.close()


# ============================================================
# Chart 4 — Database query time
# ============================================================

timing = overall[
    ["METHOD", "MEAN_DB_QUERY_TIME_MS"]
].copy()

plt.figure(figsize=(7, 5))

plt.bar(
    timing["METHOD"],
    timing["MEAN_DB_QUERY_TIME_MS"]
)

plt.ylabel("Mean Database Query Time (ms)")
plt.xlabel("Retrieval Method")

plt.title(
    "Mean SAP HANA Cloud Query Time"
)

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "04_database_query_time.png",
    dpi=300
)

plt.close()


# ============================================================
# Chart 5 — Semantic processing components
# ============================================================

semantic = overall[
    overall["METHOD"] == "Semantic"
].iloc[0]

semantic_components = pd.Series(
    {
        "Query Embedding": semantic[
            "MEAN_EMBEDDING_TIME_MS"
        ],
        "HANA Vector Query": semantic[
            "MEAN_DB_QUERY_TIME_MS"
        ],
    }
)

plt.figure(figsize=(7, 5))

plt.bar(
    semantic_components.index,
    semantic_components.values
)

plt.ylabel("Mean Time (ms)")

plt.title(
    "Semantic Search Processing Components"
)

plt.tight_layout()

plt.savefig(
    FIGURES_DIR / "05_semantic_processing_time.png",
    dpi=300
)

plt.close()


print("Charts created successfully.")

print("\nFiles:")
for file in sorted(FIGURES_DIR.glob("*.png")):
    print(file.name)