import datetime
import os
from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from ipyleaflet import GeoJSON, Map, Marker
from loguru import logger
from pins import board_connect
from shiny import App, render, ui, reactive
from shinywidgets import output_widget, render_widget

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
vessel_history = (
    read_data("vessel_history_clean")
    .with_columns(
        (pl.col('ActualDepart') - pl.col('ScheduledDepart')).alias('Delay'),
    )
)

start_date = vessel_history.select(pl.col("Date").min()).collect().get_column("Date")[0]
end_date = vessel_history.select(pl.col("Date").max()).collect().get_column("Date")[0]

# ------------------------------------------------------------------------------
# UI logic
# ------------------------------------------------------------------------------


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(
            "selected_vessel_name",
            "Vessel Name:",
            ["All"] + vessel_verbose.collect().get_column("VesselName").unique().to_list(),
        ),
        ui.input_date_range(
            "selected_daterange",
            "Date range",
            start=start_date,
            end=end_date,
            min=start_date,
            max=end_date + datetime.timedelta(days=1),
        ),
        bg="#f8f8f8",
    ),
    ui.card(
        ui.card_header("Ferry routes"),
        output_widget("map"),
    ),
    ui.card(
        ui.card_header("Vessels"),
        ui.output_data_frame("vessel_trip_summary"),
    ),
    ui.card(
        ui.card_header("Routes"),
        ui.output_data_frame("routes_summary"),
    ),
    title="Seattle Ferry Delay Predictor",
)

# ------------------------------------------------------------------------------
# Server logic
# ------------------------------------------------------------------------------


def server(input, output, session):

    @reactive.calc
    def filtered_vessel_history() -> pl.LazyFrame:
        selected_vessel_name = input.selected_vessel_name().lower()
        start_date, end_date = input.selected_daterange()

        df = vessel_history

        if selected_vessel_name != "all":
            df = (
                df
                .filter(pl.col("Vessel") == selected_vessel_name)
            )

        df = (
            df
            .filter(
                pl.col("Date") >= pl.date(start_date.year, start_date.month, start_date.day),
                pl.col("Date") <= pl.date(end_date.year, end_date.month, end_date.day),
            )
        )

        return df

    @render_widget
    def map():
        hyatt_regency_seattle_location = (47.61453555315236, -122.33406011740034)
        map = Map(center=hyatt_regency_seattle_location, zoom=9)

        geo_json = GeoJSON(
            style={
                "opacity": 1,
                "dashArray": "9",
                "fillOpacity": 0.1,
                "weight": 1,
            },
            hover_style={"color": "white", "dashArray": "0", "fillOpacity": 0.5},
        )
        map.add_layer(geo_json)

        point = Marker(location=(52.204793, 0.121558), draggable=False)
        map.add_layer(point)

        return map

    @render.data_frame
    def vessel_trip_summary():
        df = (
            filtered_vessel_history()
            .group_by("Vessel")
            .agg(
                pl.col("Vessel").count().alias("Number of Trips"),
                pl.col("Delay").mean().alias("Average Delay (seconds)"),
            )
            .sort("Average Delay (seconds)", descending=True)
            .with_columns(
                pl.col('Vessel').str.to_titlecase()
            )
            .collect()
        )

        return render.DataGrid(df, width='100%', summary=False)


    @render.data_frame
    def routes_summary():
        df = (
            filtered_vessel_history()
            .with_columns(
                (pl.col('Departing') + ' -> ' + pl.col('Arriving')).alias('Route')
            )
            .group_by("Route")
            .agg(
                pl.col("Route").count().alias("Number of Trips"),
                pl.col("Delay").mean().alias("Average Delay (seconds)"),
            )
            .sort("Average Delay (seconds)", descending=True)
            .collect()
        )
        return render.DataGrid(df, width='100%', summary=False)


app = App(app_ui, server)
