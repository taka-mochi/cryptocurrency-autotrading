# coding: utf-8

from binance_api.servicebase import ServiceBase
import json
from binance.client import Client
from binance.exceptions import BinanceAPIException

class Order(ServiceBase):
    def _get_filter(self, symbol, filter_name):
        if symbol is None: return None
        exinfo = self.binance.exchange_info
        if symbol not in exinfo: return None

        return exinfo[symbol][filter_name]
    
    def tick_price(self, symbol_or_pair = None):
        filters = self._get_filter(self.to_symbol(symbol_or_pair), "price")
        if filters is None: return None

        return float(filters["tickSize"])
    
    def min_create_amount(self, symbol_or_pair = None):
        filters = self._get_filter(self.to_symbol(symbol_or_pair), "lot")
        if filters is None: return None

        return float(filters["minQty"])

    def tick_amount(self, symbol_or_pair = None):
        filters = self._get_filter(self.to_symbol(symbol_or_pair), "lot")
        if filters is None: return None

        return float(filters["stepSize"])


    def create(self, params = {}):
        is_test_mode = "test_mode" in self.binance.options and self.binance.options["test_mode"] is True
        client = self.client

        # convert param from cc to binance style
        # SYMBOL
        symbol = self.pair_to_symbol(params["pair"])

        # SIDE
        # ORDER_TYPE (limit or market)
        side   = None
        is_limit_order = None
        order_type_str = params["order_type"].lower()
        if order_type_str == "buy":
            side = Client.SIDE_BUY
            is_limit_order = True
        elif order_type_str == "sell":
            side = Client.SIDE_SELL
            is_limit_order = True
        elif order_type_str == "market_buy":
            side = Client.SIDE_BUY
            is_limit_order = False
        elif order_type_str == "market_sell":
            side = Client.SIDE_SELL
            is_limit_order = False
        else:
            return self._get_fail_retstr("order_type:" + params["order_type"] + " is not supported")

        # quantity
        quantity = params["amount"]

        try:
            def make_price_str(price_inst):
                if isinstance(price_inst, str):
                    price = price_inst
                else:
                    price='%.8f' % (price_inst)
                return price

            price = None
            if is_limit_order:
                price = make_price_str(params['rate'])

            # place an order
            if is_test_mode == False:
                # make valid order

                if price is not None:
                    ret = client.create_order(
                        symbol=symbol,
                        side=side,
                        timeInForce="GTC",
                        type=Client.ORDER_TYPE_LIMIT if is_limit_order else Client.ORDER_TYPE_MARKET,
                        quantity=quantity,
                        price=price
                    )
                else:
                    ret = client.create_order(
                        symbol=symbol,
                        side=side,
                        timeInForce="GTC",
                        type=Client.ORDER_TYPE_LIMIT if is_limit_order else Client.ORDER_TYPE_MARKET,
                        quantity=quantity,
                    )
            else:
                # make test order
                if price is not None:
                    ret = client.create_test_order(
                        symbol=symbol,
                        side=side,
                        type=Client.ORDER_TYPE_LIMIT if is_limit_order else Client.ORDER_TYPE_MARKET,
                        quantity=quantity,
                        price=price
                    )
                else:
                    ret = client.create_test_order(
                        symbol=symbol,
                        side=side,
                        type=Client.ORDER_TYPE_LIMIT if is_limit_order else Client.ORDER_TYPE_MARKET,
                        quantity=quantity,
                    )

        except BinanceAPIException as e:
            return self._get_fail_retstr(str(e.status_code) + ":" + str(e.message))

        if not self._check_success(ret):
            return self._process_ret(ret)

        new_ret = {}
        new_ret["success"] = True
        new_ret["pair"] = self.symbol_to_pair(ret["symbol"])
        new_ret["id"] = ret["orderId"]
        new_ret["rate"] = ret["price"]
        new_ret["order_type"] = ret["side"].lower()
        new_ret["order_type_detail"] = ret["type"]
        new_ret["amount"] = ret["origQty"]
        new_ret["order_status"] = ret["status"]
        new_ret["clientOrderId"] = ret["clientOrderId"]
        #created_at = datetime.fromtimestamp(ret["transactTime"], tz=pytz.utc)
        new_ret["created_at"] = self._gtctime_to_createdat_str(ret["transactTime"]/1000)
        
        """
        ret example
        {
        "symbol": "BTCUSDT",
        "orderId": 28,
        "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
        "transactTime": 1507725176595,
        "price": "0.00000000",
        "origQty": "10.00000000",
        "executedQty": "10.00000000",
        "status": "FILLED",
        "timeInForce": "GTC",
        "type": "MARKET",
        "side": "SELL"
        }
        """

        return json.dumps(new_ret)

    def cancel(self, params = {}):
        defaults = {
            'id': ""
        }
        defaults.update(params)
        params = defaults.copy()
        params["orderId"] = params["id"]
        del params["id"]
        if "pair" in params:
            params["symbol"] = self.pair_to_symbol(params["pair"])

        try:
            ret = self.client.cancel_order(symbol=params["symbol"], orderId=params["orderId"])
        except BinanceAPIException as e:
            return self._get_except_retstr(e)

        if not self._check_success(ret):
            return self._process_ret(ret)

        ret["success"] = True
        ret["id"] = ret["orderId"]
        return self._process_ret(ret)

    def _create_symbol_list_from_param(self, params):
        symbols = []
        if "pair" not in params and "symbol" not in params:
            return False, self._get_fail_retstr("Set 'symbol' or 'pair' when accessing binance api")

        if "pair" in params:
            if isinstance(params["pair"], list):
                symbols = list(map(lambda x:self.to_symbol(x), params["pair"]))
            else:
                symbols = [params["pair"]]
        else:
            if isinstance(params["symbol"], list):
                symbols = params["symbol"]
            else:
                symbols = [params["symbol"]]

        return True, symbols

    def opens(self, params = {}):
        ok, symbols = self._create_symbol_list_from_param(params)
        if not ok:
            return symbols

        new_ret = {"success":True}
        all_orders = []
        
        force_all_order_request = "__force_all_order__" in params and params["__force_all_order__"]

        for symbol in symbols:
            try:
                if force_all_order_request:
                    print("****** get all orders (not only opens) ******")
                    ret = self.client.get_all_orders(symbol=symbol)
                else:
                    ret = self.client.get_open_orders(symbol=symbol)
            except BinanceAPIException as e:
                return self._get_except_retstr(e)

            if not self._check_success(ret):
                return self._process_ret(ret)
        

            orders = []
            for open_order in ret:
                new_order = {}
                new_order["symbol"] = open_order["symbol"]
                new_order["pair"] = self.symbol_to_pair(open_order["symbol"])
                new_order["id"] = open_order["orderId"]
                new_order["rate"] = open_order["price"]
                new_order["orig_amount"] = float(open_order["origQty"])
                new_order["pending_amount"] = float(open_order["origQty"]) - float(open_order["executedQty"])
                new_order["order_type"] = open_order["side"].lower()
                new_order["created_at"] = self._gtctime_to_createdat_str(open_order["time"]/1000)
                new_order["stop_loss_rate"] = None if float(open_order["stopPrice"]) == 0 else open_order["stopPrice"]
                new_order["pending_market_buy_amount"] = None
                new_order["status"] = open_order["status"]

                orders.append(new_order)

            all_orders += orders

        new_ret["orders"] = list(sorted(all_orders, key=lambda x:x["created_at"], reverse=True))

        return json.dumps(new_ret)

        # result sample
        """
[
  {
    "symbol": "LTCBTC",
    "orderId": 1,
    "clientOrderId": "myOrder1",
    "price": "0.1",
    "origQty": "1.0",
    "executedQty": "0.0",
    "status": "NEW",
    "timeInForce": "GTC",
    "type": "LIMIT",
    "side": "BUY",
    "stopPrice": "0.0",
    "icebergQty": "0.0",
    "time": 1499827319559,
    "isWorking": trueO
  }
]
        """

    def transactions(self, params = {}):
        ok, symbols = self._create_symbol_list_from_param(params)
        if not ok:
            return symbols

        new_ret = {"success": True}
        all_trades = []

        for symbol in symbols:
            try:
                ret = self.client.get_my_trades(symbol=symbol)
            except BinanceAPIException as e:
                return self._get_except_retstr(e)
       
            pair_name = self.symbol_to_pair(symbol)
            qty_currency = pair_name.split("_")[0]
            base_currency = pair_name.split("_")[1]

            # change ret to cc style
            trades = []
            for t in ret:
                """
                #"id": 38,
                #"order_id": 49,
                #"created_at": "2015-11-18T07:02:21.000Z",
                #"funds": {
                #    "btc": "0.1",
                #    "jpy": "-4096.135"
                #},
                #"pair": "btc_jpy",
                #"rate": "40900.0",
                #"fee_currency": "JPY",
                #"fee": "6.135",
                #"liquidity": "T",
                #"side": "buy"
                """
                trade = {}
                trade["id"] = t["id"]
                trade["pair"] = pair_name
                trade["order_id"] = t["orderId"]
                trade["rate"] = t["price"]
                trade["created_at"] = self._gtctime_to_createdat_str(t["time"]/1000)
                trade["fee_currency"] = t["commissionAsset"]
                trade["fee"] = t["commission"]
                trade["liquidity"] = "M" if t["isMaker"] else "T"
                trade["side"] = "buy" if t["isBuyer"] == True else "sell"

                funds = {}
                if t["isBuyer"] == True:
                    funds[qty_currency]  = float(t["qty"])
                    funds[base_currency] = - float(t["qty"]) * float(t["price"])
                else:
                    funds[qty_currency]  = - float(t["qty"])
                    funds[base_currency] = float(t["qty"]) * float(t["price"])

                if t["commissionAsset"].lower() == qty_currency.lower():
                    # minus commission from qty currency
                    funds[qty_currency] -= float(t["commission"])
                elif t["commissionAsset"].lower() == base_currency.lower():
                    # minus commission from base currency
                    # 取引している通貨とは別の通貨から惹かれる場合もあるので、両方チェック（BNB等）
                    funds[base_currency] -= float(t["commission"])

                trade["funds"] = funds

                trades.append(trade)

            all_trades += trades

        new_ret["transactions"] = list(sorted(all_trades, key=lambda x:x["created_at"], reverse=True))

        return json.dumps(new_ret)
        

        # Check an order's status. でもいい？
        # /api/v3/myTrades は weightが5で利用weightがきつい。1symbolに対して5使ってしまう
        # だから、PositionManager側でparseするより、api側で状態を取得して返すようにするほうがいい？？
        # => PositionMnaagerに買いていたものを、cc api, binance api に移す感じ

        # 追記: 現状のママでよさそう
        # 1分毎に行う処理
        # new order: weight 1 * positions
        # cancel order: weight 1 * positions
        #
        # 毎フレーム行う処理
        # balance の確認: weight 5
        # openOrder の確認: weight 1 * positions
        # transactions の確認: weight 5 * positions
        # => 1分間に10回処理をする場合 & 6通貨同時進行
        # 2*6 + (6+6*6)*10 = 432/min < 1200/min
        # => 問題なさそう
        # day limit は order のみなので、balance 等のrequestは別？


if __name__ == "__main__":
    import os
    import sys
    print(sys.path)

    from binance_api.binance_api import Binance

    api_key = None
    secret_key = None
    with open(os.path.join(os.path.dirname(__file__), "key/test_binance_key.txt")) as r:
        api_key = r.readline().strip()
        secret_key = r.readline().strip()

    api = Binance(api_key, secret_key)

    trades_str = api.order.transactions({"symbol": ["BTCUSDT", "LSKBTC"]})
    trades = json.loads(trades_str)
    print("transactions")
    for trade in trades["transactions"]:
        print("=====")
        for key in sorted(trade.keys()):
            print(key + ":" + str(trade[key]))

    print("--------all orders---------")
    orders_str = api.order.opens({"symbol":["BTCUSDT", "LSKBTC", "OMGBTC"], "__force_all_order__": True})
    orders = json.loads(orders_str)
    for order in orders["orders"]:
        print("=====")
        for key in sorted(order.keys()):
            print(key + ":" + str(order[key]))
