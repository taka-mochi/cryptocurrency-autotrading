# coding: utf-8
import unittest
from real_trade.ChartBars import Chart
from real_trade.ChartBars import Bar
from real_trade.TechnicalCalculator import TechnicalCalculator

class TestCalculator(unittest.TestCase):
    def test_calc_ma(self):
        calc = TechnicalCalculator()
        bars = [
            (1, Bar(end=20)),
            (2, Bar(end=10)),
            (3, Bar(end=40)),
            (4, Bar(end=30)),
        ]
        
        v = calc.calculate_end_ma_for_last_bar(bars, 2)
        self.assertAlmostEqual((40+30)/2.0, v)

        v = calc.calculate_end_ma_for_last_bar(bars, 1)
        self.assertAlmostEqual((30)/1.0, v)

        v = calc.calculate_end_ma_for_last_bar(bars, 3)
        self.assertAlmostEqual((40+30+10)/3.0, v)

        v = calc.calculate_end_ma_for_last_bar(bars, 4)
        self.assertAlmostEqual((40+30+10+20)/4.0, v)

        v = calc.calculate_end_ma_for_last_bar(bars, 5)
        self.assertTrue(v is None)

        v = calc.calculate_end_ma_for_last_bar(bars, 0)
        self.assertTrue(v is None)
        
        v = calc.calculate_end_ma_for_last_bar(bars, -1)
        self.assertTrue(v is None)

    def test_cal_all(self):

        calc = TechnicalCalculator([3,5,9])
        bars = []

        count = 8
        for i in range(count):
            bars.append(((i+1), Bar(end=(i+1)*10)))

        ret = calc.calculate_technical_values_for_last_bar(bars)
        self.assertTrue("3ma_end" in ret)
        self.assertTrue("5ma_end" in ret)
        self.assertTrue("9ma_end" in ret)
        self.assertTrue("3ma_end_div_rate" in ret)
        self.assertTrue("5ma_end_div_rate" in ret)
        self.assertTrue("9ma_end_div_rate" in ret)

        expect_3ma = (count+count-1+count-2)*10/3.0
        self.assertAlmostEqual(expect_3ma, ret["3ma_end"])
        self.assertAlmostEqual((count*10 - expect_3ma)/expect_3ma, ret["3ma_end_div_rate"])
        expect_5ma = (count+count-1+count-2+count-3+count-4)*10/5.0
        self.assertAlmostEqual(expect_5ma, ret["5ma_end"])
        self.assertAlmostEqual((count*10 - expect_5ma)/expect_5ma, ret["5ma_end_div_rate"])

        self.assertTrue(ret["9ma_end"] is None)
        self.assertTrue(ret["9ma_end_div_rate"] is None)

if __name__ == "__main__":
    unittest.main()
