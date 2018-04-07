# coding: utf-8
import os
import sys
import time
import json
import signal

from ChartBars import Chart
from Util import TimeUtil

#from binance.websockets import BinanceSocketManager
from api.WebsocketStreamBase import WebsocketStreamBase

class ChartUpdaterByBinanceWS(WebsocketStreamBase):
    def __init__(self,
                 binance_api_client,
                 chart_span_minutes,
                 pairs_or_symbols,
                 run_immediately = True,
                 technical_calculator = None,
                 callback_on_update = None):
        super(ChartUpdaterByBinanceWS, self).__init__(None, False)
        
        SUPPORTED_SPAN_MINUTES = [
            1,3,5,15,30,60,120,240
        ]
        if int(chart_span_minutes) not in SUPPORTED_SPAN_MINUTES:
            raise Exception("Binance Websocket does not support chart span: %dm" % (int(chart_span_minutes),))

        self.chart_span_minutes = int(chart_span_minutes)
        self.callback_on_update = callback_on_update

        self.target_symbols = list(map(lambda x:self._to_symbol(x), pairs_or_symbols))
        self.symbol_to_idxlist = {}
        self.symbol_to_chart = {}

        # make charts for each symbol
        for i, symbol in enumerate(self.target_symbols):
            if symbol not in self.symbol_to_idxlist:
                self.symbol_to_idxlist[symbol] = []
            self.symbol_to_idxlist[symbol].append(i)

            if symbol not in self.symbol_to_chart:
                chart = Chart(span_minutes=chart_span_minutes,
                              technical_calculator=technical_calculator)
                self.symbol_to_chart[symbol] = chart

        # make stream url
        url_base = "wss://stream.binance.com:9443"

        symbols = self.symbol_to_idxlist.keys()
        stream_name = self.__make_streamname(symbols, chart_span_minutes)
        url = url_base + "/stream?streams=" + stream_name

        self.set_url(url)

        # run
        if run_immediately:
            self.run_on_another_thread()

    @staticmethod
    def __make_streamname(symbols, minutes):
        stream_names = []
        for symbol in symbols:
            s = ChartUpdaterByBinanceWS._to_symbol(symbol)
            stream_names.append(s + "@kline_" + str(minutes) + "m")

        return "/".join(stream_names)

    @staticmethod
    def _to_symbol(pair_or_symbol):
        return pair_or_symbol.replace("_", "").lower()

    # def _start(self):
    #     # => Managerに任せてもうまく動かん。自前のWebsocket実装のほうが多分いい
    #     # https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md
    #     #TO FIX
    #     unique_symbols = list(set(self.target_symbols))
    #     stream_names = list(map(lambda x:"%s@kline_%dm" % (x,self.chart_span_minutes) , unique_symbols))
    #     print("stream_names: " + str(stream_names))
    #     self.conn_key = self.bw_manager.start_multiplex_socket(stream_names, lambda x:self.on_message(x))
    #     print("conn_key: " + str(self.conn_key))

    def set_callback_on_update(self, callback):
        self.callback_on_update = callback

    # callback after connect
    def _start_subscribe_after_connect(self):
        # do nothing
        pass

    def on_message(self, ws, msg):
        try:
            msg = json.loads(msg)
        except Exception as e:
            print(str(e))
            return
        

        stream_name = msg["stream"]
        raw_data = msg["data"]

        if "kline" not in stream_name:
            print("bnws error: not supported ws message is received: %s:%s" % (stream_name, str(raw_data)))
            return

        if raw_data["e"] == "e":
            # some error occurred
            print("bnws error from API: " + str(raw_data))
            return
        
        symbol = stream_name.split("@")[0]
        if symbol not in self.symbol_to_idxlist:
            print("bnws: no callback for %s" % (symbol))
            return

        main_data = raw_data["k"]
        start_time = int(main_data["t"])//1000
        begin = float(main_data["o"])
        end   = float(main_data["c"])
        high  = float(main_data["h"])
        low   = float(main_data["l"])
        

        chart = self.symbol_to_chart[symbol]
        chart.add_new_value_by_kline_data(start_time, begin=begin, end=end, high=high, low=low)

        # callback after update
        if self.callback_on_update is not None:
            self.callback_on_update(symbol)

    def get_chart(self, symbol_or_pair):
        symbol = self._to_symbol(symbol_or_pair)
        if symbol not in self.symbol_to_chart: return None
        return self.symbol_to_chart[symbol]

if __name__ == "__main__":
    from api.binance_api.binance_api import Binance

    api_key = None
    secret_key = None
    with open(os.path.join(os.path.dirname(__file__), "api/binance_api/key/test_binance_key.txt")) as r:
        api_key = r.readline().strip()
        secret_key = r.readline().strip()

    b = Binance(api_key, secret_key)
    binance_api_client = b.client
    chart_span_minutes = 1
    pairs_or_symbols = ["btc_usdt", "eth_btc", "neo_btc"]
    
    updater_and_runner = ChartUpdaterByBinanceWS(
        binance_api_client = binance_api_client,
        chart_span_minutes = chart_span_minutes,
        pairs_or_symbols = pairs_or_symbols
    )
    def callback(symbol):
        chart = updater_and_runner.get_chart(symbol)
        timestamp, last_bar = chart.get_bar_from_last(with_timestamp=True)
        print(symbol, timestamp, last_bar.begin, last_bar.end, last_bar.high, last_bar.low, last_bar.is_freezed())
        
    updater_and_runner.set_callback_on_update(callback)

    def stop(a,b):
        updater_and_runner.stop()
        sys.exit(-1)

    signal.signal(signal.SIGQUIT, stop)
    signal.signal(signal.SIGHUP, stop)
    #signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    def show_bar():
        chart = updater_and_runner.get_chart()
        last_bar_set = chart.bars_w_starttime[-1]
        last_time = last_bar_set[0]
        last_bar = last_bar_set[1]

        print("%s: (b,e,h,l) = (%f,%f,%f,%f)" % (
            TimeUtil.fromutctimestamp(float(last_time)),
            last_bar.begin, last_bar.end, last_bar.high, last_bar.low))
        
    #updater_and_runner.set_callback_on_update(show_bar)

    if sys.version_info[0] <= 2:
        a = raw_input()
    else:
        a = input()
    updater_and_runner.stop()

    time.sleep(2)
