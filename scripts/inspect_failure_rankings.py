from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

rankings_path = (
    PROJECT_ROOT
    / "results"
    / "evaluation_rankings.csv"
)

df = pd.read_csv(rankings_path)


failure_queries = [
    "Q014",
    "Q017",
    "Q018",
    "Q020",
    "Q026",
]


filtered = df[
    df["QUERY_ID"].isin(failure_queries)
].copy()


for query_id in failure_queries:

    print("\n")
    print("=" * 90)
    print(f"QUERY: {query_id}")
    print("=" * 90)

    query_results = filtered[
        filtered["QUERY_ID"] == query_id
    ]

    for method in ["Keyword", "Semantic"]:

        print(f"\n{method.upper()} RESULTS")
        print("-" * 70)

        method_results = query_results[
            query_results["METHOD"] == method
        ]

        if method_results.empty:
            print("No results.")
            continue

        print(
            method_results[
                [
                    "RANK",
                    "TICKET_ID",
                    "RETURNED_ISSUE_FAMILY",
                    "EXPECTED_ISSUE_FAMILY",
                    "RELEVANT",
                    "SCORE",
                ]
            ].to_string(index=False)
        )