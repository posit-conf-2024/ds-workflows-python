from vetiver import VetiverModel
from dotenv import load_dotenv, find_dotenv
import vetiver
import pins

from sklearn.base import TransformerMixin

class DenseTransformer(TransformerMixin):
    def fit(self, X, y=None, **fit_params):
        return self

    def transform(self, X, y=None, **fit_params):
        return X.toarray()
load_dotenv(find_dotenv())

b = pins.board_connect(server_url='https://pub.ferryland.posit.team/', allow_pickle_read=True)
v = VetiverModel.from_pin(b, 'brooklynbagel/ferry_delay', version = '266')

vetiver_api = vetiver.VetiverAPI(v)
api = vetiver_api.app
# vetiver_api.run()
