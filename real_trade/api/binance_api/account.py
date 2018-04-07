import json
from binance_api.servicebase import ServiceBase
from binance.exceptions import BinanceAPIException

class Account(ServiceBase):
    def balance(self, params = {}):
        try:
            info = self.client.get_account()
        except BinanceAPIException as e:
            return self._get_except_retstr(e)

        if info is None: return self._get_fail_retstr("None returned")
        if "balances" not in info: return self._get_fail_retstr("no balances entry")
        if not self._check_success(info):
            return self._process_ret(info)
        
        balances = info["balances"]
        # flatten
        result = {}
        for balance in balances:
            asset = balance["asset"]
            result[asset.lower()] = balance["free"]
            result[asset.lower()+"_reserved"] = balance["locked"]

        result["success"] = True
        return json.dumps(result)

    def leverage_balance(self):
        return json.dumps({"success":True, "margin":{"jpy":0,"btc":0}, "margin_available":{"jpy":0,"btc":0}})
    
    """
    def info(self, params = {}):
        return self.coinCheck.request(ServiceBase.METHOD_GET, self.baseUrl, params)
    """

if __name__ == "__main__":
    from binance_api import Binance
    import os

    api_key = None
    secret_key = None
    with open(os.path.join(os.path.dirname(__file__), "key/test_binance_key.txt")) as r:
        api_key = r.readline().strip()
        secret_key = r.readline().strip()

    api = Binance(api_key, secret_key)

    balance = api.account.balance()
    print(balance)
