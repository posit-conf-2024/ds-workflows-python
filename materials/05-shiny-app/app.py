import os


import polars as pl
from dotenv import load_dotenv
from loguru import logger
import ibis
from shiny import App, ui

from src.module_model_explorer import model_explorer_server, model_explorer_ui
from src.database import get_con

load_dotenv()
pl.Config(thousands_separator=True)


# ------------------------------------------------------------------------------
# Help functions
# ------------------------------------------------------------------------------
def read_data(table_name: str) -> pl.LazyFrame:
    logger.error(f"Reading all of {table_name} from the database...")
    con = get_con()
    table = con.table(table_name)
    # Note to self, table.to_polars was not working for some reason.
    df = pl.DataFrame(table.to_pandas())
    return df.lazy()


# ------------------------------------------------------------------------------
# Global state
# ------------------------------------------------------------------------------
con = get_con()
vessel_verbose = read_data("vessel_verbose_clean")
terminal_weather = read_data("terminal_weather_clean")
terminal_locations = read_data("terminal_locations_clean")
vessel_history = read_data("vessel_history_clean").with_columns(
    (pl.col("ActualDepart") - pl.col("ScheduledDepart")).alias("Delay"),
)

start_date = vessel_history.select(pl.col("Date").min()).collect().get_column("Date")[0]
end_date = vessel_history.select(pl.col("Date").max()).collect().get_column("Date")[0]

# ------------------------------------------------------------------------------
# UI logic
# ------------------------------------------------------------------------------
app_ui = ui.page_navbar(
    ui.nav_panel(
        "Model Explorer",
        model_explorer_ui(
            "model_explorer_module",
            vessel_verbose=vessel_verbose,
            vessel_history=vessel_history,
            terminal_weather=terminal_weather,
            con=con,
        ),
    ),
    title="Seattle Ferry Model & Data Explorer",
)


# ------------------------------------------------------------------------------
# Server logic
# ------------------------------------------------------------------------------
def server(input, output, session):
    model_explorer_server(
        "model_explorer_module",
        vessel_history=vessel_history,
        vessel_verbose=vessel_verbose,
        terminal_locations=terminal_locations,
        terminal_weather=terminal_weather,
        con=con,
    )


app = App(app_ui, server)
