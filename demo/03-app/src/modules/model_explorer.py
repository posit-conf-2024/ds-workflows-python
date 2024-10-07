import datetime
import json
import os
import random
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
import polars as pl
from ibis import _
from ibis.backends.duckdb import Backend
from ipyleaflet import AntPath, AwesomeIcon, DivIcon, GeoJSON, Map, Marker
from loguru import logger
from posit.connect import Client
from rich import inspect
from rich.pretty import pprint
from shiny import Inputs, Outputs, Session, module, reactive, render, ui
from shinywidgets import output_widget, render_widget

from src.timer import time_function


def get_route_options(con: Backend) -> dict:
    with Client() as client:
        username = client.me.username

    options_list = (
        con.table("vessel_history")
        .group_by(["Departing", "Arriving"])
        .aggregate(n=_.Departing.count())
        .order_by(_.n.desc())
        .to_polars()
        .to_dicts()
    )
    options_dict = {}
    for i in options_list:
        arriving = i["Arriving"]
        departing = i["Departing"]
        n_trips = i["n"]
        value = f"{arriving} | {departing}"
        label = f"{arriving.title()} to {departing.title()} ({n_trips:,} trips)"
        options_dict[value] = label
    return options_dict


def get_weather_code_options() -> dict[int, str]:
    """
    See API docs for details: https://open-meteo.com/en/docs.

    WMO Weather interpretation codes (WW)
    Code	Description
    0	Clear sky
    1, 2, 3	Mainly clear, partly cloudy, and overcast
    45, 48	Fog and depositing rime fog
    51, 53, 55	Drizzle: Light, moderate, and dense intensity
    56, 57	Freezing Drizzle: Light and dense intensity
    61, 63, 65	Rain: Slight, moderate and heavy intensity
    66, 67	Freezing Rain: Light and heavy intensity
    71, 73, 75	Snow fall: Slight, moderate, and heavy intensity
    77	Snow grains
    80, 81, 82	Rain showers: Slight, moderate, and violent
    85, 86	Snow showers slight and heavy
    95 *	Thunderstorm: Slight or moderate
    96, 99 *	Thunderstorm with slight and heavy hail
    """
    return {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Drizzle: Light intensity",
        53: "Drizzle: Moderate intensity",
        55: "Drizzle: Dense intensity",
        56: "Freezing Drizzle: Light intensity",
        57: "Freezing Drizzle: Dense intensity",
        61: "Rain: Slight intensity",
        63: "Rain: Moderate intensity",
        65: "Rain: Heavy intensity",
        66: "Freezing Rain: Light intensity",
        67: "Freezing Rain: Heavy intensity",
        71: "Snow fall: Slight intensity",
        73: "Snow fall: Moderate intensity",
        75: "Snow fall: Heavy intensity",
        77: "Snow grains",
        80: "Rain showers: Slight intensity",
        81: "Rain showers: Moderate intensity",
        82: "Rain showers: Violent intensity",
        85: "Snow showers: Slight intensity",
        86: "Snow showers: Heavy intensity",
        95: "Thunderstorm: Slight intensity",
        96: "Thunderstorm: with slight hail",
        99: "Thunderstorm: with heavy hail",
    }


def sidebar(con: Backend):
    sidebar_background_color = "#f8f8f8"

    with Client() as client:
        username = client.me.username

    vessel_names = (
        con.table("vessel_verbose")
        .select("VesselName")
        .to_polars()
        .get_column("VesselName")
        .to_list()
    )

    return ui.sidebar(
        ui.help_text(
            "The parameters below are inputs to the Ferry Delay Prediction Model. Adjust the parameters to see how they impact the predicted delay time."
        ),
        ui.accordion(
            ui.accordion_panel(
                "Basic Information",
                ui.input_select("selected_route", "Route", get_route_options(con)),
                ui.input_select("selected_vessel_name", "Vessel Name", vessel_names),
                style=f"background-color: {sidebar_background_color};",
            ),
            ui.accordion_panel(
                "Date and Time",
                ui.input_date(
                    "selected_date",
                    "Date",
                    value=datetime.date.today(),
                    min=datetime.date.today(),
                ),
                ui.input_slider(
                    "selected_hour", "Hour of Day", value=12, min=0, max=23
                ),
                style=f"background-color: {sidebar_background_color};",
            ),
            ui.accordion_panel(
                "Weather Basics",
                ui.input_select(
                    "selected_weather_code",
                    "Weather Code",
                    get_weather_code_options(),  # type: ignore
                ),
                ui.input_slider(
                    "selected_temperature",
                    "Temperature (°C)",
                    value=12,
                    min=-30,
                    max=40,
                ),
                ui.input_slider(
                    "selected_precipitation",
                    "Precipitation (mm)",
                    value=0,
                    min=0,
                    max=100,
                ),
                ui.input_slider(
                    "selected_cloud_cover",
                    "Cloud Cover (%)",
                    value=0,
                    min=0,
                    max=100,
                ),
                style=f"background-color: {sidebar_background_color};",
            ),
            ui.accordion_panel(
                "Wind",
                ui.input_slider(
                    "selected_wind_speed",
                    "Wind Speed",
                    value=0,
                    min=0,
                    max=100,
                ),
                ui.input_slider(
                    "selected_wind_gust",
                    "Wind Gusts",
                    value=0,
                    min=0,
                    max=100,
                ),
                ui.input_select(
                    "selected_wind_direction",
                    "Wind Direction",
                    {
                        0: "N ↑",
                        45: "NE ↗",
                        90: "E →",
                        135: "SE ↘",
                        180: "S ↓",
                        225: "SW ↙",
                        270: "W ←",
                        315: "NW ↖",
                    },  # type: ignore
                ),
                style=f"background-color: {sidebar_background_color};",
            ),
        ),
        bg=sidebar_background_color,
        width="400px",
    )


