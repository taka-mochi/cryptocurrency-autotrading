# coding: utf-8

import time
import math
from ChartBars import Chart
from Util import TimeUtil

class PriceDecider_CloseFixedRateAndTime_base(object):
    def __init__(self,
                 close_div_rate_from_buy_value,
                 close_bar_count_to_hold):
        self.close_div_rate_from_open_value = close_div_rate_from_buy_value
        self.close_bar_count_to_hold = close_bar_count_to_hold

        print("close_div_rate", self.close_div_rate_from_open_value)
        print("sell_bar_count", self.close_bar_count_to_hold)

    def decide_make_position_order(self, chart):
        raise NotImplementedError()

    # decide whether to sell or not by holding time span
    def market_sell_decide_algorithm(self, chart, open_rate, created_time, current_time):
        created_timestamp = TimeUtil.timestamp_utc(created_time)
        current_timestamp = TimeUtil.timestamp_utc(current_time)
        created_index = chart.convert_unixtime_to_bar_indexlike_value(created_timestamp)
        current_index = chart.convert_unixtime_to_bar_indexlike_value(current_timestamp)

        if current_index - created_index >= self.close_bar_count_to_hold:
            return True

        return False

    # decide the price to sell
    def sell_price_decide_algorithm(self, open_rate):
        return open_rate * (1+self.close_div_rate_from_open_value)

