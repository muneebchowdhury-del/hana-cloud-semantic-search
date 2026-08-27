from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

results_path = (
    PROJECT_ROOT
    / "results"
    / "evaluation_summary.csv"
)

df = pd.read_csv(results_path)


print("=" * 80)
print("QUERIES WITH PRECISION@5 BELOW 1.0")
print("=" * 80)

failures = df[
    df["PRECISION_AT_5"] < 1.0
].copy()

columns = [
    "QUERY_ID",
    "QUERY_TYPE",
    "QUERY",
    "EXPECTED_ISSUE_FAMILY",
    "METHOD",
    "PRECISION_AT_5",
    "SUCCESS_AT_5",
    "FIRST_RELEVANT_RANK",
    "RECIPROCAL_RANK",
]

print(
    failures[columns]
    .sort_values(
        ["METHOD", "QUERY_ID"]
    )
    .to_string(index=False)
)


print("\n")
print("=" * 80)
print("QUERIES WITH NO RELEVANT TOP-5 RESULT")
print("=" * 80)

complete_failures = df[
    df["SUCCESS_AT_5"] == 0
]

if complete_failures.empty:
    print("None.")
else:
    print(
        complete_failures[columns]
        .sort_values(
            ["METHOD", "QUERY_ID"]
        )
        .to_string(index=False)
    )