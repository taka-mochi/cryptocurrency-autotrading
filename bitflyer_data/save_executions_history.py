# -*- coding: utf-8 -*-

import pybitflyer
import time
import sys
import os
from datetime import datetime
from datetime import timedelta
#from datetime import pytz
import dateutil.parser
import argparse

def make_unixtime(datestr, offset_minutes = 60*9):
    d = dateutil.parser.parse(datestr) + timedelta(minutes=offset_minutes)
    return time.mktime(d.timetuple())

def save_to_file(data_list, save_dir):
    sorted_data = list(sorted(data_list, key=lambda x:int(x["id"])))

    start_date = sorted_data[0]["exec_date"]
    end_date = sorted_data[-1]["exec_date"]

    start_date = dateutil.parser.parse(start_date)
    end_date   = dateutil.parser.parse(end_date)

    start_unixdate = time.mktime(start_date.timetuple())
    end_unixdate   = time.mktime(end_date.timetuple())

    save_fname = os.path.join(save_dir, "bitflyerfx_%010d-%010d.csv" % (start_unixdate, end_unixdate,))
    with open(save_fname, "w") as fw:
        for data in sorted_data:
            unixtime = int(make_unixtime(data["exec_date"]))
            fw.write("%d,%s,%s\n" % (unixtime, str(data["price"]), str(data["size"]),))

    print("saved_to:" + save_fname)

def download_eternal(api, start_id, stop_date, market):
    before_id = start_id
    results = []
    while True:
        if before_id is not None:
            ret = api.executions(before=before_id, product_code=market, count=5000)
        else:
            ret = api.executions(product_code=market)
            
        if len(ret) > 0:
            before_id = int(ret[-1]["id"])+1
            oldest_date = dateutil.parser.parse(ret[-1]["exec_date"]) + timedelta(minutes=60*9)
            print(before_id, oldest_date, ret[-1]["price"], ret[-1]["size"])

            if stop_date > oldest_date:
                ok_results = filter(lambda x:dateutil.parser.parse(x["exec_date"]) + timedelta(minutes=60*9) >= stop_date, ret)
                results += ok_results
                break

            results += ret

            save_length = 20000
            if len(results) >= save_length:
                save_to_file(results[:save_length], "raw_data")
                results = results[save_length:]
        
            time.sleep(0.02)
        else:
            time.sleep(10)

    save_to_file(results, "raw_data")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download bf FX')

    parser.add_argument('--start_id', type=int, default=None)
    parser.add_argument('--stop_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d_%H-%M-%S'), default=None)

    args = parser.parse_args()

    print("start_id", args.start_id)
    print("stop_date", args.stop_date)

    download_eternal(pybitflyer.API(), args.start_id, args.stop_date, "FX_BTC_JPY")
