# -*- coding: utf-8 -*-

import time
import sys
import os
from datetime import datetime
from datetime import timedelta
#from datetime import pytz
import dateutil.parser
import urllib.request
import json
import argparse
import subprocess

def date_to_str(date):
    return date.strftime("%Y-%m-%d_%H-%M-%S")

def unix_to_str(unixtime):
    return date_to_str(datetime.fromtimestamp(int(unixtime)))

def save_to_file(data_list, save_dir, market_name):
    sorted_data = list(sorted(data_list, key=lambda x:int(x[0])))

    start_unixdate = sorted_data[0][0]/1000
    end_unixdate = sorted_data[-1][0]/1000

    start = datetime.fromtimestamp(start_unixdate)
    end = datetime.fromtimestamp(end_unixdate)

    save_fname = os.path.join(save_dir, "binance_%s_1min_%s-%s.csv" % (market_name, date_to_str(start), date_to_str(end),))
    with open(save_fname, "w") as fw:
        for data in sorted_data:
            # open,close,low,high,baseamount,quoteamount
            fw.write("%s,%s,%s,%s,%s,%s,%s\n" % (unix_to_str(data[0]/1000), data[1], data[4], data[3], data[2], data[5], data[7],))

    print("saved_to:" + save_fname)

def download_eternal(start_unixtime, stop_unixtime, market, use_wget = False, wget_proxy = None):
    results = []
    prev_oldest_date = None
    while True:
        baseurl = "https://api.binance.com/api/v1/klines?symbol=%s&interval=1m" % (market,)
        targeturl = baseurl
        if start_unixtime is not None:
            targeturl = baseurl + ("&endTime=%d" % (start_unixtime*1000))

        if use_wget:
            if wget_proxy is not None:
                tmp_file = "___tmp_save"
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
                ret_str = subprocess.check_output('wget -e HTTPS_PROXY=%s --no-check-certificate "%s" -O %s' % (wget_proxy,targeturl,tmp_file,), shell=True)
                with open(tmp_file) as fr:
                    ret_str = fr.read()
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
            else:
                ret_str = subprocess.check_output('wget "%s" -O -' % (targeturl,), shell=True)
            ret =json.loads(ret_str)
        else:
            f = urllib.request.urlopen(targeturl)
            s = f.read().decode('utf-8')
            ret = json.loads(s)

        if len(ret) > 0:
            oldest_date = ret[0][0]/1000
            print(oldest_date, datetime.fromtimestamp(int(oldest_date)))

            if stop_unixtime > oldest_date or prev_oldest_date == oldest_date:
                ok_results = filter(lambda x:x[0]/1000 >= stop_unixtime, ret)
                results += ok_results
                break

            results += ret

            start_unixtime = ret[0][0]/1000
            prev_oldest_date = oldest_date

            time.sleep(0.02)
        else:
            time.sleep(10)

    save_to_file(results, "bar_data", market)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download bf FX')

    parser.add_argument('--start_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d_%H-%M-%S'), default=None)
    parser.add_argument('--stop_date', type=lambda s: datetime.strptime(s, '%Y-%m-%d_%H-%M-%S'), default=None)
    parser.add_argument('--use_wget', default=False, action='store_true')
    parser.add_argument('--wget_https_proxy', default=None, type=str)
    parser.add_argument('--market', default="ETHBTC")

    args = parser.parse_args()

    print("start_date", args.start_date)
    print("stop_date", args.stop_date)

    if args.start_date is not None:
        args.start_date = time.mktime(args.start_date.timetuple())
    if args.stop_date is not None:
        args.stop_date = time.mktime(args.stop_date.timetuple())

    download_eternal(args.start_date, args.stop_date, args.market, use_wget=args.use_wget, wget_proxy=args.wget_https_proxy)
