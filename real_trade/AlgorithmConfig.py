# coding: utf-8

import json
from Algorithm_PriceDeciderByMA import PriceDeciderByMA
from Algorithm_PriceDeciderByHighestOrLowest import PriceDeciderByHighestOrLowest
from Algorithm_PriceDeciderByContinuousPositiveLine import PriceDeciderByContinuousPositiveLine

class OneAlgorithmConfig(object):
    def __init__(self):
        self.use_bar_count = 25
        self.open_rate = -0.1
        self.close_rate = 0.1
        self.max_hold_bar_count = 15
        self.stoploss_rate = None
        self.lot = 1.0
        self.use_leverage = True
        self.algorithm_type = "ma_div"
        self.pair = "btc_jpy"
        
        self.all_parameters = {}  # アルゴリズムによっては上記以外の値も入っている
        
    def is_algorithm_type_valid(self):
        return self.algorithm_type == "ma_div" or \
               self.algorithm_type == "high_or_low_div" or \
               self.algorithm_type == "bar_count_scal"
               
    def create_price_decider(self):
        if self.algorithm_type == "ma_div":
            return PriceDeciderByMA(use_ma_count=self.use_bar_count,
                                   buy_ma_div_rate=self.open_rate,
                                   sell_div_rate_from_buy_value=self.close_rate,
                                   sell_bar_count_to_hold=self.max_hold_bar_count)
                                   
        elif self.algorithm_type == "high_or_low_div":
            return PriceDeciderByHighestOrLowest(use_bar_count=self.use_bar_count,
                                                 open_div_rate=self.open_rate,
                                                 close_div_rate_from_buy_value=self.close_rate,
                                                 close_bar_count_to_hold=self.max_hold_bar_count)
        elif self.algorithm_type == "bar_count_scal":
            params = self.all_parameters
            assert ("cont_positive_line_count" in params)
            assert ("do_filter_by_ma_slope" in params)
            if params["do_filter_by_ma_slope"]:
                assert ("filter_ma_count" in params)
                assert ("filter_ma_bar_span" in params)

            return PriceDeciderByContinuousPositiveLine(
                cont_positive_line_count=params["cont_positive_line_count"],
                buy_order_up_rate=self.open_rate,
                close_div_rate_from_buy_value=self.close_rate,
                stop_loss_rate=params["stoploss_rate"] if "stoploss_rate" in params else None,
                close_bar_count_to_hold=self.max_hold_bar_count,
                do_filter_by_ma_slope=params["do_filter_by_ma_slope"],
                filter_ma_count=params["filter_ma_count"],
                filter_ma_bar_span=params["filter_ma_bar_span"],
                losscut_rate=params["losscut_rate"] if "losscut_rate" in params else None)

            
        return None

class AlgorithmConfig(object):
    def __init__(self):
        self.configs = []
        
    @staticmethod
    def load_from_json(json_file):
        json_loaded = json.load(open(json_file))

        get_or_default = lambda json_inst, key, default: json_inst[key] if key in json_inst else default

        new_inst = AlgorithmConfig()
        new_inst.configs = []
        for i, one_alg in enumerate(json_loaded):
            inst = OneAlgorithmConfig()
            inst.use_bar_count = get_or_default(one_alg, "use_bar_count", None)
            inst.open_rate        = get_or_default(one_alg, "open_rate", None)
            inst.close_rate       = get_or_default(one_alg, "close_rate", None)
            inst.max_hold_bar_count = get_or_default(one_alg, "max_hold_bar_count", None)
            inst.stoploss_rate = get_or_default(one_alg, "stoploss_rate", None)
            inst.use_leverage = get_or_default(one_alg, "use_leverage", True)
            inst.lot = get_or_default(one_alg, "lot", 1.0)
            inst.algorithm_type = get_or_default(one_alg, "algorithm_type", None)
            inst.pair = get_or_default(one_alg, "pair", "btc_jpy")
            
            if inst.open_rate is None or \
               inst.close_rate is None or \
               inst.max_hold_bar_count is None or \
               inst.algorithm_type is None:
                print("%dth algorithm config is not valid!!" % i)
                continue
                
            inst.all_parameters = one_alg
            
            # check values
            if inst.open_rate != 'market':
                assert (isinstance(inst.open_rate, float))
            assert (isinstance(inst.close_rate, float))
            assert (isinstance(inst.max_hold_bar_count, int))
            assert (isinstance(inst.lot, float))
            #assert (isinstance(inst.algorithm_type, str))
            
            new_inst.configs.append(inst)
        
        return new_inst
        
        
