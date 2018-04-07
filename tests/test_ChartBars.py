# coding: utf-8
import unittest
from real_trade.ChartBars import Chart
from real_trade.ChartBars import Bar
from real_trade.TechnicalCalculator import TechnicalCalculator

# one bar in chart
class TestBar(unittest.TestCase):
    def test_bar(self):
        bar = Bar()
        self.assertTrue(bar.begin is None)
        self.assertTrue(bar.end   is None)
        self.assertTrue(bar.high  is None)
        self.assertTrue(bar.low   is None)
        self.assertFalse(bar.is_freezed())
        bar.freeze()
        self.assertTrue(bar.is_freezed())

        bar = Bar(20,30,40,50)
        self.assertEqual(bar.begin, 20)
        self.assertEqual(bar.end,   30)
        self.assertEqual(bar.high, 40)
        self.assertEqual(bar.low, 50)

        bar.update_by_new_value(60)
        self.assertEqual(bar.begin, 20)
        self.assertEqual(bar.end,   60)
        self.assertEqual(bar.high, 60)
        self.assertEqual(bar.low, 50)

        bar.update_by_new_value(55)
        self.assertEqual(bar.begin, 20)
        self.assertEqual(bar.end,   55)
        self.assertEqual(bar.high, 60)
        self.assertEqual(bar.low, 50)

        bar.update_by_new_value(10)
        self.assertEqual(bar.begin, 20)
        self.assertEqual(bar.end,   10)
        self.assertEqual(bar.high, 60)
        self.assertEqual(bar.low, 10)

    def test_freeze(self):
        bar = Bar(20,30,40,50)
        bar.freeze()

        exp = None
        try:
            bar.update_by_new_value(20)
        except Exception as e:
            exp = e
        self.assertTrue(isinstance(exp, AssertionError))

 
