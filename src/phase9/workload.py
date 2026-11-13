"""Deterministic fictional workforce rows shared by PostgreSQL and DuckDB.

This is an in-database DML microbenchmark, NOT a real ETL or CDC data source.
"""
from dataclasses import dataclass

COLUMNS = (
    "employee_id", "department_id", "location_id",
    "month_no", "salary_cents", "fte_milli",
)
SELECT_FILTER = (
    "SELECT COUNT(*) AS employee_count, "
    "COALESCE(SUM(salary_cents), 0) AS salary_cents, "
    "COALESCE(SUM(fte_milli), 0) AS fte_milli "
    "FROM {table} WHERE department_id = 8 AND month_no BETWEEN 9 AND 21"
)


@dataclass(frozen=True)
class Scale:
    baseline: int
    update_every: int = 20
    insert_percent: int = 1

    def __post_init__(self):
        if type(self.baseline) is not int or not 1_000 <= self.baseline <= 2_000_000:
            raise ValueError("Synthetic baseline rows must be 1000..2000000")
        if self.update_every != 20 or self.insert_percent != 1:
            raise ValueError("Only the fixed 5% update and 1% insertion workload is supported")

    @property
    def inserted(self):
        return self.baseline // 100

    @property
    def updated(self):
        return self.baseline // self.update_every

    @property
    def final_rows(self):
        return self.baseline + self.inserted

    @property
    def changed_rows(self):
        return self.updated + self.inserted


def projection(start: int, end: int, baseline: int, final: bool):
    """Same numeric integer expressions work in PostgreSQL and DuckDB."""
    if not 1 <= start <= end <= 2_020_000 or not 1_000 <= baseline <= 2_000_000:
        raise ValueError("Unsafe generator bounds")
    premium = f"(CASE WHEN n <= {baseline} AND n % 20 = 0 THEN 5000 ELSE 0 END)" if final else "0"
    return (
        "SELECT n::BIGINT AS employee_id, "
        "(n % 40 + 1)::INTEGER AS department_id, "
        "(n % 10 + 1)::INTEGER AS location_id, "
        "(n % 36 + 1)::INTEGER AS month_no, "
        f"(300000 + (n * 97) % 700000 + {premium})::BIGINT AS salary_cents, "
        "(500 + n % 501)::INTEGER AS fte_milli "
        f"FROM generate_series({start}, {end}) AS src(n)"
    )


def delta_projection(scale: Scale):
    """Change set: 5% updates plus 1% new records, no unchanged rows."""
    n = scale.baseline
    return (
        "SELECT * FROM ("
        "SELECT n::BIGINT AS employee_id, "
        "(n % 40 + 1)::INTEGER AS department_id, "
        "(n % 10 + 1)::INTEGER AS location_id, "
        "(n % 36 + 1)::INTEGER AS month_no, "
        "(300000 + (n * 97) % 700000 + 5000)::BIGINT AS salary_cents, "
        "(500 + n % 501)::INTEGER AS fte_milli "
        f"FROM generate_series(20, {n}, 20) AS updates(n) "
        "UNION ALL "
        f"{projection(n + 1, scale.final_rows, n, final=True)}"
        ") AS changes WHERE TRUE"
    )
