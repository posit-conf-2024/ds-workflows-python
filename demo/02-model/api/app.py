from vetiver import VetiverModel
from dotenv import load_dotenv, find_dotenv
import vetiver
import pins
from sklearn.base import BaseEstimator, TransformerMixin
import sys

class DenseTransformer(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None, **params):
        return self

    def transform(self, X, y=None, **params):
        return X.toarray()

setattr(sys.modules['__main__'], 'DenseTransformer', DenseTransformer)

load_dotenv(find_dotenv())

b = pins.board_connect(allow_pickle_read=True)
v = VetiverModel.from_pin(b, 'sam.edwardes@posit.co/ferry_delay')

vetiver_api = vetiver.VetiverAPI(v)
api = vetiver_api.app