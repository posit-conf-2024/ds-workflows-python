from shiny import Inputs, Outputs, Session, module, render, ui
import datetime
import os
from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from ipyleaflet import GeoJSON, Map, Marker, AwesomeIcon, Popup, AntPath
from ipywidgets import HTML
from loguru import logger
from pins import board_connect
from shiny import App, render, ui, reactive
from shinywidgets import output_widget, render_widget


@module.ui
def data_explorer_ui(
    vessel_verbose: pl.LazyFrame,
    start_date: datetime.date,
    end_date: datetime.date,
):
    return ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "selected_vessel_name",
                "Vessel Name:",
                ["All"]
                + vessel_verbose.collect().get_column("VesselName").unique().to_list(),
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
            ui.card_header("Routes"),
            ui.output_data_frame("routes_summary"),
        ),
        ui.card(
            ui.card_header("Vessels"),
            ui.output_data_frame("vessel_trip_summary"),
        ),
    )


@module.server
def data_explorer_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    vessel_history: pl.LazyFrame,
    terminal_locations: pl.LazyFrame,
):
    @reactive.calc
    def filtered_vessel_history() -> pl.LazyFrame:
        selected_vessel_name = input.selected_vessel_name().lower()
        start_date, end_date = input.selected_daterange()

        df = vessel_history

        if selected_vessel_name != "all":
            df = df.filter(pl.col("Vessel") == selected_vessel_name)

        df = df.filter(
            pl.col("Date")
            >= pl.date(start_date.year, start_date.month, start_date.day),
            pl.col("Date") <= pl.date(end_date.year, end_date.month, end_date.day),
        )

        return df

    @render_widget
    def map():
        hyatt_regency_seattle_location = (47.61453555315236, -122.33406011740034)
        test_location = (48.0, -123)
        map = Map(center=(48, -122.5), zoom=7.8)

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

        # Add all of the terminals as markers
        ferry_icon = AwesomeIcon(name="ship")
        for i in terminal_locations.collect().to_dicts():
            # Create a marker for each terminal.
            marker = Marker(
                location=(i["Latitude"], i["Longitude"]),
                draggable=False,
                title=i["TerminalName"].title(),
                icon=ferry_icon,
                opacity=0.8,
            )
            map.add_layer(marker)

            # TODO: add pop-up markers
            # # Add pop-up information when the marker is clicked
            # message = HTML()
            # message.value = f"<b>{i["TerminalName"].title()}</b>"
            # message.placeholder = "Some HTML"
            # message.description = "Some HTML"

            # # Popup with a given location on the map:
            # popup = Popup(
            #     location=(i["Latitude"], i["Longitude"]),
            #     child=message,
            #     close_button=False,
            #     auto_close=False,
            #     close_on_escape_key=False
            # )
            # # map.add(popup)
            # marker.popup = popup

        # Add the Hyatt as a marker
        hotel_icon = AwesomeIcon(name="hotel", marker_color="red")
        map.add_layer(
            Marker(
                location=hyatt_regency_seattle_location,
                draggable=False,
                icon=hotel_icon,
            )
        )
        map.add_layer(Marker(location=test_location, draggable=False, icon=hotel_icon))

        # Add some paths
        ant_path = AntPath(
            locations=[hyatt_regency_seattle_location, test_location],
            dash_array=[1, 10],
            delay=1000,
            color="#7590ba",
            pulse_color="#3f6fba",
        )

        map.add(ant_path)

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
            .with_columns(pl.col("Vessel").str.to_titlecase())
            .collect()
        )

        return render.DataGrid(df, width="100%", summary=False)

    @render.data_frame
    def routes_summary():
        df = (
            filtered_vessel_history()
            .with_columns(
                (pl.col("Departing") + " -> " + pl.col("Arriving")).alias("Route")
            )
            .group_by("Route")
            .agg(
                pl.col("Route").count().alias("Number of Trips"),
                pl.col("Delay").mean().alias("Average Delay (seconds)"),
            )
            .sort("Average Delay (seconds)", descending=True)
            .collect()
        )
        return render.DataGrid(df, width="100%", summary=False)
