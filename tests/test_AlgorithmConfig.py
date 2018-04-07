# coding: utf-8
import unittest
import os
from real_trade.AlgorithmConfig import AlgorithmConfig

from datetime import datetime
from datetime import timedelta
import pytz

import json
from real_trade.Algorithm_PriceDeciderByMA import PriceDeciderByMA
from real_trade.Algorithm_PriceDeciderByHighestOrLowest import PriceDeciderByHighestOrLowest
from real_trade.Algorithm_PriceDeciderByContinuousPositiveLine import PriceDeciderByContinuousPositiveLine

class TestAlgorithmConfig(unittest.TestCase):
    TMP_DIR = "tmp_algorithm_config"
    
    def _create_test_tmp_dir(self):
        if not os.path.exists(TestAlgorithmConfig.TMP_DIR):
            os.makedirs(TestAlgorithmConfig.TMP_DIR)
    
    def dump_to_test_tmp_dir(self, file_name, data):
        with open(os.path.join(TestAlgorithmConfig.TMP_DIR, file_name), "w") as fw:
            fw.write(json.dumps(data))
    
    def setUp(self):
        self._create_test_tmp_dir()
    
    def test_loadnormal(self):
        test1 = [
          {"use_bar_count":20,"open_rate":-0.12,"close_rate":0.09,"max_hold_bar_count":21,"lot":0.9,"algorithm_type":"ma_div"}
        ]
        self.dump_to_test_tmp_dir("test_1.json", test1)
        config = AlgorithmConfig.load_from_json(os.path.join(TestAlgorithmConfig.TMP_DIR, "test_1.json"))
        self.assertEqual(1, len(config.configs))
        c1 = config.configs[0]
        self.assertEqual(c1.use_bar_count, 20)
        self.assertEqual(c1.open_rate, -0.12)
        self.assertEqual(c1.close_rate, 0.09)
        self.assertEqual(c1.max_hold_bar_count, 21)
        self.assertEqual(c1.lot, 0.9)
        self.assertEqual(c1.algorithm_type, "ma_div")
        
        price_decider = c1.create_price_decider()
        self.assertTrue("PriceDeciderByMA" in str(type(price_decider)))
        self.assertEqual(price_decider.use_ma_count, 20)
        self.assertEqual(price_decider.open_ma_div_rate, -0.12)
        self.assertEqual(price_decider.close_div_rate_from_open_value, 0.09)
        self.assertEqual(price_decider.close_bar_count_to_hold, 21)
        
    def test_loadmulti(self):
        test2 = [
          {"use_bar_count":20,"open_rate":-0.12,"close_rate":0.09,"max_hold_bar_count":21,"lot":0.9,"algorithm_type":"ma_div"},
          {"use_bar_count":11,"open_rate":-0.02,"close_rate":0.07,"max_hold_bar_count":16,"algorithm_type":"high_or_low_div"},
            {"open_rate":0.02,"close_rate":0.01, "max_hold_bar_count": 3, "algorithm_type": "bar_count_scal", "cont_positive_line_count": 2, "do_filter_by_ma_slope": True, "filter_ma_count": 5, "filter_ma_bar_span": 3, "stoploss_rate": 0.97},
        ]
        self.dump_to_test_tmp_dir("test_2.json", test2)
        config = AlgorithmConfig.load_from_json(os.path.join(TestAlgorithmConfig.TMP_DIR, "test_2.json"))
        self.assertEqual(3, len(config.configs))
        c1 = config.configs[0]
        self.assertEqual(c1.use_bar_count, 20)
        self.assertEqual(c1.open_rate, -0.12)
        self.assertEqual(c1.close_rate, 0.09)
        self.assertEqual(c1.max_hold_bar_count, 21)
        self.assertEqual(c1.lot, 0.9)
        self.assertEqual(c1.algorithm_type, "ma_div")
        for i,v in enumerate(test2):
            for key in v.keys():
                self.assertTrue(key in config.configs[i].all_parameters)

        price_decider = c1.create_price_decider()
        self.assertTrue("PriceDeciderByMA" in str(type(price_decider)))
        self.assertEqual(price_decider.use_ma_count, 20)
        self.assertEqual(price_decider.open_ma_div_rate, -0.12)
        self.assertEqual(price_decider.close_div_rate_from_open_value, 0.09)
        self.assertEqual(price_decider.close_bar_count_to_hold, 21)

        #######
        
        c2 = config.configs[1]
        self.assertEqual(c2.use_bar_count, 11)
        self.assertEqual(c2.open_rate, -0.02)
        self.assertEqual(c2.close_rate, 0.07)
        self.assertEqual(c2.max_hold_bar_count, 16)
        self.assertEqual(c2.lot, 1.0)
        self.assertEqual(c2.algorithm_type, "high_or_low_div")

        price_decider = c2.create_price_decider()
        self.assertTrue("PriceDeciderByHighestOrLowest" in str(type(price_decider)))
        self.assertEqual(price_decider.use_bar_count, 11)
        self.assertEqual(price_decider.open_div_rate, -0.02)
        self.assertEqual(price_decider.use_high, True)
        self.assertEqual(price_decider.close_bar_count_to_hold, 16)
        self.assertEqual(price_decider.close_div_rate_from_open_value, 0.07)

        c3 = config.configs[2]
        self.assertEqual(c3.use_bar_count, None)
        self.assertEqual(c3.open_rate, 0.02)
        self.assertEqual(c3.close_rate, 0.01)
        self.assertEqual(c3.max_hold_bar_count, 3)
        self.assertEqual(c3.lot, 1.0)
        self.assertEqual(c3.algorithm_type, "bar_count_scal")
        self.assertEqual(c3.all_parameters["cont_positive_line_count"], 2)
        self.assertEqual(c3.all_parameters["stoploss_rate"], 0.97)
        self.assertEqual(c3.all_parameters["do_filter_by_ma_slope"], True)
        self.assertEqual(c3.all_parameters["filter_ma_count"], 5)
        self.assertEqual(c3.all_parameters["filter_ma_bar_span"], 3)

        price_decider = c3.create_price_decider()
        self.assertTrue("PriceDeciderByContinuousPositiveLine" in str(type(price_decider)))
        self.assertEqual(price_decider.buy_order_up_rate, 0.02)
        self.assertEqual(price_decider.close_bar_count_to_hold, 3)
        self.assertEqual(price_decider.close_div_rate_from_open_value, 0.01)
        self.assertEqual(price_decider.cont_positive_line_count, 2)
        self.assertEqual(price_decider.stop_loss_rate, 0.97)
        self.assertEqual(price_decider.do_filter_by_ma_slope, True)
        self.assertEqual(price_decider.filter_ma_count, 5)
        self.assertEqual(price_decider.filter_ma_bar_span, 3)
        self.assertEqual(price_decider.filter_ma_keyname, "5ma_end")

        
    def test_loaderror(self):
        test3 = [
          {"use_bar_cont":20,"open_rate":-0.12,"close_rate":0.09,"max_hodl_bar_count":21,"lot":0.9,"algorithm_type":"ma_div"},
          {"use_bar_count":11,"open_rate":-0.02,"close_ate":0.07,"max_hold_bar_count":16,"algorithm_type":"high_or_low_div"},
        ]
        self.dump_to_test_tmp_dir("test_3.json", test3)
        config = AlgorithmConfig.load_from_json(os.path.join(TestAlgorithmConfig.TMP_DIR, "test_3.json"))
        print(config.configs)
        self.assertEqual(0, len(config.configs))
        

if __name__ == "__main__":
    unittest.main()

