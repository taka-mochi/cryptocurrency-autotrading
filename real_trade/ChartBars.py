# coding: utf-8
import os
from datetime import datetime
from datetime import timedelta
import sys
import time
import math
import threading

# one bar in chart
class Bar(object):
    def __init__(self, begin = None, end = None, high = None, low = None, technical_values = None):
        self.begin = begin
        self.end = end
        self.high = high
        self.low = low

        self.technical_values = technical_values  # this is optional data

        self.is_freezed_ = False

    def make_copy(self):
        bar = Bar(self.begin, self.end, self.high, self.low, self.technical_values)
        bar.is_freezed_ = self.is_freezed_
        return bar

    def update_by_new_value(self, value, update_only_high_or_low=False):
        assert (self.is_freezed_ is False)

        if self.begin is None:
            self.begin = value

        if self.high is None or value > self.high:
            self.high = value
        if self.low is None or value < self.low:
            self.low = value

        if not update_only_high_or_low:
            self.end = value

    def freeze(self):
        self.is_freezed_ = True

    def is_freezed(self):
        return self.is_freezed_

# Chart = list of Bar
# time is handled by unixtime
class Chart(object):
    def __init__(self, span_minutes, technical_calculator = None):

        # cannot handle more than 1 hour bar
        assert (span_minutes <= 60)

        self.span_seconds = int(span_minutes * 60)
        self.bars_w_starttime = []
        self.bars_lock_obj = threading.Lock()
        self.technical_calculator = technical_calculator

        self.max_bar_store_count = 3600

    def _init_bar_create(self, add_unixtime, add_value):
        self.bars_w_starttime = []

        bar = Bar(add_value, add_value, add_value, add_value)
        add_unixtime_spansecond_divided = (add_unixtime // self.span_seconds)*self.span_seconds
        add_datetime = datetime.fromtimestamp(float(add_unixtime_spansecond_divided))

        start_datetime = datetime(add_datetime.year, add_datetime.month, add_datetime.day, add_datetime.hour, add_datetime.minute, add_datetime.second)
        start_unixtime = time.mktime(start_datetime.timetuple())

        self.bars_w_starttime.append((start_unixtime, bar))

        self.update_last_technical_values()

    def convert_unixtime_to_bar_indexlike_value(self, unixtime):
        return int(math.floor(unixtime)) // (self.span_seconds)

    def convert_indexlike_value_to_unixtime(self, indexlike_value):
        return int(math.floor(indexlike_value)*self.span_seconds)

    # call technical value updater to last bar instance
    def update_last_technical_values(self):
        if self.technical_calculator is not None:
            technical_values = \
                self.technical_calculator.calculate_technical_values_for_last_bar(self.bars_w_starttime)
            self.bars_w_starttime[-1][1].technical_values = technical_values

    # add new tick data to chart
    def add_new_data(self, add_unixtime, add_value, update_only_high_or_low=False):
        with self.bars_lock_obj:

            if len(self.bars_w_starttime) == 0:
                # initial add
                self._init_bar_create(add_unixtime, add_value)
                return

            last_bar = self.bars_w_starttime[-1]
            last_bar_starttime = last_bar[0]
            last_bar_inst      = last_bar[1]

            if add_unixtime < last_bar_starttime:
                print("impossible!!! older data cannot be inserted!!")
                print("last unixtime: %f, passed unixtime: %f" % (float(last_bar_starttime), float(add_unixtime),))
                return

            add_index_of_minutes  = self.convert_unixtime_to_bar_indexlike_value(add_unixtime)
            last_index_of_minutes = self.convert_unixtime_to_bar_indexlike_value(last_bar_starttime)

            if add_index_of_minutes == last_index_of_minutes:
                # bar is not changed
                last_bar_inst.update_by_new_value(add_value, update_only_high_or_low)
                self.update_last_technical_values()

            elif not update_only_high_or_low:
                # make new bar
                last_end_value = last_bar_inst.end
                last_bar_inst.freeze()
                self.update_last_technical_values()

                # add blank time bar (e.g. 1min span: last 16:05:30 - new 16:08:10 => bar of 16:06:00,16:07:00 will be inserted
                while last_index_of_minutes+1 < add_index_of_minutes:
                    bar = Bar(last_end_value, last_end_value, last_end_value, last_end_value)
                    bar.freeze()
                    self.bars_w_starttime.append((self.convert_indexlike_value_to_unixtime(last_index_of_minutes+1), bar))
                    self.update_last_technical_values()

                    last_index_of_minutes += 1

                new_last_bar = Bar(add_value, add_value, add_value, add_value)
                self.bars_w_starttime.append((self.convert_indexlike_value_to_unixtime(add_index_of_minutes), new_last_bar))
                self.update_last_technical_values()

                # remove old data if bar count exceeds the limitation
                if len(self.bars_w_starttime) > self.max_bar_store_count:
                    remove_count = len(self.bars_w_starttime) - self.max_bar_store_count
                    self.bars_w_starttime = self.bars_w_starttime[remove_count:]

    def add_new_value_by_kline_data(self, start_unixtime, begin, end, low, high):
        # add data by ordering: begin => low => high => end
        self.add_new_data(start_unixtime  , begin)
        self.add_new_data(start_unixtime+1, low)
        self.add_new_data(start_unixtime+2, high)
        self.add_new_data(start_unixtime+3, end)

    # check current time whether last bar instance should be freezed or not, and perform freeze if required
    def update_freeze_state(self, now_unixtime):
        with self.bars_lock_obj:
            if len(self.bars_w_starttime) == 0: return

            last_index_of_minutes = self.convert_unixtime_to_bar_indexlike_value(self.bars_w_starttime[-1][0])
            now_index_of_minutes  = self.convert_unixtime_to_bar_indexlike_value(now_unixtime)

            if last_index_of_minutes != now_index_of_minutes:
                self.bars_w_starttime[-1][1].freeze()

    def get_bar_from_last(self, offset_from_last = 0, get_copy = True, with_timestamp = False):
        timestamp = None
        return_bar = None
        with self.bars_lock_obj:
            if len(self.bars_w_starttime) < 1+offset_from_last:
                pass
            else:
                (timestamp, return_bar) = self.bars_w_starttime[-1-offset_from_last]
                if get_copy:
                    return_bar = return_bar.make_copy()

        if with_timestamp:
            return timestamp, return_bar
        else:
            return return_bar
