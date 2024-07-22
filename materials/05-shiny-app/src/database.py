import os

import ibis
from ibis.backends.postgres import Backend

def get_con() -> Backend:
    con = ibis.postgres.connect(
        database=os.environ["DATABASE_NAME_PYTHON"],
        host=os.environ["DATABASE_HOST"],
        user=os.environ["DATABASE_USER_PYTHON"],
        password=os.environ["DATABASE_PASSWORD_PYTHON"],
        schema=os.environ["DATABASE_SCHEMA"],
    )
    return con


def get_table(con: Backend, table_name: str) -> ibis.expr.types.relations.Table:
    table = con.table(table_name)
    return table