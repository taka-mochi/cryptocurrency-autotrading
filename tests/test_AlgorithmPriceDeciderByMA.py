# coding: utf-8
import unittest
from datetime import datetime
from datetime import timedelta
import pytz
from real_trade.ChartBars import Chart
from real_trade.ChartBars import Bar
from real_trade.Algorithm_PriceDeciderByMA import PriceDeciderByMA
from real_trade.TechnicalCalculator import TechnicalCalculator

time_offset = 10000*60

class TestAlgorithmByMA(unittest.TestCase):
    def create_chartbase(self):
        chart = Chart(span_minutes=1, technical_calculator=TechnicalCalculator([3]))
        return chart

    def test_make_position_order_alg(self):
        alg = PriceDeciderByMA(use_ma_count=3,
                               buy_ma_div_rate=-0.05,
                               sell_div_rate_from_buy_value=0.1,
                               sell_bar_count_to_hold=3)
        
        chart = self.create_chartbase()
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None,None), (t,p))

        chart.add_new_data(time_offset+10+60*0, 350)
        chart.add_new_data(time_offset+10+60*1, 300)
        chart.add_new_data(time_offset+10+60*2, 250)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))

        chart.add_new_data(time_offset+10+60*3, 400)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual(t, "long")
        self.assertAlmostEqual((350+300+250)/3*0.95, p)

        chart.add_new_data(time_offset+20+60*3, 500)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual(t, "long")
        self.assertAlmostEqual((350+300+250)/3*0.95, p)

        chart.add_new_data(time_offset+20+60*4, 100)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual(t, "long")
        self.assertAlmostEqual((300+250+500)/3*0.95, p)

    def test_make_position_short_order_alg(self):
        alg = PriceDeciderByMA(use_ma_count=3,
                               buy_ma_div_rate=0.05,
                               sell_div_rate_from_buy_value=-0.1,
                               sell_bar_count_to_hold=3)
        
        chart = self.create_chartbase()
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None,None), (t,p))

        chart.add_new_data(time_offset+10+60*0, 350)
        chart.add_new_data(time_offset+10+60*1, 300)
        chart.add_new_data(time_offset+10+60*2, 250)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual((None, None), (t, p))

        chart.add_new_data(time_offset+10+60*3, 400)
        (t, p) = alg.decide_make_position_order(chart)
        self.assertEqual(t, "short")
        self.assertAlmostEqual((350+300+250)/3*1.05, p)

    def test_market_sell_decide_alg(self):

        alg = PriceDeciderByMA(use_ma_count=3,
                               buy_ma_div_rate=-0.05,
                               sell_div_rate_from_buy_value=0.1,
                               sell_bar_count_to_hold=5)
        chart = self.create_chartbase()
        
        chart.add_new_data(time_offset+1+60*0, 100)
        chart.add_new_data(time_offset+1+60*1, 110)
        chart.add_new_data(time_offset+1+60*2, 120)
        chart.add_new_data(time_offset+1+60*3, 130)
        chart.add_new_data(time_offset+1+60*4, 140)
        chart.add_new_data(time_offset+1+60*5, 150)
        chart.add_new_data(time_offset+1+60*6, 160)
        
        base_time = datetime(year=1970,month=1,day=1, tzinfo=pytz.utc)
        
        buy_date = base_time + timedelta(seconds=20)
        now_time = base_time + timedelta(seconds=32+60*5)
        ret = alg.market_sell_decide_algorithm(chart,
                                               105,
                                               buy_date, 
                                               now_time)
        self.assertTrue(ret)

        now_time = base_time + timedelta(seconds=32+60*4)
        ret = alg.market_sell_decide_algorithm(chart,
                                               105,
                                               buy_date, 
                                               now_time)
        self.assertFalse(ret)

        now_time = base_time + timedelta(seconds=32+60*6)
        ret = alg.market_sell_decide_algorithm(chart,
                                               105,
                                               buy_date, 
                                               now_time)
        self.assertTrue(ret)
        
        now_time = datetime(year=1970,month=1,day=1, tzinfo=pytz.timezone('Asia/Tokyo')) +  timedelta(seconds=32+60*6)
        ret = alg.market_sell_decide_algorithm(chart,
                                               105,
                                               buy_date, 
                                               now_time)
        self.assertFalse(ret)

    def test_make_sell_position_order_alg(self):
        alg = PriceDeciderByMA(use_ma_count=3,
                               buy_ma_div_rate=-0.05,
                               sell_div_rate_from_buy_value=0.1,
                               sell_bar_count_to_hold=3)

        self.assertAlmostEqual(int(10000*(1+0.1)), alg.sell_price_decide_algorithm(10000))
        self.assertAlmostEqual(int(12000*(1+0.1)), alg.sell_price_decide_algorithm(12000))
        self.assertAlmostEqual(int(9000*(1+0.1)), alg.sell_price_decide_algorithm(9000))

if __name__ == "__main__":
    unittest.main()

