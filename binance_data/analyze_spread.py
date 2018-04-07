# -*- coding: utf-8 -*-

import time
import sys
import os
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import argparse
import json
import numpy as np

def calc_move_average_price_of_btc_acc(price_and_amount_ordered, target_acc_btc):
    acc_btc = 0
    total_amount = 0
    for v in price_and_amount_ordered:
        price = float(v[0])
        amount = float(v[1])
        btc_amount = price * amount
        if acc_btc + btc_amount >= target_acc_btc:
            remain_btc_amount = target_acc_btc - acc_btc
            acc_btc = target_acc_btc
            total_amount += remain_btc_amount / price
            break

        acc_btc += btc_amount
        total_amount += amount

    return acc_btc / total_amount

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze spread')

    parser.add_argument('--input_file', required=True)
    parser.add_argument('--accumulate_btc', default=1.0, type=float)

    args = parser.parse_args()

    bid_ask_avgs = []

    for line in open(args.input_file):
        line = line.strip()
        if line == "": continue

        # {"lastUpdateId":35755367,"bids":[["0.15087900","6.15500000",[]],["0.15087800","1.32200000",[]],["0.15052100","0.05000000",[]],["0.15050200","0.21600000",[]],["0.15033700","0.46800000",[]],["0.15028600","0.58200000",[]],["0.15028000","1.11300000",[]],["0.15021800","0.50000000",[]],["0.15021300","0.27600000",[]],["0.15020000","0.20000000",[]]],"asks":[["0.15088000","0.00100000",[]],["0.15088200","9.95700000",[]],["0.15120600","0.04900000",[]],["0.15127400","0.05000000",[]],["0.15136300","0.12000000",[]],["0.15137100","0.12000000",[]],["0.15137200","0.01500000",[]],["0.15138200","0.31000000",[]],["0.15150000","0.00700000",[]],["0.15158900","2.71700000",[]]]}
        depth = json.loads(line)
        bids = list(sorted(depth["bids"], key=lambda x:-float(x[0]))) # 買い注文
        asks = list(sorted(depth["asks"], key=lambda x:float(x[0]))) # 売り注文

        bid_average_value = calc_move_average_price_of_btc_acc(bids, args.accumulate_btc)
        ask_average_value = calc_move_average_price_of_btc_acc(asks, args.accumulate_btc)

        bid_ask_avgs.append((bid_average_value, ask_average_value))


    # spread rate
    spread_rates = list(map(lambda x:(x[1]-x[0])/x[0], bid_ask_avgs))
    count = len(spread_rates)
    spread_average = np.average(spread_rates)*100
    spread_stdev = np.std(spread_rates)*100

    print("data count = %d" % (count,))
    print("spread average = %f%%" % (spread_average))
    print("spread stdev = %f%%" % (spread_stdev))
    print("95%% range: %f%% - %f%% - %f%%" % ((spread_average-2*spread_stdev), spread_average, (spread_average+2*spread_stdev),))
