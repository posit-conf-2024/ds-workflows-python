import os
from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from loguru import logger
from pins import board_connect
from shiny import App, ui

from src.module_model_explorer import model_explorer_server, model_explorer_ui

load_dotenv()
pl.Config(thousands_separator=True)


# ------------------------------------------------------------------------------
# Help functions
# ------------------------------------------------------------------------------
def read_data(pin_name: str) -> pl.LazyFrame:
    pin_full_name = f"{username}/{pin_name}"
    cache_path = Path(f".cache/{pin_name}.parquet")

    # If the data is cached, read from the cache. This speeds up development.
    if cache_path.exists():
        logger.info("Reading vessel_history_clean from cache")
        df = pl.read_parquet(cache_path)

    # If the data is not cached, read from Posit Connect.
    else:
        # Read from Posit Connect
        logger.info(f"Reading {pin_full_name} from Posit Connect")
        board = board_connect()
        board.pin_read(pin_full_name)
        paths = board.pin_download(pin_full_name)
        df = pl.read_parquet(paths)

        # If not running on Connect, cache the data.
        if os.getenv("LOCAL_DEV"):
            logger.info(f"Caching {pin_name}")
            Path(".cache").mkdir(exist_ok=True)
            df.write_parquet(cache_path)

    return df.lazy()


# ------------------------------------------------------------------------------
# Global state
# ------------------------------------------------------------------------------
username = "sam.edwardes"
vessel_verbose = read_data("vessel_verbose_clean")
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
        terminal_locations=terminal_locations,
    )


app = App(app_ui, server)