# Chart = list of Bar
# time is handled by unixtime
class TestChart(unittest.TestCase):
    def test_add_bars(self):
        chart = Chart(span_minutes=5)
        self.assertEqual(0, len(chart.bars_w_starttime))

        unixtime1 = 60*5*10000 + 60*5*10 + 3
        chart.add_new_data(unixtime1, 20)
        self.assertEqual(1, len(chart.bars_w_starttime))
        self.assertEqual(60*5*10000 + 60*5*10, chart.bars_w_starttime[0][0])
        self.assertEqual(20, chart.bars_w_starttime[0][1].begin)
        self.assertEqual(20, chart.bars_w_starttime[0][1].end)
        self.assertEqual(20, chart.bars_w_starttime[0][1].low)
        self.assertEqual(20, chart.bars_w_starttime[0][1].high)
        self.assertFalse(chart.bars_w_starttime[0][1].is_freezed())

        unixtime2 = 60*5*10000 + 60*5*10 + 43
        chart.add_new_data(unixtime2, 40)
        self.assertEqual(1, len(chart.bars_w_starttime))
        self.assertEqual(60*5*10000 + 60*5*10, chart.bars_w_starttime[0][0])
        self.assertEqual(20, chart.bars_w_starttime[0][1].begin)
        self.assertEqual(40, chart.bars_w_starttime[0][1].end)
        self.assertEqual(20, chart.bars_w_starttime[0][1].low)
        self.assertEqual(40, chart.bars_w_starttime[0][1].high)
        self.assertFalse(chart.bars_w_starttime[0][1].is_freezed())

        unixtime3 = 60*5*10000 + 60*5*11 + 8
        chart.add_new_data(unixtime3, 10)
        self.assertEqual(2, len(chart.bars_w_starttime))
        self.assertEqual(60*5*10000 + 60*5*10, chart.bars_w_starttime[0][0])
        self.assertTrue(chart.bars_w_starttime[0][1].is_freezed())
        self.assertEqual(60*5*10000 + 60*5*11, chart.bars_w_starttime[1][0])
        self.assertEqual(10, chart.bars_w_starttime[1][1].begin)
        self.assertEqual(10, chart.bars_w_starttime[1][1].end)
        self.assertEqual(10, chart.bars_w_starttime[1][1].low)
        self.assertEqual(10, chart.bars_w_starttime[1][1].high)
        self.assertFalse(chart.bars_w_starttime[1][1].is_freezed())

        unixtime4 = 60*5*10000 + 60*5*14 + 8
        chart.add_new_data(unixtime4, 100)
        self.assertEqual(5, len(chart.bars_w_starttime))
        for i in range(2,4):
            self.assertEqual(60*5*10000 + 60*5*(10+i), chart.bars_w_starttime[i][0])
            self.assertEqual(10, chart.bars_w_starttime[i][1].begin)
            self.assertEqual(10, chart.bars_w_starttime[i][1].end)
            self.assertEqual(10, chart.bars_w_starttime[i][1].low)
            self.assertEqual(10, chart.bars_w_starttime[i][1].high)
            self.assertTrue(chart.bars_w_starttime[i][1].is_freezed())

        self.assertEqual(60*5*10000 + 60*5*14, chart.bars_w_starttime[4][0])
        self.assertEqual(100, chart.bars_w_starttime[4][1].begin)
        self.assertEqual(100, chart.bars_w_starttime[4][1].end)
        self.assertEqual(100, chart.bars_w_starttime[4][1].low)
        self.assertEqual(100, chart.bars_w_starttime[4][1].high)
        self.assertFalse(chart.bars_w_starttime[4][1].is_freezed())
        
    def test_chart_less_than_1min_bar(self):
        chart = Chart(span_minutes=0.714)
        span_seconds = int(60*0.714)
        self.assertEqual(0, len(chart.bars_w_starttime))
        
        unixtime1 = span_seconds*10000 + span_seconds*10 + 3
        chart.add_new_data(unixtime1, 20)
        self.assertEqual(1, len(chart.bars_w_starttime))
        self.assertEqual(span_seconds*10000 + span_seconds*10, chart.bars_w_starttime[0][0])
        self.assertEqual(20, chart.bars_w_starttime[0][1].begin)
        self.assertEqual(20, chart.bars_w_starttime[0][1].end)
        self.assertEqual(20, chart.bars_w_starttime[0][1].low)
        self.assertEqual(20, chart.bars_w_starttime[0][1].high)
        self.assertFalse(chart.bars_w_starttime[0][1].is_freezed())

        unixtime2 = span_seconds*10000 + span_seconds*10 + 32
        chart.add_new_data(unixtime2, 40)
        self.assertEqual(1, len(chart.bars_w_starttime))
        self.assertEqual(span_seconds*10000 + span_seconds*10, chart.bars_w_starttime[0][0])
        self.assertEqual(20, chart.bars_w_starttime[0][1].begin)
        self.assertEqual(40, chart.bars_w_starttime[0][1].end)
        self.assertEqual(20, chart.bars_w_starttime[0][1].low)
        self.assertEqual(40, chart.bars_w_starttime[0][1].high)
        self.assertFalse(chart.bars_w_starttime[0][1].is_freezed())

        unixtime3 = span_seconds*10000 + span_seconds*11 + 8
        chart.add_new_data(unixtime3, 10)
        self.assertEqual(2, len(chart.bars_w_starttime))
        self.assertEqual(span_seconds*10000 + span_seconds*10, chart.bars_w_starttime[0][0])
        self.assertTrue(chart.bars_w_starttime[0][1].is_freezed())
        self.assertEqual(span_seconds*10000 + span_seconds*11, chart.bars_w_starttime[1][0])
        self.assertEqual(10, chart.bars_w_starttime[1][1].begin)
        self.assertEqual(10, chart.bars_w_starttime[1][1].end)
        self.assertEqual(10, chart.bars_w_starttime[1][1].low)
        self.assertEqual(10, chart.bars_w_starttime[1][1].high)
        self.assertFalse(chart.bars_w_starttime[1][1].is_freezed())

    def test_update_freeze(self):
        chart = Chart(span_minutes=5)
        self.assertEqual(0, len(chart.bars_w_starttime))

        unixtime1 = 10000*60*5+60*5*10 + 3
        chart.add_new_data(unixtime1, 20)
        self.assertEqual(1, len(chart.bars_w_starttime))
        self.assertEqual(10000*60*5+60*5*10, chart.bars_w_starttime[0][0])
        self.assertEqual(20, chart.bars_w_starttime[0][1].begin)
        self.assertEqual(20, chart.bars_w_starttime[0][1].end)
        self.assertEqual(20, chart.bars_w_starttime[0][1].low)
        self.assertEqual(20, chart.bars_w_starttime[0][1].high)
        self.assertFalse(chart.bars_w_starttime[0][1].is_freezed())

        chart.update_freeze_state(10000*60*5+60*5*11 + 30)
        self.assertTrue(chart.bars_w_starttime[0][1].is_freezed())

    def test_chart_with_technical_calculator(self):
        ma_counts = [3,7]
        tech_calc = TechnicalCalculator(ma_counts)
        chart = Chart(span_minutes=1,
                      technical_calculator=tech_calc)

        count = 10
        for i in range(count):
            latest_div_10 = (i+1)
            latest_end_value = latest_div_10*10
            chart.add_new_data(10000*60+i*60+1, latest_end_value)
            bar = chart.bars_w_starttime[-1][1]

            for ma_count in ma_counts:
                key = str(ma_count) + "ma_end"
                key_div = key + "_div_rate"
                self.assertTrue(key in bar.technical_values)
                self.assertTrue(key_div in bar.technical_values)

                if latest_div_10 < ma_count:
                    self.assertTrue(bar.technical_values[key] is None)
                    self.assertTrue(bar.technical_values[key_div] is None)
                else:
                    ma = sum([_*10.0 for _ in range(latest_div_10+1-ma_count, latest_div_10+1)])
                    ma /= ma_count
                    self.assertAlmostEqual(ma, bar.technical_values[key])
                    self.assertAlmostEqual((latest_end_value-ma)/ma, bar.technical_values[key_div])
        

    def test_convert_unixtime_to_bar_indexlike_value(self):
        chart = Chart(span_minutes=5)

        unixtime = 60*5+95
        self.assertEqual(1, chart.convert_unixtime_to_bar_indexlike_value(unixtime))
        self.assertEqual(5*60, chart.convert_indexlike_value_to_unixtime(1))

        unixtime = 60*5*2+87.5
        self.assertEqual(2, chart.convert_unixtime_to_bar_indexlike_value(unixtime))
        self.assertEqual(60*5*2, chart.convert_indexlike_value_to_unixtime(2.5))

        chart = Chart(span_minutes=15)
        unixtime = 60*15+95
        self.assertEqual(1, chart.convert_unixtime_to_bar_indexlike_value(unixtime))
        self.assertEqual(15*60, chart.convert_indexlike_value_to_unixtime(1))

        unixtime = 60*15*2+87.5
        self.assertEqual(2, chart.convert_unixtime_to_bar_indexlike_value(unixtime))
        self.assertEqual(15*60*2, chart.convert_indexlike_value_to_unixtime(2.5))

        chart = Chart(span_minutes=1)
        unixtime = 60*1+35
        self.assertEqual(1, chart.convert_unixtime_to_bar_indexlike_value(unixtime))
        self.assertEqual(60, chart.convert_indexlike_value_to_unixtime(1))

        unixtime = 60*1*2+37.5
        self.assertEqual(2, chart.convert_unixtime_to_bar_indexlike_value(unixtime))
        self.assertEqual(60*1*2, chart.convert_indexlike_value_to_unixtime(2.5))


    def test_get_bar_from_last(self):
        chart = Chart(span_minutes=5)
        self.assertEqual(0, len(chart.bars_w_starttime))

        unixtime1 = 10000*60*5+60*5*10 + 3
        chart.add_new_data(unixtime1, 20)

        last_bar = chart.get_bar_from_last(get_copy=False)
        self.assertEqual(20, last_bar.end)
        self.assertEqual(last_bar, chart.bars_w_starttime[-1][1])
        self.assertEqual(chart.get_bar_from_last(1), None)

        copy = chart.get_bar_from_last(get_copy=True)
        self.assertEqual(20, copy.end)
        self.assertNotEqual(copy, chart.bars_w_starttime[-1][1])

        unixtime2 = 10000*60*5 + 60*5*11 + 73
        chart.add_new_data(unixtime2, 40)

        last_bar = chart.get_bar_from_last(get_copy=False)
        self.assertEqual(40, last_bar.end)
        self.assertEqual(False, last_bar.is_freezed())

        last_prev_bar = chart.get_bar_from_last(1, get_copy=True)
        self.assertNotEqual(last_prev_bar, chart.bars_w_starttime[-2][1])
        self.assertEqual(20, copy.end)
        self.assertEqual(True, last_prev_bar.is_freezed())

if __name__ == "__main__":
    unittest.main()
