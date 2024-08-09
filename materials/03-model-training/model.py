from sklearn.base import TransformerMixin
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline

class DenseTransformer(TransformerMixin):
    def fit(self, X, y=None, **fit_params):
        return self

    def transform(self, X, y=None, **fit_params):
        return X.toarray()

numeric_features = [
    "SpeedInKnots",
    "EngineCount",
    "Horsepower",
    "MaxPassengerCount",
    # "PassengerOnly",
    # "FastFerry",
    "YearBuilt",
    "YearRebuilt",
    "departing_temperature_2m",
    # "departing_precipitation",
    "departing_cloud_cover",
    "departing_wind_speed_10m",
    "departing_wind_direction_10m",
    "departing_wind_gusts_10m",
    "arriving_temperature_2m",
    # "arriving_precipitation",
    "arriving_cloud_cover",
    "arriving_wind_speed_10m",
    "arriving_wind_direction_10m",
    "arriving_wind_gusts_10m",
]

categorical_features = [
    "Vessel",
    "Month",
    "Weekday",
    "Hour",
    "Departing",
    "Arriving",
    "ClassName",
    "PropulsionInfo",
    "departing_weather_code",
    "arriving_weather_code",
]

preprocessor = ColumnTransformer(
    [
        # this just passes the variables through as-is
        ("num", "passthrough", numeric_features),
        # this one-hot encodes the variables
        ("cat", OneHotEncoder(), categorical_features),
    ]
)

regressor = HistGradientBoostingRegressor(verbose=2, random_state=2)

model = Pipeline(
    [
        ("preprocessor", preprocessor),
        ("density", DenseTransformer()),
        ("regressor", regressor),
    ]
)