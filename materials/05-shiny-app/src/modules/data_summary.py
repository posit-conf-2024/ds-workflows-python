import great_tables.shiny as gts
import ibis
import polars.selectors as cs
from great_tables import GT
from ibis import _
from ibis.backends.postgres import Backend
from shiny import Inputs, Outputs, Session, module, ui


@module.ui
def data_summary_ui(con: Backend):
    return ui.tags.div(
        gts.output_gt("table")
    )


@module.server
def data_summary_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    con: Backend,
):
    @output
    @gts.render_gt
    def table():
        df = (
            con
            .table("vessel_history_clean")
            .mutate(
                DelayMinutes=_.ActualDepart.delta(_.ScheduledDepart, "second") / 60
            )
            .group_by(["Departing", "Arriving"])
            .agg(
                NumTrips=_.Departing.count(),
                AverageDelay=_.DelayMinutes.mean(),
                StandardDeviationDelay=_.DelayMinutes.std(),
            )
            .order_by(ibis.desc("AverageDelay"))
            .to_polars()
        )
        return (
            GT(df)
            .tab_header("Delay Stats by Route")
            .tab_spanner(label="Delay in Minutes", columns=cs.ends_with("Delay"))
            .cols_label(
                NumTrips="Number of Trips",
                AverageDelay="Average",
                StandardDeviationDelay="Standard"
            )
            .fmt_number(
                columns=cs.ends_with("Delay"),
                compact=True,
                decimals=2,
            )
            .fmt_number(
                columns=cs.ends_with("Trips"),
                compact=True,
            )
            .data_color(
                columns=["NumTrips"],
                palette=[
                    "#00A600", "#E6E600", "#E8C32E", "#D69C4E", "#Dc863B", "sienna", "sienna4", "tomato4", "brown"
                ],
                domain=[60_000, 0]
                )
        )