@module.ui
def model_explorer_ui(con: Backend):
    return ui.layout_sidebar(
        sidebar(con),
        # Value boxes
        ui.layout_column_wrap(
            ui.value_box(
                "Predicted Delay",
                ui.output_ui("predicted_delay_text"),
            ),
            ui.value_box("Average Delay", ui.output_ui("average_delay_text")),
            ui.value_box("Standard Deviation of Delay", ui.output_ui("std_delay_text")),
        ),
        # Map and delay distribution
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("Ferry route"),
                output_widget("map"),
            ),
            ui.card(
                ui.card_header("Distribution of Delays"),
                output_widget("distribution_of_delays_plot"),
            ),
        ),
        # Route history table
        ui.navset_card_pill(
            ui.nav_panel("Route History", ui.output_data_frame("route_history_table")),
            ui.nav_panel("Vessel Details", ui.output_code("vessel_details_output")),
            ui.nav_panel("Vessel Drawing", ui.output_ui("vessel_drawing_output")),
            ui.nav_panel("Vessel Silhouette", ui.output_ui("vessel_silhouette_output")),
        ),
    )


@module.server
def model_explorer_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    con: Backend,
):
    # Read in the datasets that are small and used by several
    # different parts of the server.
    vessel_verbose = con.sql("SELECT * FROM vessel_verbose").to_polars()
    terminal_locations = con.sql("SELECT * FROM terminal_locations").to_polars()

    @reactive.calc
    def get_starting_and_ending_terminal() -> tuple[str, str]:
        route = input.selected_route()
        start, end = [i.lower().strip() for i in route.split(" | ")]
        return start, end

    @time_function
    @reactive.calc
    def filtered_vessel_history() -> pl.LazyFrame:
        # fmt: off
        starting_terminal_name, ending_terminal_name = get_starting_and_ending_terminal()

        df = (
            con
            .table("vessel_history").filter(
                [
                    _.Departing == starting_terminal_name,
                    _.Arriving == ending_terminal_name
                ]
            )
            .to_polars()
            .lazy()
            .with_columns(
                (pl.col("ActualDepart") - pl.col("ScheduledDepart")).alias("Delay"),
            )
        )
        # fmt: on
        return df

    @reactive.calc
    def get_selected_vessel_data() -> dict[str, Any]:
        selected_vessel_data = vessel_verbose.filter(
            pl.col("VesselName") == input.selected_vessel_name()
        )
        return selected_vessel_data.to_dicts()[0]

    @reactive.calc
    @time_function
    def predict_delay() -> float:
        """
        The delay model is hosted on Posit Connect at this URL:
        https://connect.posit.it/content/823c479e-3d5e-4898-8801-a5c2cec97bb5
        """
        logger.info("Predicting ferry delay...")
        # Based on the selected vessel name, get all of the data related to that
        # vessel.
        selected_vessel_data = vessel_verbose.filter(
            pl.col("VesselName") == input.selected_vessel_name()
        ).to_dicts()[0]

        # Some of the vessels have not been rebuilt. When this applies, impute
        # the current year as the year rebuilt.
        if selected_vessel_data["YearRebuilt"]:
            year_rebuilt = selected_vessel_data["YearRebuilt"].year
        else:
            year_rebuilt = datetime.datetime.now().year

        prediction_input_data = {
            "Vessel": str(selected_vessel_data["VesselName"]),
            "Departing": str(get_starting_and_ending_terminal()[0]),
            "Arriving": str(get_starting_and_ending_terminal()[1]),
            "Weekday": int(input.selected_date().weekday() + 1),
            "Hour": int(input.selected_hour()),
            "ClassName": str(selected_vessel_data["ClassName"]),
            "SpeedInKnots": int(selected_vessel_data["SpeedInKnots"]),
            "EngineCount": int(selected_vessel_data["EngineCount"]),
            "Horsepower": int(selected_vessel_data["Horsepower"]),
            "MaxPassengerCount": int(selected_vessel_data["MaxPassengerCount"]),
            "PassengerOnly": None,  # selected_vessel_data["PassengerOnly"],
            "FastFerry": None,  # selected_vessel_data["FastFerry"],
            "PropulsionInfo": str(selected_vessel_data["PropulsionInfo"]),
            "YearBuilt": int(selected_vessel_data["YearBuilt"].year),
            "YearRebuilt": int(year_rebuilt),
            "departing_weather_code": str(input.selected_weather_code()),
            "departing_temperature_2m": int(input.selected_temperature()),
            "departing_precipitation": int(input.selected_precipitation()),
            "departing_cloud_cover": int(input.selected_cloud_cover()),
            "departing_wind_speed_10m": int(input.selected_wind_speed()),
            "departing_wind_direction_10m": int(input.selected_wind_direction()),
            "departing_wind_gusts_10m": int(input.selected_wind_gust()),
            "arriving_weather_code": str(input.selected_weather_code()),
            "arriving_temperature_2m": int(input.selected_temperature()),
            "arriving_precipitation": int(input.selected_precipitation()),
            "arriving_cloud_cover": int(input.selected_cloud_cover()),
            "arriving_wind_speed_10m": int(input.selected_wind_speed()),
            "arriving_wind_direction_10m": int(input.selected_wind_direction()),
            "arriving_wind_gusts_10m": int(input.selected_wind_gust()),
        }

        # Make the prediction
        endpoint_url = os.environ["FERRY_MODEL_API_URL"]

        headers = {
            "Authorization": f'Key {os.environ["CONNECT_API_KEY"]}',
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        with httpx.Client() as client:
            response = httpx.post(
                endpoint_url, headers=headers, json=[prediction_input_data]
            )

        logger.info(f"{response=}")

        if response.status_code != 200:
            logger.error(prediction_input_data)
            logger.error(f"{response.text}")
            logger.error(response.request.url)
            logger.error(response.request.headers)
            logger.error(response.request.content)
            return random.randint(-3, 23)
        else:
            logger.info(f"Model response: {response.json()}")
            return round(response.json()["predict"][0], 1)

    @render.text
    def predicted_delay_text():
        return f"{predict_delay()} minutes"

    @render.text
    def average_delay_text():
        avg_delay = (
            filtered_vessel_history()
            .select(pl.col("Delay").mean().dt.total_minutes())
            .collect()
            .item()
        )
        return f"{avg_delay} minutes"

    @render.text
    def std_delay_text():
        standard_deviation_delay = (
            filtered_vessel_history()
            .select(pl.col("Delay").std().dt.total_minutes())
            .collect()
            .item()
        )
        return f"{standard_deviation_delay} minutes"

    @render_widget
    def map():
        # Get terminal data
        (
            starting_terminal_name,
            ending_terminal_name,
        ) = get_starting_and_ending_terminal()

        starting_terminal_data = (
            terminal_locations.filter(
                pl.col("TerminalName").eq(starting_terminal_name)
            ).to_dicts()
        )[0]

        ending_terminal_data = (
            terminal_locations.filter(
                pl.col("TerminalName").eq(ending_terminal_name)
            ).to_dicts()
        )[0]

        # Remember latitude runs east -> west
        # longitude runs north -> south

        # Figure out the starting bounds
        if starting_terminal_data["Latitude"] > ending_terminal_data["Latitude"]:
            north = starting_terminal_data["Latitude"]
            south = ending_terminal_data["Latitude"]
        else:
            north = ending_terminal_data["Latitude"]
            south = starting_terminal_data["Latitude"]

        if starting_terminal_data["Longitude"] > ending_terminal_data["Longitude"]:
            east = starting_terminal_data["Longitude"]
            west = ending_terminal_data["Longitude"]
        else:
            east = ending_terminal_data["Longitude"]
            west = starting_terminal_data["Longitude"]

        # The lat/lon bounds in the form [[south, west], [north, east]].
        starting_bounds = [
            [south - 0.02, west - 0.01],
            [north + 0.02, east + 0.01],
        ]

        # Create map
        map = Map()
        map.fit_bounds(starting_bounds)
        map.add_layer(
            GeoJSON(
                style={
                    "opacity": 1,
                    "dashArray": "9",
                    "fillOpacity": 0.1,
                    "weight": 1,
                },
                hover_style={"color": "white", "dashArray": "0", "fillOpacity": 0.5},
            )
        )

        # Add the Hyatt as a marker
        hyatt_regency_seattle_location = (47.61453555315236, -122.33406011740034)
        hotel_icon = AwesomeIcon(name="hotel", marker_color="blue")
        map.add_layer(
            Marker(
                location=hyatt_regency_seattle_location,
                draggable=False,
                icon=hotel_icon,
            )
        )

        # Add the terminals as markers
        for start_finish, terminal in zip(
            ["start", "finish"], [starting_terminal_data, ending_terminal_data]
        ):
            # Look up the terminal location
            # Create a marker for each terminal.
            if start_finish == "start":
                ferry_icon = AwesomeIcon(name="ship", marker_color="green")
            else:
                ferry_icon = AwesomeIcon(name="flag-checkered", marker_color="black")
            text = DivIcon(
                html=terminal["TerminalName"].title(),
                icon_size=(len(terminal["TerminalName"]) * 7, 20),
            )
            map.add_layer(
                Marker(
                    location=(terminal["Latitude"] - 0.005, terminal["Longitude"]),
                    icon=text,
                )
            )
            marker = Marker(
                location=(terminal["Latitude"], terminal["Longitude"]),
                draggable=False,
                title=f'{terminal["TerminalName"].title()} ({terminal["Latitude"]}, {terminal["Longitude"]})',
                icon=ferry_icon,
            )
            map.add_layer(marker)

        # Add path between terminals
        prediction = predict_delay()
        avg_delay = (
            filtered_vessel_history()
            .select(pl.col("Delay").mean().dt.total_minutes())
            .collect()
            .item()
        )

        # When the prediction is greater than the average delay, the line will
        # be red and the pulse will be yellow. The line will also move slower.
        if prediction > avg_delay:
            ant_line_colour = "red"
            ant_line_pulse_colour = "yellow"
            delay = 5_000
        else:
            ant_line_colour = "green"
            ant_line_pulse_colour = "blue"
            delay = 1_000

        ant_path = AntPath(
            locations=[
                (
                    starting_terminal_data["Latitude"],
                    starting_terminal_data["Longitude"],
                ),
                (ending_terminal_data["Latitude"], ending_terminal_data["Longitude"]),
            ],
            dash_array=[1, 10],
            delay=delay,
            color=ant_line_colour,
            pulse_color=ant_line_pulse_colour,
        )

        map.add(ant_path)

        return map

    @render_widget
    def distribution_of_delays_plot():
        prediction = predict_delay()
        df = (
            filtered_vessel_history()
            .select(pl.col("Delay").dt.total_minutes())
            .collect()
            .to_pandas()
        )
        fig = px.histogram(
            df, x="Delay", labels={"Delay": "Delay (minutes)", "count": "Count"}
        )
        fig.add_vline(
            x=prediction,
            line_color="red",
            annotation_text=f"Prediction ({prediction} minutes)",
            annotation=dict(font_color="red"),
        )
        return fig

    @render.data_frame
    def route_history_table():
        df = (
            filtered_vessel_history()
            .sort("ScheduledDepart", descending=True)
            .select(
                pl.col(pl.String).str.to_titlecase(),
                pl.col("ScheduledDepart")
                .dt.to_string(r"%b %d, %Y @ %H:%M")
                .alias("Scheduled Departure"),
                pl.col("ActualDepart")
                .dt.to_string(r"%b %d, %Y @ %H:%M")
                .alias("Actual Departure"),
                pl.col("Delay").dt.total_minutes().alias("Delay (Minutes)"),
            )
            .collect()
        )
        return render.DataGrid(df, width="100%", summary=False)

    @render.code
    def vessel_details_output():
        selected_vessel_data = get_selected_vessel_data()

        def json_default(value):
            """
            json.dumps does not know how to serialize datetime objects. This
            function will handle that case.
            """
            if isinstance(value, datetime.datetime):
                return value.isoformat()
            else:
                return str(value)

        return json.dumps(selected_vessel_data, default=json_default, indent=4)

    @render.ui
    def vessel_drawing_output():
        selected_vessel_data = get_selected_vessel_data()
        return ui.tags.img(src=selected_vessel_data["DrawingImg"])

    @render.ui
    def vessel_silhouette_output():
        selected_vessel_data = get_selected_vessel_data()
        return ui.tags.img(src=selected_vessel_data["SilhouetteImg"])
