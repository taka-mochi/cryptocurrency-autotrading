# coding: utf-8

import time
import math
from ChartBars import Chart
from Util import TimeUtil
from Algorithm_PriceDecider_CloseFixedRateAndTime_base import PriceDecider_CloseFixedRateAndTime_base

class PriceDeciderByHighestOrLowest(PriceDecider_CloseFixedRateAndTime_base):
    def __init__(self,
                 use_bar_count,
                 open_div_rate,
                 close_div_rate_from_buy_value,
                 close_bar_count_to_hold):
        super(PriceDeciderByHighestOrLowest, self).__init__(close_div_rate_from_buy_value, close_bar_count_to_hold)
        self.use_bar_count = use_bar_count
        self.open_div_rate = open_div_rate
        self.use_high = open_div_rate < 0
        self.compare_func = max if self.open_div_rate < 0 else min

        print("parameter of %s" % str(self))
        print("bar_count", self.use_bar_count)
        print("open_div_rate", self.open_div_rate)
        #print("close_div_rate", self.close_div_rate_from_open_value)
        #print("close_bar_count", self.close_bar_count_to_hold)

    def decide_make_position_order(self, chart):
        assert ("ChartBars.Chart" in str(type(chart)))
        #assert (isinstance(chart, Chart))

        # amount is not decided by this method!!
        position_type = None
        position_price = None

        last_bar = chart.get_bar_from_last()
        prev_bar = chart.get_bar_from_last(1)

        get_value_func = lambda bar: bar.high if self.use_high else bar.low
        #VALUE_IDX = chart.get_column_idx(self.use_key)

        if last_bar is None or prev_bar is None:
            # no bar
            return (None, position_price)
    
        start_index = 0 if last_bar.is_freezed() else 1
        cur_value = -1
        for i in range(self.use_bar_count):
            bar = chart.get_bar_from_last(start_index+i)
            if bar is None:
                return (None, None)

            if cur_value < 0:
                cur_value = get_value_func(bar)
            else:
                cur_value = self.compare_func(cur_value, get_value_func(bar))
            
        position_type = "long" if self.open_div_rate < 0 else "short"
        target_value = cur_value * (1+self.open_div_rate)
    
        return (position_type, target_value)

    # decide whether to sell or not by holding time span
    """
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
        return int(math.floor(open_rate * (1+self.close_div_rate_from_open_value)))
    """

