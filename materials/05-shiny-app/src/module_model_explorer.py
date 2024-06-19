import random
from textwrap import dedent
from loguru import logger
from shiny import Inputs, Outputs, Session, module, render, ui, req
import datetime

import polars as pl
from ipyleaflet import GeoJSON, Map, Marker, AwesomeIcon, AntPath, FeatureGroup
from shiny import render, ui, reactive
from shinywidgets import output_widget, render_widget


def get_terminal_options(vessel_history: pl.LazyFrame, col_name: str = "Departing") -> dict:
    options = (
        vessel_history
        .select(pl.col(col_name))
        .group_by(col_name)
        .count()
        .sort("count", descending=True)
        .collect()
        .to_dicts()
    )
    options_dict = {}
    for i in options:
        terminal_name = i[col_name]
        number_of_trips = i["count"]
        options_dict[terminal_name] = f"{terminal_name.title()} ({number_of_trips:,} Voyages)"
    return options_dict


@module.ui
def model_explorer_ui(vessel_verbose: pl.LazyFrame, vessel_history: pl.LazyFrame):
    logger.info("Initializing UI ------------------------------")

    starting_terminal_options = get_terminal_options(vessel_history, "Departing")
    ending_terminal_options = get_terminal_options(
        vessel_history.filter(pl.col("Departing").eq("seattle")),
        "Arriving"
    )

    return ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "selected_starting_terminal",
                "Starting Terminal:",
                starting_terminal_options,
                selected="seattle"

            ),
            ui.input_select(
                "selected_ending_terminal",
                "Ending Terminal:",
                ending_terminal_options,
                selected="bremerton"
            ),
            ui.input_date(
                "selected_date",
                "Date",
                value=datetime.date.today(),
                min=datetime.date.today(),
            ),
            ui.input_select(
                "selected_weather", "Weather:", ["cloudy", "sunny", "rainy"]
            ),
            ui.input_slider(
                "selected_wind_speed", "Wind Speed:", value=10, min=0, max=100
            ),
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
        ),
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("Ferry route"),
                output_widget("map"),
            ),
            ui.card(ui.card_header("Quick facts"), ui.output_ui("quick_facts")),
        ),
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
    @reactive.effect
    @reactive.event(input.selected_starting_terminal, ignore_init=True)
    def update_ending_terminal_options():
        logger.info("Updating ending terminal options")
        starting_terminal = input.selected_starting_terminal()
        ending_terminal_options = get_terminal_options(
            vessel_history.filter(pl.col("Departing").eq(starting_terminal)),
            "Arriving"
        )
        ui.update_select("selected_ending_terminal", choices=ending_terminal_options)

    @reactive.calc
    def starting_terminal_location() -> dict:
        logger.info("Getting starting terminal data")
        terminal_name = input.selected_starting_terminal()
        df = terminal_locations.filter(
            pl.col("TerminalName").eq(terminal_name)
        ).collect()
        if df.shape[0] > 1:
            raise ValueError(f"More than one terminal found with name {terminal_name}")
        return df.to_dicts()[0]

    @reactive.calc
    def ending_terminal_location() -> dict:
        logger.info("Getting ending terminal data.")
        terminal_name = input.selected_ending_terminal()
        df = terminal_locations.filter(
            pl.col("TerminalName").eq(terminal_name)
        ).collect()
        if df.shape[0] > 1:
            raise ValueError(f"More than one terminal found with name {terminal_name}")
        return df.to_dicts()[0]

    @reactive.calc
    def filtered_vessel_history() -> pl.LazyFrame:
        with reactive.isolate():
            starting = input.selected_starting_terminal()
        ending = input.selected_ending_terminal()
        logger.info(f"Filtering vessel history on {starting} and {ending}")
        df = vessel_history.filter(
            pl.col("Departing").eq(starting),
            pl.col("Arriving").eq(ending),
        )
        return df
    #
    @reactive.calc
    def predict_delay() -> float:
        """
        This function is a placeholder, once the model is live update it to call the
        Vetiver API.
        """
        logger.info("Predicting delay")
        # Get input data
        with reactive.isolate():
            starting_terminal = starting_terminal_location()
        ending_terminal = ending_terminal_location()
        weather = input.selected_weather()
        wind_speed = input.selected_wind_speed()
        wind_direction = input.selected_wind_direction()
        vessel_name = input.selected_vessel_name()
        date = input.selected_date()

        # Temporary fake prediction
        df = filtered_vessel_history()

        avg_delay = (
            df
            .select(pl.col("Delay").mean().dt.total_minutes())
            .collect()
            .item()
        )
        logger.info(f"{avg_delay=}")

        standard_deviation_delay = (
            df
            .select(pl.col("Delay").std().dt.total_minutes())
            .collect()
            .item()
        )
        logger.info(f"{standard_deviation_delay=}")

        return round(
            random.normalvariate(mu=avg_delay, sigma=standard_deviation_delay), 1
        )

    @render_widget
    def map():
        # Get terminal data
        starting_terminal = starting_terminal_location()
        ending_terminal = ending_terminal_location()

        # Remember latitude runs east -> west
        # longitude runs north -> south

        # Figure out the starting bounds
        if starting_terminal["Latitude"] > ending_terminal["Latitude"]:
            north = starting_terminal["Latitude"]
            south = ending_terminal["Latitude"]
        else:
            north = ending_terminal["Latitude"]
            south = starting_terminal["Latitude"]

        if starting_terminal["Longitude"] > ending_terminal["Longitude"]:
            east = starting_terminal["Longitude"]
            west = ending_terminal["Longitude"]
        else:
            east = ending_terminal["Longitude"]
            west = starting_terminal["Longitude"]

        # Calculate the center
        center = (
            (starting_terminal["Latitude"] + ending_terminal["Latitude"]) / 2,
            (starting_terminal["Longitude"] + starting_terminal["Longitude"]) / 2
        )

        # The lat/lon bounds in the form [[south, west], [north, east]].
        starting_bounds = [
            [south - 0.02, west - 0.01],
            [north + 0.02, east + 0.01],
        ]

        # Create map
        map = Map()
        map.fit_bounds(starting_bounds)
        map.add_layer(GeoJSON(
            style={
                "opacity": 1,
                "dashArray": "9",
                "fillOpacity": 0.1,
                "weight": 1,
            },
            hover_style={"color": "white", "dashArray": "0", "fillOpacity": 0.5},
        ))

        # Add the Hyatt as a marker
        hyatt_regency_seattle_location = (47.61453555315236, -122.33406011740034)
        hotel_icon = AwesomeIcon(name="hotel", marker_color="red")
        map.add_layer(
            Marker(
                location=hyatt_regency_seattle_location,
                draggable=False,
                icon=hotel_icon,
            )
        )

        # Add all of the terminals as markers
        for start_finish, terminal in zip(["start", "finish"], [starting_terminal, ending_terminal]):
            # Look up the terminal location
            # Create a marker for each terminal.
            if start_finish == "start":
                ferry_icon = AwesomeIcon(name="ship", marker_color="green")
            else:
                ferry_icon = AwesomeIcon(name="ship", marker_color="red")
            marker = Marker(
                location=(terminal["Latitude"], terminal["Longitude"]),
                draggable=False,
                title=f"{terminal["TerminalName"].title()} ({terminal["Latitude"]}, {terminal["Longitude"]})",
                icon=ferry_icon,
            )
            map.add_layer(marker)

        # Add path between terminals
        ant_path = AntPath(
            locations=[
                (starting_terminal["Latitude"], starting_terminal["Longitude"]),
                (ending_terminal["Latitude"], ending_terminal["Longitude"]),
            ],
            dash_array=[1, 10],
            delay=1000,
            color="#7590ba",
            pulse_color="#3f6fba",
        )

        map.add(ant_path)

        return map

    @render.ui
    def quick_facts():
        # Get input data
        starting_terminal = starting_terminal_location()
        ending_terminal = ending_terminal_location()
        weather = input.selected_weather()
        wind_speed = input.selected_wind_speed()
        wind_direction = input.selected_wind_direction()
        vessel_name = input.selected_vessel_name()
        date = input.selected_date()

        # Make prediction
        predicted_delay = predict_delay()

        # Summary data
        avg_delay = (
            filtered_vessel_history()
            .select(pl.col("Delay").mean().dt.total_minutes())
            .collect()
            .item()
        )
        standard_deviation_delay = (
            filtered_vessel_history()
            .select(pl.col("Delay").std().dt.total_minutes())
            .collect()
            .item()
        )
        avg_trips_per_day = int(
            filtered_vessel_history()
            .select(pl.col("Date").dt.round("1d").cast(pl.Date))
            .group_by("Date")
            .count()
            .select(pl.col("count").mean())
            .collect()
            .item()
        )

        text = f"""
        The predicted delay is **{predicted_delay}** minutes.

        - **Selected route:** {starting_terminal['TerminalName'].title()} to {ending_terminal['TerminalName'].title()}
        - **Average delay:** {avg_delay} minutes with a standard deviation of {standard_deviation_delay} minutes.
        - **Average trips/day:** {avg_trips_per_day}
        """

        # Render the UI
        return ui.markdown(dedent(text).strip())

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
