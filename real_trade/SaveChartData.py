# -*- coding: utf-8 -*-

import time
import sys
import os
import argparse
import json
import signal

from datetime import datetime
from datetime import timedelta

from ChartUpdaterByCCWebsocket import ChartUpdaterByCoincheckWS
from Util import TimeUtil

class ChartSaveByCoincheckWS(ChartUpdaterByCoincheckWS):
    def __init__(self,
                 save_file_path,
                 save_span_sec,
                 max_save_minutes=140):

        super(ChartSaveByCoincheckWS, self).__init__(
            chart_span_minutes=1,
            callback_on_update=self.on_message_callback,
            run_immediately=True,
        )

        while self.is_started is False:
            time.sleep(0.1)
        self.start_btc_jpy_subscribe()


        self.last_saved_time = None
        self.save_file_path = save_file_path
        self.save_span_sec  = save_span_sec
        self.max_save_minutes = max_save_minutes

    def on_message_callback(self):
        now = TimeUtil.now_utc()

        to_save = self.last_saved_time is None or (now - self.last_saved_time).total_seconds() >= self.save_span_sec

        if not to_save:
            return

        print("save", now)

        save_oldest_time = now - timedelta(seconds=self.max_save_minutes*60)
        with self.chart.bars_lock_obj:
            while len(self.chart.bars_w_starttime) > 0:
                starttime = TimeUtil.fromutctimestamp(self.chart.bars_w_starttime[0][0])
                if starttime < save_oldest_time:
                    del self.chart.bars_w_starttime[0]
                else:
                    break

            with open(self.save_file_path, "w") as fw:
                for timestamp, bar in self.chart.bars_w_starttime:
                    date = TimeUtil.fromutctimestamp(timestamp)

                    begin = bar.begin
                    end   = bar.end
                    high  = bar.high
                    low   = bar.low

                    fw.write("%s,%f,%f,%f,%f\n" % (str(date),begin,end,low,high,))

        self.last_saved_time = now

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Save Data from CC')
    parser.add_argument('--save_file_path', required=True,
                        help='Save file path')
    
    args = parser.parse_args()
    print(args)

    checker = ChartSaveByCoincheckWS(
        save_file_path=args.save_file_path,
        save_span_sec=30,
    )

    def stop(a,b):
        checker.set_reconnect_and_resubscribe_when_closed(False)
        checker.stop()
        sys.exit(-1)

    try:
        signal.signal(signal.SIGINT, stop)
    except:
        pass

    # update position manager loop!!!
    while True:
        time.sleep(15)  # 
