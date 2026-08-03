"""Run SQL analysis queries and export result tables.

Reads all .sql files in sql/ and writes outputs to reports/sql_outputs/.
"""

from __future__ import annotations

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "sql_outputs"


def normalize_sql_for_duckdb(query: str) -> str:
    """Convert hash-style full-line comments to DuckDB-compatible comments."""
    normalized_lines = []
    for line in query.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            indent = line[: len(line) - len(stripped)]
            normalized_lines.append(f"{indent}--{stripped[1:]}")
        else:
            normalized_lines.append(line)
    return "\n".join(normalized_lines)


def main() -> None:
    sql_files = sorted(SQL_DIR.glob("*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"No SQL files found in {SQL_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(database=":memory:")
    try:
        for sql_file in sql_files:
            query = sql_file.read_text(encoding="utf-8")
            query = normalize_sql_for_duckdb(query)
            result_df = conn.execute(query).fetchdf()

            output_name = f"{sql_file.stem}.csv"
            output_path = OUTPUT_DIR / output_name
            result_df.to_csv(output_path, index=False)

            print(f"[OK] {sql_file.name} -> {output_path} ({len(result_df)} rows)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
