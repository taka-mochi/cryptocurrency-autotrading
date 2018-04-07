# coding: utf-8
import unittest
from datetime import datetime
from datetime import timedelta
import pytz
from real_trade.ChartBars import Chart
from real_trade.ChartBars import Bar
from real_trade.Algorithm_PriceDeciderByContinuousPositiveLine import PriceDeciderByContinuousPositiveLine as AlgPosLine
from real_trade.TechnicalCalculator import TechnicalCalculator

time_offset = 100000*60

class TestAlgorithmByContinousPositiveLine(unittest.TestCase):
    def create_chartbase(self):
        chart = Chart(span_minutes=1, technical_calculator=TechnicalCalculator([3]))
        return chart

    def test_make_position_order_alg_wo_ma_filter(self):
        up_rate = 0.05
        alg = AlgPosLine(cont_positive_line_count=2,
                         buy_order_up_rate=up_rate,
                         close_div_rate_from_buy_value=0.01,
                         stop_loss_rate=0.975,
                         close_bar_count_to_hold=2,
                         do_filter_by_ma_slope=False,
                         make_order_only_first_time_bar=False)

        chart = self.create_chartbase()
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None,None), (t,p))

        chart.add_new_data(time_offset+10+60*0, 350)
        chart.add_new_data(time_offset+10+60*1, 300)
        chart.add_new_data(time_offset+10+60*2, 250)
        chart.add_new_data(time_offset+11+60*2, 260)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))

        chart.add_new_data(time_offset+10+60*3, 400)
        chart.add_new_data(time_offset+11+60*3, 410)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))

        chart.add_new_data(time_offset+10+60*4, 500)
        (t, p, sl) = alg.decide_make_position_order(chart)
        self.assertEqual(t, "long")
        self.assertAlmostEqual(p, 410*(1+up_rate))
        self.assertAlmostEqual(sl, 410*0.975)

        chart.add_new_data(time_offset+20+60*4, 500)
        chart.add_new_data(time_offset+10+60*5, 400)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))
        
        chart.add_new_data(time_offset+20+60*5, 401)
        chart.add_new_data(time_offset+10+60*6, 401)
        chart.add_new_data(time_offset+20+60*6, 402)
        chart.add_new_data(time_offset+10+60*7, 402)
        (t, p, sl) = alg.decide_make_position_order(chart)
        self.assertEqual(("long", 402*(1+up_rate)), (t, p))
        self.assertAlmostEqual(sl, 402*0.975)
        
        chart.add_new_data(time_offset+20+60*7, 401)
        chart.add_new_data(time_offset+10+60*8, 398)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))
        
    def test_make_position_order_alg_w_ma_filter(self):
        up_rate = 0.05
        alg = AlgPosLine(cont_positive_line_count=2,
                         buy_order_up_rate=up_rate,
                         close_div_rate_from_buy_value=0.01,
                         stop_loss_rate=0.975,
                         close_bar_count_to_hold=2,
                         do_filter_by_ma_slope=True,
                         filter_ma_count=3,      # 3maを基準にして相場判定する
                         filter_ma_bar_span=1,   # 1本前の3maと比較する
                         make_order_only_first_time_bar=False)  
                         
        chart = self.create_chartbase()
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None,None), (t,p))
        self.assertFalse(alg.check_filter_by_ma_dir(chart, chart.get_bar_from_last(), 0))
        
        chart.add_new_data(time_offset+10+60*0, 350)
        chart.add_new_data(time_offset+10+60*1, 300)
        chart.add_new_data(time_offset+10+60*2, 250)
        chart.add_new_data(time_offset+11+60*2, 260)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))
        self.assertFalse(alg.check_filter_by_ma_dir(chart, chart.get_bar_from_last(1), 1))

        chart.add_new_data(time_offset+10+60*3, 400)
        chart.add_new_data(time_offset+11+60*3, 410)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))
        self.assertFalse(alg.check_filter_by_ma_dir(chart, chart.get_bar_from_last(1), 1))

        # current の3ma: (410+260+300)/3
        # 1本前の3ma: (260+300+350)/3
        # current が上回っている => order 作る
        chart.add_new_data(time_offset+10+60*4, 200)
        (t, p, sl) = alg.decide_make_position_order(chart)
        self.assertEqual(t, "long")
        self.assertAlmostEqual(p, 410*(1+up_rate))
        self.assertAlmostEqual(sl, 410*0.975)
        self.assertTrue(alg.check_filter_by_ma_dir(chart, chart.get_bar_from_last(1), 1))

        # current の3ma: (210+410+260)/3
        # 1本前の3ma: (260+300+410)/3
        # 1本前の3maの方が大きい => orderなし
        #  * 60*4も60*3のtimestampも陽線なので、filter無しならorderが通る
        chart.add_new_data(time_offset+20+60*4, 210)
        chart.add_new_data(time_offset+10+60*5, 400)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))
        self.assertFalse(alg.check_filter_by_ma_dir(chart, chart.get_bar_from_last(1), 1))

        alg.do_filter_by_ma_slope = False
        (t, p, sl) = alg.decide_make_position_order(chart)
        self.assertEqual("long",t)
        self.assertAlmostEqual(210*(1+up_rate), p)
        self.assertAlmostEqual(210*0.975, sl)
        
    def test_losscut_rate(self):
        up_rate = 0.05
        losscut_rate = 0.99
        alg = AlgPosLine(cont_positive_line_count=2,
                         buy_order_up_rate=up_rate,
                         close_div_rate_from_buy_value=0.01,
                         close_bar_count_to_hold=2,
                         stop_loss_rate=None,
                         losscut_rate=losscut_rate,
                         do_filter_by_ma_slope=False,
                         make_order_only_first_time_bar=False)
                         
        chart = self.create_chartbase()
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None,None), (t,p))

        chart.add_new_data(time_offset+10+60*0, 350)
        chart.add_new_data(time_offset+10+60*1, 300)
        chart.add_new_data(time_offset+10+60*2, 250)
        chart.add_new_data(time_offset+11+60*2, 260)
        chart.add_new_data(time_offset+10+60*3, 400)
        chart.add_new_data(time_offset+11+60*3, 410)
        chart.add_new_data(time_offset+10+60*4, 500)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual(t, "long")
        self.assertAlmostEqual(p, 410*(1+up_rate))
        
        open_rate = 410*(1+up_rate)
        target_losscut = open_rate*losscut_rate
        base_time = datetime(year=1970,month=1,day=1, tzinfo=pytz.utc)
        buy_date = base_time + timedelta(seconds=20)
        now_time = base_time + timedelta(seconds=20)
        
        chart.add_new_data(time_offset+11+60*4, target_losscut+1)
        self.assertFalse(alg.market_sell_decide_algorithm(chart, open_rate, buy_date, now_time))
        
        chart.add_new_data(time_offset+12+60*4, target_losscut-0.1)
        self.assertTrue(alg.market_sell_decide_algorithm(chart, open_rate, buy_date, now_time))
        
if __name__ == "__main__":
    unittest.main()

