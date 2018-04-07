# coding: utf-8
import os
import sys
import time
import json
import signal

from api.WebsocketStreamBase import WebsocketStreamBase
from ChartBars import Chart
from Util import TimeUtil

class ChartUpdaterByCoincheckWS(WebsocketStreamBase):
    def __init__(self,
                 chart_span_minutes,
                 technical_calculator = None,
                 callback_on_update = None,
                 run_immediately = True):
        url = "wss://ws-api.coincheck.com/"
        super(ChartUpdaterByCoincheckWS, self).__init__(url, run_immediately)

        self.chart = Chart(span_minutes=chart_span_minutes,
                           technical_calculator=technical_calculator)
        self.last_received_id = 0
        self.callback_on_update = callback_on_update

    def set_callback_on_update(self, callback):
        self.callback_on_update = callback

    def start_btc_jpy_subscribe(self):
        self.request({"type": "subscribe",
                      "channel": "btc_jpy-trades"})

    def _start_subscribe_after_connect(self):
        self.start_btc_jpy_subscribe()

    def on_message(self, ws, msg):
        now = TimeUtil.now_timestamp_utc()

        received_data = json.loads(msg)
        #print("msg:"+str(msg))

        if not isinstance(received_data, list):
            print("error: recieved data is not array: " + str(msg))
            return

        if len(received_data) < 5:
            print("error: recieved array length is less than 5: " + str(received_data))
            return

        msg_id = received_data[0]
        pair = received_data[1]
        price = float(received_data[2])
        amount = float(received_data[3])
        trade_type = received_data[4]

        update_only_high_or_low = False
        if self.last_received_id is not None and msg_id < self.last_received_id:
            # this is not clever solution!!!
            #  because old message possibly update (high&low)
            #  but I ignore it. my algorithm cannot handle high & low value
            #print("old message recieved (latest:%d, received:%d)" % (self.last_received_id, msg_id,))
            update_only_high_or_low = True
            return

        if pair != "btc_jpy":
            print("received data is not btc_jpy data: " + str(pair))
            return

        self.last_received_id = max(msg_id, self.last_received_id)

        # update chart     
        self.chart.add_new_data(now, price, update_only_high_or_low)

        # callback after update
        if self.callback_on_update is not None:
            self.callback_on_update(0)

    def get_chart(self, symbol = "btc_jpy"):
        return self.chart

if __name__ == "__main__":

    updater_and_runner = ChartUpdaterByCoincheckWS(5)
    while updater_and_runner.is_started is False:
        time.sleep(0.1)

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
        
    updater_and_runner.set_callback_on_update(show_bar)
    updater_and_runner.start_btc_jpy_subscribe()

    a = raw_input()
    updater_and_runner.stop()

    time.sleep(2)
