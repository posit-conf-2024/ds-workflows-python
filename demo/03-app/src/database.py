import ibis
from ibis.backends.duckdb import Backend as DuckDBBackend

def get_con() -> DuckDBBackend:
    con = ibis.duckdb.connect("md:washington_ferries", read_only=True)
    return con
