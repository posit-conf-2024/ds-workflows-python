import os
import ibis
import polars as pl

from ibis import _
from dotenv import load_dotenv

load_dotenv(override=True)
username = os.environ["USER"]

con = ibis.postgres.connect(
    database=os.environ["DATABASE_NAME_PYTHON"],
    host=os.environ["DATABASE_HOST"],
    user=os.environ["DATABASE_USER_PYTHON"],
    password=os.environ["DATABASE_PASSWORD_PYTHON"],
    schema=os.environ["DATABASE_SCHEMA"],
)

con.list_tables()

pl.Config.set_tbl_rows(100)

print(
    con
    .table(f"{username}_terminal_weather_clean")
    .select("weather_code")
    .value_counts()
    .order_by(ibis.desc("weather_code_count"))
    .to_polars()
)