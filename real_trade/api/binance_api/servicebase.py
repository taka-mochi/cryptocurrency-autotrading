from binance.exceptions import BinanceAPIException
from datetime import datetime
import pytz
import json

class ServiceBase:
    METHOD_GET = 'GET'
    METHOD_POST = 'POST'
    METHOD_DELETE = 'DELETE'

    def __init__(self, binanceInst):
        self.binance = binanceInst
        self.client = binanceInst.client
        if (binanceInst.DEBUG):
            self.logger = binanceInst.logger

    def _get_fail_retstr(self, detail=""):
        return '{"sucess":false, "reason":'+str(detail)+'}'

    def _get_except_retstr(self, binance_exception):
        e = binance_exception
        return self._get_fail_retstr(str(e.status_code) + ":" + str(e.message))

    def _gtctime_to_createdat_str(self, timestamp):
        t = datetime.fromtimestamp(timestamp, tz=pytz.utc)
        return datetime.strftime(t, "%Y-%m-%dT%H:%M:%S.000Z")
    
    def pair_to_symbol(self, pairname):
        return pairname.upper().replace("_", "")

    def symbol_to_pair(self, symbol):
        symbol = symbol.lower()
        if symbol.startswith("btc"):
            return symbol.replace("btc", "btc_")
        else:
            return symbol.replace("btc", "_btc")

    def _is_pair(self, pair_or_symbol):
         return "_" in pair_or_symbol

    def _is_symbol(self, pair_or_symbol):
        return not self._is_pair(pair_or_symbol)

    def to_symbol(self, pair_or_symbol):
        if self._is_symbol(pair_or_symbol): return pair_or_symbol
        return self.pair_to_symbol(pair_or_symbol)

    def to_pair(self, pair_or_symbol):
        if self._is_pair(pair_or_symbol): return pair_or_symbol
        return self.symbol_to_pair(pair_or_symbol)

    def _check_success(self, ret):
        if "code" not in ret: return True
        return ret["code"] > -1000

    def _process_ret(self, ret):
        if "code" not in ret: return json.dumps(ret)
        if ret["code"] <= -1000:
            # error
            ret["success"] = False
            return json.dumps(ret)

        ret["success"] = True
        return json.dumps(ret)
    
