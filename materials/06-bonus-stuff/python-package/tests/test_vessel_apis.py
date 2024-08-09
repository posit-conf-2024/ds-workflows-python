from datetime import date

from rich.console import Console

from ferryland.ferryland import VesselsAPI

console = Console()
vessels_api = VesselsAPI()

console.rule("Vessel Accomodations")
vessel_accommodations = vessels_api.vessel_accommodations()
print(vessel_accommodations)

console.rule("Vessel History")
vessel_history = vessels_api.vessel_history(
    vessel_name="Spokane", date_start=date(2024, 1, 1), date_end=date(2024, 1, 7)
)
print(vessel_history)

console.rule("Vessel Verbose")
vessel_verbose = vessels_api.vessel_verbose()
print(vessel_verbose)
