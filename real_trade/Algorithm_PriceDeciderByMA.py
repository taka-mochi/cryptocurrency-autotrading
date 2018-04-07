# coding: utf-8

import time
import math
from ChartBars import Chart
from Util import TimeUtil
from Algorithm_PriceDecider_CloseFixedRateAndTime_base import PriceDecider_CloseFixedRateAndTime_base

class PriceDeciderByMA(PriceDecider_CloseFixedRateAndTime_base):
    def __init__(self,
                 use_ma_count,
                 buy_ma_div_rate,
                 sell_div_rate_from_buy_value,
                 sell_bar_count_to_hold):
        super(PriceDeciderByMA, self).__init__(sell_div_rate_from_buy_value, sell_bar_count_to_hold)
        self.use_ma_count = use_ma_count
        self.open_ma_div_rate = buy_ma_div_rate
        self.use_ma_key = str(use_ma_count) + "ma_end"

        print("parameter of %s", str(self))
        print("ma_count", self.use_ma_count)
        print("open_div_rate", self.open_ma_div_rate)

    def decide_make_position_order(self, chart):
        assert ("ChartBars.Chart" in str(type(chart)))
        #assert (isinstance(chart, Chart))

        # amount is not decided by this method!!
        position_type = None
        position_price = None

        last_bar = chart.get_bar_from_last()
        prev_bar = chart.get_bar_from_last(1)

        if last_bar is None or prev_bar is None:
            # no bar
            return (None, position_price)

        use_bar = last_bar if last_bar.is_freezed() else prev_bar
        if use_bar.technical_values is None or\
           self.use_ma_key not in use_bar.technical_values:
            # no technical values
            return (None, position_price)
            
        ma_value = use_bar.technical_values[self.use_ma_key]
        if ma_value is None:
            return (position_type, position_price)

        position_type = "long" if self.open_ma_div_rate < 0 else "short"
        target_value = ma_value * (1+self.open_ma_div_rate)
    
        return (position_type, target_value)

    # decide whether to sell or not by holding time span
    """
    def market_sell_decide_algorithm(self, chart, open_rate, created_time, current_time):
        created_timestamp = TimeUtil.timestamp_utc(created_time)
        current_timestamp = TimeUtil.timestamp_utc(current_time)
        created_index = chart.convert_unixtime_to_bar_indexlike_value(created_timestamp)
        current_index = chart.convert_unixtime_to_bar_indexlike_value(current_timestamp)

        if current_index - created_index >= self.sell_bar_count_to_hold:
            return True

        return False

    # decide the price to sell
    def sell_price_decide_algorithm(self, open_rate):
        return int(math.floor(open_rate * (1+self.close_div_rate_from_open_value)))
    """
