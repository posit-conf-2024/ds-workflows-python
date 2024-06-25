import datetime
import random

import plotly.express as px
import polars as pl
from ipyleaflet import AntPath, AwesomeIcon, DivIcon, GeoJSON, Map, Marker
from loguru import logger
from shiny import Inputs, Outputs, Session, module, reactive, render, ui
from shinywidgets import output_widget, render_widget


def get_route_options(vessel_history: pl.LazyFrame) -> dict:
    options_list = (
        vessel_history.group_by("Departing", "Arriving")
        .count()
        .sort("count", descending=True)
        .collect()
        .to_dicts()
    )
    options_dict = {}
    for i in options_list:
        arriving = i["Arriving"]
        departing = i["Departing"]
        n_trips = i["count"]
        value = f"{arriving} | {departing}"
        label = f"{arriving.title()} to {departing.title()} ({n_trips:,} trips)"
        options_dict[value] = label
    return options_dict


def sidebar(vessel_history: pl.LazyFrame, vessel_verbose: pl.LazyFrame):
    return ui.sidebar(
        ui.input_select(
            "selected_route",
            "Route",
            get_route_options(vessel_history),
        ),
        # TODO: add button to reverse route
        ui.input_date(
            "selected_date",
            "Date",
            value=datetime.date.today(),
            min=datetime.date.today(),
        ),
        ui.input_select("selected_weather", "Weather:", ["cloudy", "sunny", "rainy"]),
        ui.input_slider("selected_wind_speed", "Wind Speed:", value=10, min=0, max=100),
        ui.input_select(
            "selected_wind_direction",
            "Wind Direction",
            ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        ),
        ui.input_select(
            "selected_vessel_name",
            "Vessel Name:",
            ["All"]
            + vessel_verbose.collect().get_column("VesselName").unique().to_list(),
        ),
        bg="#f8f8f8",
        width="400px",
    )


@module.ui
def model_explorer_ui(vessel_verbose: pl.LazyFrame, vessel_history: pl.LazyFrame):
    return ui.layout_sidebar(
        sidebar(vessel_verbose=vessel_verbose, vessel_history=vessel_history),
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
        ui.card(
            ui.card_header("Route history"), ui.output_data_frame("route_history_table")
        ),
    )


@module.server
def model_explorer_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    vessel_history: pl.LazyFrame,
    terminal_locations: pl.LazyFrame,
):
    @reactive.calc
    def get_starting_and_ending_terminal() -> tuple[str, str]:
        route = input.selected_route()
        logger.info(f"{route=}")
        start, end = [i.lower().strip() for i in route.split(" | ")]
        logger.info(f"{start=}")
        logger.info(f"{end=}")
        return start, end

    @reactive.calc
    def filtered_vessel_history() -> pl.LazyFrame:
        (
            starting_terminal_name,
            ending_terminal_name,
        ) = get_starting_and_ending_terminal()
        logger.info(
            f"Filtering vessel history on {starting_terminal_name} and {ending_terminal_name}"
        )
        df = vessel_history.filter(
            pl.col("Departing").eq(starting_terminal_name),
            pl.col("Arriving").eq(ending_terminal_name),
        )
        return df

    @reactive.calc
    def predict_delay() -> float:
        """
        This function is a placeholder, once the model is live update it to call the
        Vetiver API.
        """
        logger.info("Predicting delay")
        # Get input data
        (
            starting_terminal_name,
            ending_terminal_name,
        ) = get_starting_and_ending_terminal()
        weather = input.selected_weather()
        wind_speed = input.selected_wind_speed()
        wind_direction = input.selected_wind_direction()
        vessel_name = input.selected_vessel_name()
        date = input.selected_date()

        # Temporary fake prediction
        df = filtered_vessel_history()

        avg_delay = (
            df.select(pl.col("Delay").mean().dt.total_minutes()).collect().item()
        )
        logger.info(f"{avg_delay=}")

        standard_deviation_delay = (
            df.select(pl.col("Delay").std().dt.total_minutes()).collect().item()
        )
        logger.info(f"{standard_deviation_delay=}")

        return round(
            random.normalvariate(mu=avg_delay, sigma=standard_deviation_delay), 1
        )

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
            terminal_locations.filter(pl.col("TerminalName").eq(starting_terminal_name))
            .collect()
            .to_dicts()
        )[0]

        ending_terminal_data = (
            terminal_locations.filter(pl.col("TerminalName").eq(ending_terminal_name))
            .collect()
            .to_dicts()
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

        # Add all of the terminals as markers
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
                title=f"{terminal["TerminalName"].title()} ({terminal["Latitude"]}, {terminal["Longitude"]})",
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
        if prediction > avg_delay:
            ant_line_colour = "red"
            ant_line_pulse_colour = "yellow"
        else:
            ant_line_colour = "green"
            ant_line_pulse_colour = "blue"

        ant_path = AntPath(
            locations=[
                (
                    starting_terminal_data["Latitude"],
                    starting_terminal_data["Longitude"],
                ),
                (ending_terminal_data["Latitude"], ending_terminal_data["Longitude"]),
            ],
            dash_array=[1, 10],
            delay=1000,
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