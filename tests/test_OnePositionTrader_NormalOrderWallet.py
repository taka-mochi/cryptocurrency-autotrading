# coding: utf-8
import unittest
import math
import random
from datetime import datetime
import pytz
import json
from real_trade.Algorithm_PriceDeciderByContinuousPositiveLine import PriceDeciderByContinuousPositiveLine
from real_trade.ChartBars import Chart
from real_trade.Algorithm_PriceDeciderByMA import PriceDeciderByMA
from real_trade.TechnicalCalculator import TechnicalCalculator
from real_trade.MoveAverageTradePosition import OnePositionTrader
from real_trade.Util import BitcoinUtil

from tests import DummyApiForTest

time_offset = 10000*60

class TestOnePositionTrader_NormalOrderWallet(unittest.TestCase):
    def create_chartbase(self):
        chart = Chart(span_minutes=1, technical_calculator=TechnicalCalculator([3]))
        return chart

    def create_dummyapi(self):
        return DummyApiForTest.ApiDummyForTest(self, _tick_price=1.0, _tick_amount=0.00000001, _min_amount=0.005, is_leverage=False)
    
    def test_update_new_order(self):
        stoploss = 0.98
        open_rate = 0.015
        close_rate = 0.1
        decider = PriceDeciderByContinuousPositiveLine(
            cont_positive_line_count=2,
            buy_order_up_rate=open_rate,
            close_div_rate_from_buy_value=close_rate,
            stop_loss_rate=stoploss,
            close_bar_count_to_hold=3,
            do_filter_by_ma_slope=False,
            make_order_only_first_time_bar=False)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, use_leverage=False)
        default_money = 100000
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money)
        self.assertEqual(default_money, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()
        
        # no data. new order should not be ordered
        dummy_api.set_api_fail()
        dummy_api.test_create_api_must_not_be_called()
        one_pos.update_new_orders(chart)
        dummy_api.set_api_fail_by_none()
        one_pos.update_new_orders(chart)

        # not enough bar
        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+2, 900)
        chart.add_new_data(time_offset+1+60, 910)
        chart.add_new_data(time_offset+2+60, 1000)
        chart.add_new_data(time_offset+1+60*2, 1200)
        chart.add_new_data(time_offset+2+60*2, 1250)
        dummy_api.test_create_api_must_not_be_called()
        dummy_api.set_api_fail()
        one_pos.update_new_orders(chart)
        dummy_api.set_api_fail_by_none()
        one_pos.update_new_orders(chart)

        # enough bar
        print("===============")
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        rate = math.floor(1250*(1+open_rate))
        dummy_api.set_create_required_param_once({
            "rate": math.floor(rate),
            "amount": BitcoinUtil.roundBTCby1satoshi(default_money/rate),
            "order_type": "buy",
            "stop_loss_rate": float(int(1250*stoploss),)
        })
        one_pos.update_new_orders(chart)
        print("===============")

        # dont request same order
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(False)
        chart.add_new_data(time_offset+2+60*3, 1050)
        one_pos.update_new_orders(chart)
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        # minimum
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(2)
        one_pos.set_max_free_margin_of_base_currency(default_money)
        one_pos.update_new_orders(chart)
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(2)
        one_pos.update_new_orders(chart)
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money/2)
        
        # next
        chart.add_new_data(time_offset+30+60*4, 900)
        dummy_api.set_api_success()
        rate = math.floor(1050*(1+open_rate))
        dummy_api.set_create_required_param_once({
            "rate": math.floor(rate),
            "amount": BitcoinUtil.roundBTCby1satoshi(default_money/2/rate),
            "order_type": "buy",
            "stop_loss_rate": float(int(1050*stoploss)),
        })
        one_pos.update_new_orders(chart)
        
    def test_update_positions(self):
        stoploss = 0.98
        open_rate = 0.015
        close_rate = 0.1
        decider = PriceDeciderByContinuousPositiveLine(
            cont_positive_line_count=2,
            buy_order_up_rate=open_rate,
            close_div_rate_from_buy_value=close_rate,
            stop_loss_rate=stoploss,
            close_bar_count_to_hold=3,
            do_filter_by_ma_slope=False,
            make_order_only_first_time_bar=False)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, use_leverage=False)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()
        

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+2+60, 1200)
        chart.add_new_data(time_offset+2+60*2, 1250)
        chart.add_new_data(time_offset+3+60*2, 1300)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        rate = math.floor(1300*(1+open_rate))
        dummy_api.set_create_required_param_once({
            "rate": rate,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/rate),
            "stop_loss_rate": float(int(1300*stoploss)),
        })
        one_pos.update_new_orders(chart)


        position_status = {
            "transactions": [
                {
                    "id": 38,
                    "order_id": 1,
                    "created_at": "2015-11-19T07:02:21.000Z",
                    "funds": {
                        "btc": 0.1,
                        "jpy": -4096.135
                    },
                    "pair": "btc_jpy",
                    "rate": 40900.0,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },
                {
                    "id": 37,
                    "order_id": 1,
                    "created_at": "2015-11-20T06:02:21.000Z",
                    "funds": {
                        "btc": 0.05,
                        "jpy": -2096.135
                    },
                    "pair": "btc_jpy",
                    "rate": 41922.7,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },

            ]
        }
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_transaction_status(position_status["transactions"])

        def check_position(test, one_pos, pos, tr_id, side, amount, rate, created):
            self.assertEqual(tr_id, pos["id"])
            self.assertEqual(side, pos["side"])
            self.assertAlmostEqual(amount, pos["amount"])
            self.assertAlmostEqual(rate, pos["open_rate"])
            self.assertEqual(0, len(one_pos.position_id_to_sellids[tr_id]))
            self.assertEqual((created - pos["created_at_datetime"]).total_seconds(), 0)

        
        self.assertEqual(2, len(one_pos.positions))

        check_position(self, one_pos, one_pos.positions[0], 38, "buy", 0.1, 40900, 
                       datetime(year=2015,month=11,day=19,hour=7,minute=2,second=21,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[1], 37, "buy", 0.05, 41922.7, 
                       datetime(year=2015,month=11,day=20,hour=6,minute=2,second=21,tzinfo=pytz.utc))
        self.assertAlmostEqual(40900*0.1 + 41922.7*0.05, one_pos.positioned_price_base)
        self.assertAlmostEqual(0.15, one_pos.positioned_value_in_qty)

        
        position_status = {
            "transactions": [
                # new transaction!
                {
                    "id": 40,
                    "order_id": 1,
                    "created_at": "2015-11-18T08:03:21.000Z",
                    "funds": {
                        "btc": 0.2,
                        "jpy": -10100.0
                    },
                    "pair": "btc_jpy",
                    "rate": 50500.0,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },
                # old transaction!
                {
                    "id": 38,
                    "order_id": 1,
                    "created_at": "2015-11-19T07:02:21.000Z",
                    "funds": {
                        "btc": 0.1,
                        "jpy": -4096.135
                    },
                    "pair": "btc_jpy",
                    "rate": 40900.0,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },
                {
                    "id": 37,
                    "order_id": 1,
                    "created_at": "2015-11-20T06:02:21.000Z",
                    "funds": {
                        "btc": 0.05,
                        "jpy": -2096.135
                    },
                    "pair": "btc_jpy",
                    "rate": 41922.7,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },
            ]
        }

        one_pos._update_transaction_status(position_status["transactions"])
        
        self.assertEqual(3, len(one_pos.positions))

        check_position(self, one_pos, one_pos.positions[0], 40, "buy", 0.2, 50500, 
                       datetime(year=2015,month=11,day=18,hour=8,minute=3,second=21,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[1], 38, "buy", 0.1, 40900, 
                       datetime(year=2015,month=11,day=19,hour=7,minute=2,second=21,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[2], 37, "buy", 0.05, 41922.7, 
                       datetime(year=2015,month=11,day=20,hour=6,minute=2,second=21,tzinfo=pytz.utc))

        self.assertAlmostEqual(50500*0.2 + 40900*0.1 + 41922.7*0.05, one_pos.positioned_price_base)
        self.assertAlmostEqual(0.35, one_pos.positioned_value_in_qty)
        
        # 約定時刻がほぼ同じ（10秒以内）ものは1つのポジションにまとめられるよう動作すべき

        # close order の約定によって古いやつが消えるかどうかは test_close_orderで行う
        one_pos.positions = []
        one_pos.last_checked_transaction_id = 0
        one_pos.position_id_to_sellids = {}
        one_pos.positioned_value_in_qty = 0
        one_pos.positioned_price_base    = 0
        position_status = {
            "transactions": [
                # new transaction!
                {
                    "id": 40,
                    "order_id": 1,
                    "created_at": "2015-11-18T08:03:21.000Z",
                    "funds": {
                        "btc": 0.2,
                        "jpy": -10100.0
                    },
                    "pair": "btc_jpy",
                    "rate": 50500.0,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },
                # old transaction!
                {
                    "id": 38,
                    "order_id": 1,
                    "created_at": "2015-11-18T08:03:19.000Z",
                    "funds": {
                        "btc": 0.1,
                        "jpy": -4096.135
                    },
                    "pair": "btc_jpy",
                    "rate": 40900.0,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },
                {
                    "id": 37,
                    "order_id": 1,
                    "created_at": "2015-11-20T07:02:21.000Z",
                    "funds": {
                        "btc": 0.05,
                        "jpy": -2096.135
                    },
                    "pair": "btc_jpy",
                    "rate": 41922.7,
                    "fee_currency": "JPY",
                    "fee": 6.135,
                    "liquidity": "T",
                    "side": "buy"
                },
            ]
        }
        
        one_pos._update_transaction_status(position_status["transactions"])
        
        self.assertEqual(2, len(one_pos.positions))

        check_position(self, one_pos, one_pos.positions[0], 40, "buy", 0.3, (50500*0.2+40900*0.1)/0.3, 
                       datetime(year=2015,month=11,day=18,hour=8,minute=3,second=21,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[1], 37, "buy", 0.05, 41922.7, 
                       datetime(year=2015,month=11,day=20,hour=7,minute=2,second=21,tzinfo=pytz.utc))
                       
        self.assertAlmostEqual(50500*0.2 + 40900*0.1 + 41922.7*0.05, one_pos.positioned_price_base)
        self.assertAlmostEqual(0.35, one_pos.positioned_value_in_qty)

    def test_update_orders(self):
        stoploss = 0.98
        open_rate = 0.015
        close_rate = 0.1
        decider = PriceDeciderByContinuousPositiveLine(
            cont_positive_line_count=2,
            buy_order_up_rate=open_rate,
            close_div_rate_from_buy_value=close_rate,
            stop_loss_rate=stoploss,
            close_bar_count_to_hold=3,
            do_filter_by_ma_slope=False,
            make_order_only_first_time_bar=False)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, use_leverage=False)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+2+60, 1200)
        chart.add_new_data(time_offset+2+60*2, 1250)
        chart.add_new_data(time_offset+3+60*2, 1300)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        rate = math.floor(1300*(1+open_rate))
        dummy_api.set_create_required_param_once({
            "rate": rate,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/rate),
            "stop_loss_rate": float(int(1300*stoploss)),
        })
        one_pos.update_new_orders(chart)

        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertEqual(None, one_pos.exist_close_order_info_list)
        self.assertTrue(isinstance(one_pos.exist_order_info_list[0], dict))

        order_id = one_pos.exist_order_info_list[0]["id"]

        order_status = [
            {
                "id": order_id,
                "order_type": "buy",
                "rate": rate,
                "pair": "btc_jpy",
                "pending_amount": 1.2,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "2015-01-10T05:55:38.000Z"
            },
            {
              "id": 202836,
              "order_type": "sell",
              "rate": 26990,
              "pair": "btc_jpy",
              "pending_amount": 0.77,
              "pending_market_buy_amount": None,
              "stop_loss_rate": None,
              "created_at": "2015-01-10T05:55:38.000Z"
            }
        ]
        one_pos._update_order_id_status(order_status)
        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertEqual(None, one_pos.exist_close_order_info_list)

        dummy_api.order.set_cancel_api_call_ok(False)
        dummy_api.order.set_create_api_call_ok(False)
        one_pos._update_or_create_order("long", rate, 1.2)
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        cur_id = one_pos.exist_order_info_list[0]["id"]

        order_status = [
            {
                "id": cur_id+1,
                "order_type": "buy",
                "rate": rate,
                "pair": "btc_jpy",
                "pending_amount": 1.2,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "2015-01-10T05:55:38.000Z"
            },
            {
              "id": 202836,
              "order_type": "sell",
              "rate": 26990,
              "pair": "btc_jpy",
              "pending_amount": "0.77",
              "pending_market_buy_amount": None,
              "stop_loss_rate": None,
              "created_at": "2015-01-10T05:55:38.000Z"
            }
        ]
        one_pos._update_order_id_status(order_status)
        self.assertEqual(None, one_pos.exist_order_info_list)
        self.assertEqual(None, one_pos.exist_order_info_list)
        
        # step1: new order will be come
        # step2: updated by json. new order and old order are included
        # step3:  both orders should be parsed!
        one_pos.update_new_orders(chart)
        self.assertEqual(1, len(one_pos.exist_order_info_list))
        new_id = one_pos.exist_order_info_list[0]["id"]
        self.assertNotEqual(new_id, cur_id)

        order_status = [
            {
                "id": cur_id,
                "order_type": "buy",
                "rate": 15400,
                "pair": "btc_jpy",
                "pending_amount": 1.2,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "1970-01-01T08:03:01.000Z"
            },
            {
              "id": new_id,
              "order_type": "buy",
              "rate": 26990,
              "pair": "btc_jpy",
              "pending_amount": 0.77,
              "pending_market_buy_amount": None,
              "stop_loss_rate": None,
              "created_at": "1970-01-01T08:03:01.000Z"
            }
        ]

        # zero orders
        one_pos._update_order_id_status(order_status)
        self.assertEqual(2, len(one_pos.exist_order_info_list))
        self.assertEqual(cur_id, one_pos.exist_order_info_list[0]["id"])
        self.assertEqual(new_id, one_pos.exist_order_info_list[1]["id"])
        
        one_pos.update_new_orders(chart)
        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertNotEqual(cur_id, one_pos.exist_order_info_list[0]["id"])
        self.assertNotEqual(new_id, one_pos.exist_order_info_list[0]["id"])
        
        # make positions
        transaction_status = [
            {
                "id": 40,
                "order_id": new_id,
                "created_at": "2015-11-18T08:03:21.000Z",
                "funds": {
                    "btc": 0.2,
                    "jpy": -10100.0
                },
                "pair": "btc_jpy",
                "rate": 50500.0,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
        ]
        one_pos.got_close_order_ids = [874]
        order_status = [
            {
                "id": 874,
                "order_type": "sell",
                "rate": 15400,
                "pair": "btc_jpy",
                "pending_amount": 0.2,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "1970-01-01T08:03:01.000Z"
            },
        ]
        
        one_pos._update_order_id_status(order_status)
        one_pos._update_transaction_status(transaction_status)
        
        # close order occurs
        one_pos.update_new_orders(chart)
        self.assertEqual(1, len(one_pos.positions))
        self.assertEqual(40, one_pos.positions[0]["id"])
        self.assertEqual([874], one_pos.position_id_to_sellids[40])
        self.assertEqual(1, len(one_pos.exist_close_order_info_list))
        self.assertEqual(874, one_pos.exist_close_order_info_list[0]["id"])

        
    def test_update_close_order1(self):
        stoploss = 0.98
        open_rate = 0.015
        close_rate = 0.1
        decider = PriceDeciderByContinuousPositiveLine(
            cont_positive_line_count=2,
            buy_order_up_rate=open_rate,
            close_div_rate_from_buy_value=close_rate,
            stop_loss_rate=stoploss,
            close_bar_count_to_hold=3,
            do_filter_by_ma_slope=False,
            make_order_only_first_time_bar=False)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, use_leverage=False)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+2+60, 1200)
        chart.add_new_data(time_offset+2+60*2, 1250)
        chart.add_new_data(time_offset+3+60*2, 1300)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        rate = math.floor(1300*(1+open_rate))
        dummy_api.set_create_required_param_once({
            "rate": rate,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/rate),
            "stop_loss_rate": float(int(1300*stoploss)),
        })
        one_pos.update_new_orders(chart)

        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertEqual(None, one_pos.exist_close_order_info_list)
        self.assertTrue(isinstance(one_pos.exist_order_info_list[0], dict))
        
        new_id = one_pos.exist_order_info_list[0]["id"]

        created_time_str = "2015-12-02T05:27:53.000Z"
        created_time_str2 = "2015-12-05T05:27:53.000Z"
        created_time     = datetime(year=2015,month=12,day=2,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        created_time2     = datetime(year=2015,month=12,day=5,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        open_rate_v = 43553.0
        amount = 1.5234
        transaction_status = [
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "btc": amount*2/3,
                    "jpy": -10100.0*2/3
                },
                "pair": "btc_jpy",
                "rate": open_rate_v,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
        ]
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_transaction_status(transaction_status)

        self.assertEqual(1, len(one_pos.positions))

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=29,second=3, tzinfo=pytz.utc)      
        require_params = {}
        require_params["amount"] = amount*2/3
        require_params["order_type"] = "sell"
        require_params["rate"] = float(int(open_rate_v * (1+close_rate)))
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once(require_params)
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        close_order_id1 = new_id+1
        self.assertEqual(close_order_id1, one_pos.got_close_order_ids[0])

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=50,second=0, tzinfo=pytz.utc) 
        del require_params["rate"]
        require_params["order_type"] = "market_sell"
        dummy_api.set_create_required_param_once(require_params)  # market sell is required
        dummy_api.order.set_create_not_required_param_once(["rate"])
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        close_order_id2 = new_id+2
        self.assertTrue(close_order_id2 in one_pos.got_close_order_ids)
        
        # 売り注文が約定し、positionが（一部）クローズされたことを判断できるか
        # => その後さらに買いが入り、さらにcloseされた場合に正しく対応できるか

        transaction_status = [
            {
                # close position order
                "id": 46,
                "order_id": close_order_id2,
                "created_at": created_time_str,
                "funds": {
                    "btc": -amount/6,
                    "jpy": 10100.0/6
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*(1+open_rate*2),
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # this is not relevant to this position
                "id": 45,
                "order_id": close_order_id2*2,
                "created_at": created_time_str2,
                "funds": {
                    "btc": -amount/2,
                    "jpy": 10100.0/2
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*(1+open_rate*3),
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # close position order
                "id": 43,
                "order_id": close_order_id1,
                "created_at": created_time_str2,
                "funds": {
                    "btc": -amount,
                    "jpy": 10100.0
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*(1+open_rate*2),
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # another position (will not be grouped)
                "id": 42,
                "order_id": new_id,
                "created_at": created_time_str2,
                "funds": {
                    "btc": amount/5,
                    "jpy": -10100.0/5
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*1.02,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
            {
                # 40&41 => will be grouped
                "id": 41,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "btc": amount/3,
                    "jpy": -10100.0/3
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*1.01,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "btc": amount*2/3,
                    "jpy": -10100.0*2/3
                },
                "pair": "btc_jpy",
                "rate": open_rate_v,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
        ]

        # id 40,41 がすべてcloseされ、42の一部もcloseされている状態
        one_pos._update_transaction_status(transaction_status)

        self.assertEqual(1, len(one_pos.positions))
        pos = one_pos.positions[0]
        self.assertEqual("buy", pos["side"])
        self.assertEqual(42, pos["id"])
        self.assertAlmostEqual(open_rate_v*1.02, pos["open_rate"])
        self.assertAlmostEqual(amount/5-amount/6, pos["amount"])
        
    def test_update_close_order2(self):
        stoploss = 0.98
        open_rate = 0.015
        close_rate = 0.1
        decider = PriceDeciderByContinuousPositiveLine(
            cont_positive_line_count=2,
            buy_order_up_rate=open_rate,
            close_div_rate_from_buy_value=close_rate,
            stop_loss_rate=stoploss,
            close_bar_count_to_hold=3,
            do_filter_by_ma_slope=False,
            make_order_only_first_time_bar=False)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, use_leverage=False)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+2+60, 1200)
        chart.add_new_data(time_offset+2+60*2, 1250)
        chart.add_new_data(time_offset+3+60*2, 1300)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        rate = math.floor(1300*(1+open_rate))
        one_pos.update_new_orders(chart)
        new_id = one_pos.exist_order_info_list[0]["id"]

        created_time_str = "2015-12-02T05:27:53.000Z"
        created_time_str2 = "2015-12-05T05:27:53.000Z"
        created_time     = datetime(year=2015,month=12,day=2,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        created_time2     = datetime(year=2015,month=12,day=5,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        open_rate_v = 43553.0
        amount = 1.5234
        transaction_status = [
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "btc": amount*2/3,
                    "jpy": -10100.0*2/3
                },
                "pair": "btc_jpy",
                "rate": open_rate_v,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
        ]
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_transaction_status(transaction_status)
        print("-------------")
        print("pricejpy",one_pos.positioned_price_base)
        print("-------------")
        
        self.assertEqual(1, len(one_pos.positions))

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=29,second=3, tzinfo=pytz.utc)      
        one_pos.update_close_orders(chart, check_time)
        close_order_id1 = new_id+1
        self.assertEqual(close_order_id1, one_pos.got_close_order_ids[0])

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=50,second=0, tzinfo=pytz.utc) 
        one_pos.update_close_orders(chart, check_time)
        close_order_id2 = new_id+2
        self.assertTrue(close_order_id2 in one_pos.got_close_order_ids)
        
        # 売り注文が約定し、positionが（一部）クローズされたことを判断できるか

        transaction_status = [
            {
                # close position order
                "id": 46,
                "order_id": close_order_id2,
                "created_at": created_time_str,
                "funds": {
                    "btc": -amount/6,
                    "jpy": 10100.0/6
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*(1+open_rate*2),
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # this is not relevant to this position
                "id": 45,
                "order_id": close_order_id2*2,
                "created_at": created_time_str2,
                "funds": {
                    "btc": -amount/2,
                    "jpy": 10100.0/2
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*(1+open_rate*3),
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # close position order
                "id": 43,
                "order_id": close_order_id1,
                "created_at": created_time_str2,
                "funds": {
                    "btc": -amount*7/10,
                    "jpy": 10100.0
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*(1+open_rate*2),
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # another position (will not be grouped)
                "id": 42,
                "order_id": new_id,
                "created_at": created_time_str2,
                "funds": {
                    "btc": amount/5,
                    "jpy": -10100.0/5
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*1.02,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
            {
                # 40&41 => will be grouped
                "id": 41,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "btc": amount/3,
                    "jpy": -10100.0/3
                },
                "pair": "btc_jpy",
                "rate": open_rate_v*1.01,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "btc": amount*2/3,
                    "jpy": -10100.0*2/3
                },
                "pair": "btc_jpy",
                "rate": open_rate_v,
                "fee_currency": "JPY",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
        ]

        # id 40が全てcloseされ、41は一部が約定され、42は全て残っている状態
        one_pos._update_transaction_status(transaction_status)
        
        self.assertEqual(2, len(one_pos.positions))
        pos = one_pos.positions[0]
        self.assertEqual("buy", pos["side"])
        self.assertEqual(42, pos["id"])
        self.assertAlmostEqual(open_rate_v*1.02, pos["open_rate"])
        self.assertAlmostEqual(amount/5, pos["amount"])
        
        pos = one_pos.positions[1]
        self.assertEqual("buy", pos["side"])
        self.assertEqual(41, pos["id"])
        average_rate = open_rate_v*1.01/3 + open_rate_v*2/3
        self.assertAlmostEqual(average_rate, pos["open_rate"])
        self.assertAlmostEqual(amount*2/3+amount/3-amount*7/10-amount/6, pos["amount"])

        got_margin = 1500000
        one_pos.set_max_total_position_price_base(got_margin)
        one_pos.set_max_free_margin_of_base_currency(got_margin)
        self.assertAlmostEqual(amount/5+amount*2/3+amount/3-amount*7/10-amount/6, one_pos.positioned_value_in_qty)
        expected_position_price = amount/5*open_rate_v*1.02 + amount*2/3*open_rate_v+ amount/3*open_rate_v*1.01 -(amount*7/10+amount/6)*average_rate
        self.assertAlmostEqual(expected_position_price, one_pos.positioned_price_base)
        self.assertAlmostEqual(amount/5*open_rate_v*1.02 + (amount*2/3+amount/3 -amount*7/10-amount/6)*average_rate, one_pos.positioned_price_base)

        self.assertAlmostEqual(got_margin, one_pos.get_max_total_position_price_base())

if __name__ == "__main__":
    unittest.main()

