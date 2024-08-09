import datetime
import os
from dataclasses import dataclass, field

import httpx
import polars as pl


@dataclass
class VesselsAPI:
    """
    API endpoint for VessselsAPI: https://www.wsdot.wa.gov/ferries/api/vessels/rest/help
    """

    base_url: str = "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest"
    wsdot_access_code: str = field(
        default_factory=lambda: os.environ["WSDOT_ACCESS_CODE"]
    )
    params: dict = field(init=False)

    def __post_init__(self):
        self.params = {"apiaccesscode": self.wsdot_access_code}

    def call_api(self, endpoint: str, timeout: float = 10.0) -> pl.DataFrame:
        with httpx.Client(
            base_url=self.base_url, params=self.params, timeout=timeout
        ) as client:
            r = client.get(endpoint)
            data = r.json()
            df = pl.DataFrame(data)
            return df

    def cache_flush_date(self) -> pl.DataFrame:
        endopint = "/cacheflushdate"
        return self.call_api(endopint)

    def vessel_accommodations(self, vessel_id: str | None = None) -> pl.DataFrame:
        if vessel_id:
            endpoint = f"/vesselaccommodations/{vessel_id}"
        else:
            endpoint = "/vesselaccommodations"
        return self.call_api(endpoint)

    def vessel_basics(self, vessel_id: str | None = None) -> pl.DataFrame:
        if vessel_id:
            endpoint = f"/vesselbasics/{vessel_id}"
        else:
            endpoint = "/vesselbasics"
        return self.call_api(endpoint)

    def vessel_history(
        self,
        vessel_name: str | None = None,
        date_start: datetime.date | None = None,
        date_end: datetime.date | None = None,
    ) -> pl.DataFrame:
        if vessel_name and date_start and date_end:
            url = f"{self.base_url}/vesselhistory/{vessel_name}/{date_start}/{date_end}"
        elif vessel_name or date_start or date_end:
            raise ValueError(
                "Must provide all of `vessel_name`, `date_start`, and `date_end` or none of the arguments"
            )
        else:
            url = f"{self.base_url}/vesselhistory"
        return self.call_api(url, timeout=30.0)

    def vessel_locations(self, vessel_id: str | None = None) -> pl.DataFrame:
        if vessel_id:
            endpoint = f"/vessellocations/{vessel_id}"
        else:
            endpoint = "/vessellocations"
        return self.call_api(endpoint)

    def vessel_stats(self, vessel_id: str | None = None) -> pl.DataFrame:
        if vessel_id:
            endpoint = f"/vesselstats/{vessel_id}"
        else:
            endpoint = "/vesselstats"
        return self.call_api(endpoint)

    def vessel_verbose(self, vessel_id: str | None = None) -> pl.DataFrame:
        if vessel_id:
            endpoint = f"/vesselverbose/{vessel_id}"
        else:
            endpoint = "/vesselverbose"
        return self.call_api(endpoint)
