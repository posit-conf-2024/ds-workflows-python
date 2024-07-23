import polars as pl
from dotenv import load_dotenv
from loguru import logger
from shiny import App, ui

from src.database import get_con
from src.module_model_explorer import model_explorer_server, model_explorer_ui

# ------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------
load_dotenv()
pl.Config(thousands_separator=True)

# ------------------------------------------------------------------------------
# State to share with all modules
# ------------------------------------------------------------------------------
con = get_con()

# ------------------------------------------------------------------------------
# UI logic
# ------------------------------------------------------------------------------
app_ui = ui.page_navbar(
    ui.nav_panel("Model Explorer", model_explorer_ui("model_explorer_module", con=con)),
    title="Seattle Ferry Model & Data Explorer",
)

# ------------------------------------------------------------------------------
# Server logic
# ------------------------------------------------------------------------------
def server(input, output, session):
    model_explorer_server("model_explorer_module", con=con)


app = App(app_ui, server)
