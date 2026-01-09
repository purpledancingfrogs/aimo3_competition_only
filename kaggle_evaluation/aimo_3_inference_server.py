import kaggle_evaluation.core.templates

import aimo_3_gateway


# AUREON_PATHFIX
import os as _os, sys as _sys
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _ROOT not in _sys.path: _sys.path.insert(0, _ROOT)

class AIMO3InferenceServer(kaggle_evaluation.core.templates.InferenceServer):
    def __init__(self, data_paths=None):
        # Register at least one endpoint listener for kaggle_evaluation.core.templates.InferenceServer
        super().__init__(self.predict)
        self._data_paths = data_paths

    def predict(self, df):
        from .aimo_3_gateway import AIMO3Gateway
        gw = AIMO3Gateway(self._data_paths)
        return gw.predict(df)

    def _get_gateway_for_test(self, data_paths=None, *args, **kwargs):
        return aimo_3_gateway.AIMO3Gateway(data_paths)
