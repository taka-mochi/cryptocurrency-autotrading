# coding: utf-8

import time
import math
from ChartBars import Chart
from Util import TimeUtil
from Algorithm_PriceDecider_CloseFixedRateAndTime_base import PriceDecider_CloseFixedRateAndTime_base

class PriceDeciderByContinuousPositiveLine(PriceDecider_CloseFixedRateAndTime_base):
    def __init__(self,
                 cont_positive_line_count,
                 buy_order_up_rate,
                 close_div_rate_from_buy_value,
                 stop_loss_rate,
                 close_bar_count_to_hold,
                 do_filter_by_ma_slope,
                 filter_ma_count=0,
                 filter_ma_bar_span=0,
                 losscut_rate=None,
                 make_order_only_first_time_bar=True):
        super(PriceDeciderByContinuousPositiveLine, self).__init__(close_div_rate_from_buy_value, close_bar_count_to_hold)

        self.buy_order_up_rate = buy_order_up_rate
        self.cont_positive_line_count = cont_positive_line_count
        self.stop_loss_rate = stop_loss_rate
        self.do_filter_by_ma_slope = do_filter_by_ma_slope
        self.filter_ma_count = filter_ma_count
        self.filter_ma_bar_span = filter_ma_bar_span
        self.filter_ma_keyname = str(filter_ma_count) + "ma_end"
        self.losscut_rate = losscut_rate
        self.make_order_only_first_time_bar = make_order_only_first_time_bar
        
        self.last_checked_bar_timestamp = None

        print("parameter of %s" % str(self))
        print("cont_positive_line_count", self.cont_positive_line_count)
        print("buy_order_up_rate", self.buy_order_up_rate)
        print("stop_loss_rate", self.stop_loss_rate)
        print("do_filter_by_ma_slope", self.do_filter_by_ma_slope)
        print("self.filter_ma_count", self.filter_ma_count)
        print("filter_ma_bar_span", self.filter_ma_bar_span)
        print("losscut_rate", self.losscut_rate)

    def decide_make_position_order(self, chart):
        assert ("ChartBars.Chart" in str(type(chart)))
        #assert (isinstance(chart, Chart))

        # amount is not decided by this method!!
        position_type = None
        position_price = None
        stoploss_rate = None

        last_timestamp, last_bar = chart.get_bar_from_last(with_timestamp=True)
        prev_timestamp, prev_bar = chart.get_bar_from_last(1, with_timestamp=True)
        
        if last_bar is None or prev_bar is None:
            # no bar
            return (None, position_price)
            
        start_index = 0 if last_bar.is_freezed() else 1
        use_bar = last_bar if last_bar.is_freezed() else prev_bar
        use_timestamp = last_timestamp if last_bar.is_freezed() else prev_timestamp
        
        # if bar is not changed from last time, this alg will not make any order
        if self.make_order_only_first_time_bar and self.last_checked_bar_timestamp == use_timestamp:
            print("rejected because this bar is not first time bar")
            return (None, None)
    
        self.last_checked_bar_timestamp = use_timestamp
        
        # filter by ma direction
        if self.do_filter_by_ma_slope:
            if not self.check_filter_by_ma_dir(chart=chart,
                                               cur_bar=use_bar,
                                               cur_bar_index_from_last=start_index):
                print("rejected by ma slope filter")
                return (None, None)
        
        # filter by positive line continuous
        for i in range(self.cont_positive_line_count):
            bar = chart.get_bar_from_last(start_index+i)
            if bar is None:
                print("no previous bar", i)
                return (None, None)

            is_positive_line = bar.end - bar.begin > 0
            if not is_positive_line:
                print(str(i) + " prev bar is not positive bar")
                return (None, None)
            
        position_type = "long"
        target_value = use_bar.end * (1+self.buy_order_up_rate)

        if self.stop_loss_rate is not None:
            stoploss_rate = use_bar.end * self.stop_loss_rate
            return (position_type, target_value, stoploss_rate)
        else:
            return (position_type, target_value)


    def check_filter_by_ma_dir(self, chart, cur_bar, cur_bar_index_from_last):
        # get check bar
        check_ma_bar = chart.get_bar_from_last(cur_bar_index_from_last + self.filter_ma_bar_span)
        if check_ma_bar is None:
            # cannot check
            print("check ma filter: no previous bar to check ma filter")
            return False
            
        # get check ma value
        if self.filter_ma_keyname not in check_ma_bar.technical_values or \
           self.filter_ma_keyname not in cur_bar.technical_values:
            print("check ma filter: no techinical value of " + self.filter_ma_keyname)
            return False

        # check filter
        cur_ma = cur_bar.technical_values[self.filter_ma_keyname]
        pre_ma = check_ma_bar.technical_values[self.filter_ma_keyname]

        if cur_ma is None or pre_ma is None: return False
        if cur_ma < pre_ma:
            print("check ma filter: cur_ma < pre_ma = %f < %f" % (cur_ma, pre_ma,))
            return False
            
        return True
        
    def market_sell_decide_algorithm(self, chart, open_rate, created_time, current_time):
        if super(PriceDeciderByContinuousPositiveLine, self).market_sell_decide_algorithm(chart, open_rate, created_time, current_time) is True:
            return True

        # check losscut rate
        if self.losscut_rate is None: return False

        losscut_price = open_rate * self.losscut_rate
        last_bar = chart.get_bar_from_last()

        if last_bar is None: return False

        # dummy losscut
        if last_bar.end < losscut_price:
            print("losscut !!! end_v/losscut_v = %f/%f" % (float(last_bar.end),float(losscut_price),))
            return True

        return False
