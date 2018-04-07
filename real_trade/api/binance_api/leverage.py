import json
from binance_api.servicebase import ServiceBase

class Leverage(ServiceBase):
    def positions(self, params = {}):
        # no leverage trading
        return json.dumps({"success":True, "data":[]})
