# coding: utf-8
from ChartBars import Chart

class TechnicalCalculator(object):
    def __init__(self, calc_ma_counts = [5,15]):
        self.calc_ma_counts = calc_ma_counts

    def calculate_technical_values_for_last_bar(self, bars):
        result = {}
        last_bar_inst = bars[-1][1]

        for ma_count in self.calc_ma_counts:
            v          = self.calculate_end_ma_for_last_bar(bars, ma_count)
            ma_key     = str(ma_count)+"ma_end"
            ma_div_key = ma_key + "_div_rate"
            result[ma_key] = v

            if v is not None:
                result[ma_div_key] = 1.0*(last_bar_inst.end-v)/v
            else:
                result[ma_div_key] = None

        return result

    def calculate_end_ma_for_last_bar(self, bars, ma_count):
        if len(bars) < ma_count or ma_count <= 0:
            return None

        sum_value = 0
        sum_value = sum([x[1].end for x in bars[-ma_count:]])
        return 1.0*sum_value / ma_count
