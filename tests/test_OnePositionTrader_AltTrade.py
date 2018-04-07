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

class TestOnePositionTrader_AltTrade(unittest.TestCase):
    def create_chartbase(self):
        chart = Chart(span_minutes=1, technical_calculator=TechnicalCalculator([3]))
        return chart

    def create_dummyapi(self):
        return DummyApiForTest.ApiDummyForTest(self, _tick_price=0.0001, _tick_amount=0.001, _min_amount=0.001, is_leverage=False)

    def test_update_new_order(self):
        stoploss = 0.98
        open_rate = 0.015
        close_rate = 0.1
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=-0.1,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, pair="eth_btc", use_leverage=False)
        default_money = 0.15
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money)
        self.assertEqual(default_money, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()
        
        # no data. new order should not be ordered
        dummy_api.set_api_fail()
        dummy_api.test_create_api_must_not_be_called()
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.set_api_fail_by_none()
        self.assertFalse(one_pos.update_new_orders(chart))

        # not enough bar
        chart.add_new_data(time_offset+1+60, 0.08)
        chart.add_new_data(time_offset+1+60*2, 0.085)
        chart.add_new_data(time_offset+1+60*3, 0.088)
        dummy_api.test_create_api_must_not_be_called()
        dummy_api.set_api_fail()
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.set_api_fail_by_none()
        self.assertFalse(one_pos.update_new_orders(chart))

        # enough bar
        chart.add_new_data(time_offset+1+60*4, 0.089)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        expected_rate = (0.08+0.085+0.088)/3*0.9
        expected_rate = expected_rate - math.fmod(expected_rate, dummy_api.order.tick_price("eth_btc"))
        expected_amount = default_money/expected_rate
        expected_amount = expected_amount - math.fmod(expected_amount, dummy_api.order.tick_amount("eth_btc"))
        dummy_api.set_create_required_param_once({
            "rate": expected_rate,
            "amount": expected_amount,
            "order_type": "buy",
            "pair": "eth_btc",
        })
        self.assertTrue(one_pos.update_new_orders(chart))

        # dont request same order
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(False)
        chart.add_new_data(time_offset+2+60*4, 0.087)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        # minimum
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(dummy_api.order.min_create_amount("eth_btc")/100)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)
        
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(dummy_api.order.min_create_amount("eth_btc")/100)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money)

        # next
        chart.add_new_data(time_offset+30+60*4, 0.078)
        chart.add_new_data(time_offset+5+60*5, 0.09)
        one_pos.set_max_total_position_price_base(0.2)
        one_pos.set_max_free_margin_of_base_currency(0.1)
        expected_rate = (0.085+0.088+0.078)/3.0*0.9
        expected_rate = expected_rate - math.fmod(expected_rate, dummy_api.order.tick_price("eth_btc"))
        expected_amount = 0.1/expected_rate
        expected_amount = expected_amount - math.fmod(expected_amount, dummy_api.order.tick_amount("eth_btc"))
        dummy_api.set_create_required_param_once({
            "rate": expected_rate,
            "amount": expected_amount,
            "pair": "eth_btc",
        })
        self.assertTrue(one_pos.update_new_orders(chart))
        
    def test_update_positions(self):
        # partial contract のテストも
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=-0.1,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)

        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, pair="lsk_btc", use_leverage=False)
        one_pos.set_max_total_position_price_base(0.15)
        one_pos.set_max_free_margin_of_base_currency(0.15)
        self.assertEqual(0.15, one_pos.max_total_position_price_base)

        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 0.1)
        chart.add_new_data(time_offset+1+60, 0.12)
        chart.add_new_data(time_offset+2+60, 0.11)
        chart.add_new_data(time_offset+2+60*2, 0.085)
        chart.add_new_data(time_offset+3+60*2, 0.08)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 0.088)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()        
        rate = (0.08+0.11+0.1)/3*0.9
        rate = rate - math.fmod(rate, dummy_api.order.tick_price("lsk_btc"))
        amount = 0.15/rate
        amount = amount - math.fmod(amount, dummy_api.order.tick_amount("lsk_btc"))
        dummy_api.set_create_required_param_once({
            "rate": rate,
            "amount": amount,
            "pair": "lsk_btc",
        })
        one_pos.update_new_orders(chart)


        # "funds" must include commission fees
        position_status = {
            "transactions": [
                {
                    "id": 38,
                    "order_id": 1,
                    "created_at": "2015-11-19T07:02:21.000Z",
                    "funds": {
                        "lsk": 1.195,
                        "btc": -0.051
                    },
                    "pair": "lsk_btc",
                    "rate": 0.040,
                    "fee_currency": "LSK",
                    "fee": 0.005,
                    "liquidity": "T",
                    "side": "buy"
                },
                {
                    "id": 37,
                    "order_id": 1,
                    "created_at": "2015-11-20T06:02:21.000Z",
                    "funds": {
                        "lsk": 0.59,
                        "btc": -0.0261
                    },
                    "pair": "lsk_btc",
                    "rate": 0.041,
                    "fee_currency": "LSK",
                    "fee": 0.0051,
                    "liquidity": "T",
                    "side": "buy"
                },

            ]
        }
        one_pos.set_max_total_position_price_base(0.15)
        one_pos.set_max_free_margin_of_base_currency(0.15)
        one_pos._update_transaction_status(position_status["transactions"])

        def check_position(test, one_pos, pos, tr_id, side, amount, rate, created):
            self.assertEqual(tr_id, pos["id"])
            self.assertEqual(side, pos["side"])
            self.assertAlmostEqual(amount, pos["amount"])
            self.assertAlmostEqual(rate, pos["open_rate"])
            self.assertEqual(0, len(one_pos.position_id_to_sellids[tr_id]))
            self.assertEqual((created - pos["created_at_datetime"]).total_seconds(), 0)

        self.assertEqual(2, len(one_pos.positions))

        check_position(self, one_pos, one_pos.positions[0], 38, "buy", 1.195, 0.04 ,
                       datetime(year=2015,month=11,day=19,hour=7,minute=2,second=21,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[1], 37, "buy", 0.59, 0.041 ,
                       datetime(year=2015,month=11,day=20,hour=6,minute=2,second=21,tzinfo=pytz.utc))
        self.assertAlmostEqual(1.195*0.04  + 0.59*0.041, one_pos.positioned_price_base)
        self.assertAlmostEqual(1.195+0.59, one_pos.positioned_value_in_qty)

        position_status = {
            "transactions": [
                # new transaction!
                {
                    "id": 40,
                    "order_id": 1,
                    "created_at": "2015-11-20T08:03:21.000Z",
                    "funds": {
                        "lsk": 0.2,
                        "btc": -0.0088
                    },
                    "pair": "lsk_btc",
                    "rate": 0.045,
                    "fee_currency": "LSK",
                    "fee": 0.0008,
                    "liquidity": "T",
                    "side": "buy"
                },
                # not relevant transaction
                {
                    "id": 42,
                    "order_id": 1,
                    "created_at": "2015-11-21T08:03:21.000Z",
                    "funds": {
                        "neo": 0.2,
                        "btc": -0.0088
                    },
                    "pair": "neo_btc",
                    "rate": 0.045,
                    "fee_currency": "NEO",
                    "fee": 0.0008,
                    "liquidity": "T",
                    "side": "buy"
                },
                # old transaction!
                {
                    "id": 38,
                    "order_id": 1,
                    "created_at": "2015-11-19T07:02:21.000Z",
                    "funds": {
                        "lsk": 1.195,
                        "btc": -0.051
                    },
                    "pair": "lsk_btc",
                    "rate": 0.040,
                    "fee_currency": "LSK",
                    "fee": 0.005,
                    "liquidity": "T",
                    "side": "buy"
                },
                {
                    "id": 37,
                    "order_id": 1,
                    "created_at": "2015-11-20T06:02:21.000Z",
                    "funds": {
                        "lsk": 0.59,
                        "btc": -0.0261
                    },
                    "pair": "lsk_btc",
                    "rate": 0.041,
                    "fee_currency": "LSK",
                    "fee": 0.0051,
                    "liquidity": "T",
                    "side": "buy"
                },
            ]
        }

        one_pos._update_transaction_status(position_status["transactions"])
        
        self.assertEqual(3, len(one_pos.positions))

        check_position(self, one_pos, one_pos.positions[0], 40, "buy", 0.2, 0.045, 
                       datetime(year=2015,month=11,day=20,hour=8,minute=3,second=21,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[1], 38, "buy", 1.195, 0.04 ,
                       datetime(year=2015,month=11,day=19,hour=7,minute=2,second=21,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[2], 37, "buy", 0.59, 0.041 ,
                       datetime(year=2015,month=11,day=20,hour=6,minute=2,second=21,tzinfo=pytz.utc))

        self.assertAlmostEqual(1.195*0.04  + 0.59*0.041 + 0.2*0.045, one_pos.positioned_price_base)
        self.assertAlmostEqual(1.195+0.59+0.2, one_pos.positioned_value_in_qty)

        # near transaction がまとめられるかどうか
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
                    "created_at": "2015-11-19T07:02:22.000Z",
                    "funds": {
                        "lsk": 0.2,
                        "btc": -0.0088
                    },
                    "pair": "lsk_btc",
                    "rate": 0.045,
                    "fee_currency": "LSK",
                    "fee": 0.0008,
                    "liquidity": "T",
                    "side": "buy"
                },
                # not relevant transaction
                {
                    "id": 42,
                    "order_id": 1,
                    "created_at": "2015-11-21T08:03:21.000Z",
                    "funds": {
                        "neo": 0.2,
                        "btc": -0.0088
                    },
                    "pair": "neo_btc",
                    "rate": 0.045,
                    "fee_currency": "NEO",
                    "fee": 0.0008,
                    "liquidity": "T",
                    "side": "buy"
                },
                # old transaction!
                {
                    "id": 38,
                    "order_id": 1,
                    "created_at": "2015-11-19T07:02:21.000Z",
                    "funds": {
                        "lsk": 1.195,
                        "btc": -0.051
                    },
                    "pair": "lsk_btc",
                    "rate": 0.040,
                    "fee_currency": "LSK",
                    "fee": 0.005,
                    "liquidity": "T",
                    "side": "buy"
                },
                {
                    "id": 37,
                    "order_id": 1,
                    "created_at": "2015-11-20T06:02:21.000Z",
                    "funds": {
                        "lsk": 0.59,
                        "btc": -0.0261
                    },
                    "pair": "lsk_btc",
                    "rate": 0.041,
                    "fee_currency": "LSK",
                    "fee": 0.0051,
                    "liquidity": "T",
                    "side": "buy"
                },
            ]
        }
        
        one_pos._update_transaction_status(position_status["transactions"])
        
        self.assertEqual(2, len(one_pos.positions))

        check_position(self, one_pos, one_pos.positions[0], 40, "buy", 0.2+1.195, (0.045*0.2+0.04*1.195)/(0.2+1.195), 
                       datetime(year=2015,month=11,day=19,hour=7,minute=2,second=22,tzinfo=pytz.utc))
        check_position(self, one_pos, one_pos.positions[1], 37, "buy", 0.59, 0.041, 
                       datetime(year=2015,month=11,day=20,hour=6,minute=2,second=21,tzinfo=pytz.utc))
                       
        self.assertAlmostEqual(0.045*0.2+0.04*1.195 + 0.59*0.041, one_pos.positioned_price_base)
        self.assertAlmostEqual(0.2+1.195+0.59, one_pos.positioned_value_in_qty)

    def test_update_orders(self):
        open_rate = -0.1
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=open_rate,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)

        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, pair="lsk_btc", use_leverage=False)
        
        one_pos.set_max_total_position_price_base(1.5)
        one_pos.set_max_free_margin_of_base_currency(1.5)
        self.assertEqual(1.5, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 0.006)
        chart.add_new_data(time_offset+1+60, 0.0061)
        chart.add_new_data(time_offset+2+60, 0.0068)
        chart.add_new_data(time_offset+2+60*2, 0.0059)
        chart.add_new_data(time_offset+3+60*2, 0.0057)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 0.0055)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        rate = (0.0057+0.0068+0.006)/3*(1+open_rate)
        rate = rate - math.fmod(rate, dummy_api.order.tick_price("lsk_btc"))
        amount = one_pos.max_total_position_price_base / rate
        amount = amount - math.fmod(amount, dummy_api.order.tick_amount("lsk_btc"))
        dummy_api.set_create_required_param_once({
            "rate": rate,
            "amount": amount,
            "pair": "lsk_btc",
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
                "rate": "%.9f" % rate,
                "pair": "lsk_btc",
                "pending_amount": "%.9f" % amount,
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
        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertEqual(None, one_pos.exist_close_order_info_list)

        dummy_api.order.set_cancel_api_call_ok(False)
        dummy_api.order.set_create_api_call_ok(False)
        one_pos._update_or_create_order("long", rate, amount)
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        cur_id = one_pos.exist_order_info_list[0]["id"]

        # buy order disappear (sold or canceled)
        order_status = [
            {
                "id": cur_id+1,
                "order_type": "buy",
                "rate": rate,
                "pair": "lsk_btc",
                "pending_amount": "1.2",
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "2015-01-10T05:55:38.000Z"
            },
            {
              "id": 202836,
              "order_type": "sell",
              "rate": 26990,
              "pair": "lsk_btc",
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
                "pair": "lsk_btc",
                "pending_amount": 1.2,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "1970-01-01T08:03:01.000Z"
            },
            {
              "id": new_id,
              "order_type": "buy",
              "rate": 0.04,
              "pair": "lsk_btc",
              "pending_amount": 0.77,
              "pending_market_buy_amount": None,
              "stop_loss_rate": None,
              "created_at": "1970-01-01T08:03:01.000Z"
            },
            # this should be ignored (not lsk_btc)
            {
              "id": new_id,
              "order_type": "buy",
              "rate": 0.0234,
              "pair": "neo_btc",
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
        
        # order new order (old orders will be canceled)
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
                    "lsk": 0.385,
                    "btc": -0.0153,
                },
                "pair": "lsk_btc",
                "rate": 0.04,
                "fee_currency": "LSK",
                "fee": 0.0001,
                "liquidity": "T",
                "side": "buy"
            },
        ]
        one_pos.got_close_order_ids = [874]
        order_status = [
            {
                "id": 874,
                "order_type": "sell",
                "rate": 0.05,
                "pair": "lsk_btc",
                "pending_amount": 0.385,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "2018-01-01T08:03:01.000Z"
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
        self.assertAlmostEqual(0.05, one_pos.exist_close_order_info_list[0]["rate"])
        self.assertAlmostEqual(0.385, one_pos.exist_close_order_info_list[0]["amount"])
        self.assertEqual("lsk_btc", one_pos.exist_close_order_info_list[0]["pair"])
        
    def test_update_close_order1(self):
        open_rate = -0.1
        close_rate = 0.1
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=open_rate,
                                   sell_div_rate_from_buy_value=close_rate,
                                   sell_bar_count_to_hold=5)

                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api, pair="xvg_btc", use_leverage=False)
        
        default_money = 1.5
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money)
        self.assertEqual(default_money, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 0.008)
        chart.add_new_data(time_offset+1+60, 0.0087)
        chart.add_new_data(time_offset+2+60, 0.0082)
        chart.add_new_data(time_offset+2+60*2, 0.0079)
        chart.add_new_data(time_offset+3+60*2, 0.0061)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 0.0069)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        rate = (0.0061+0.0082+0.008)/3*(1+open_rate)
        rate = rate - math.fmod(rate, dummy_api.order.tick_price("xvg_btc"))
        amount = default_money / rate
        amount = amount - math.fmod(amount, dummy_api.order.tick_amount("xvg_btc"))
        dummy_api.set_create_required_param_once({
            "rate": rate,
            "amount": amount,
            "pair": "xvg_btc",
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
        open_rate_v = rate
        
        transaction_status = [
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "xvg": amount*2/3,
                    "btc": -rate*amount*2/3
                },
                "pair": "xvg_btc",
                "rate": open_rate_v,
                "fee_currency": "XVG",
                "fee": 0.0135,
                "liquidity": "T",
                "side": "buy"
            },
        ]
        one_pos.set_max_total_position_price_base(1.5)
        one_pos._update_transaction_status(transaction_status)

        self.assertEqual(1, len(one_pos.positions))

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=29,second=3, tzinfo=pytz.utc)      
        require_params = {}
        require_params["amount"] = amount*2/3
        require_params["order_type"] = "sell"
        close_rate_v = open_rate_v * (1+close_rate)
        close_rate_v = close_rate_v - math.fmod(close_rate_v, dummy_api.order.tick_price("xvg_btc"))
        require_params["rate"] = close_rate_v
        require_params["pair"] = "xvg_btc"
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
        
        # 売り注文が約定し、positionが（一部）クローズされたことを判断できるかテスト
        # => その後さらに買いが入り、さらにcloseされた場合に正しく対応できるかテスト

        transaction_status = [
            {
                # close position order
                "id": 46,
                "order_id": close_order_id2,
                "created_at": created_time_str,
                "funds": {
                    "xvg": -amount/6,
                    "btc": amount*rate/6
                },
                "pair": "xvg_btc",
                "rate": open_rate_v*(1+open_rate*2),
                "fee_currency": "BTC",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # this id is not relevant to this position
                "id": 45,
                "order_id": close_order_id2*2,
                "created_at": created_time_str2,
                "funds": {
                    "xvg": -amount/2,
                    "btc": amount*rate/2
                },
                "pair": "xvg_btc",
                "rate": open_rate_v*(1+open_rate*3),
                "fee_currency": "BTC",
                "fee": 6.135,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # this pair is not relevant to this position (this is impossible but we perform test)
                "id": 47,
                "order_id": close_order_id2,
                "created_at": created_time_str2,
                "funds": {
                    "lsk": -amount/2,
                    "btc": amount*rate/2
                },
                "pair": "lsk_btc",
                "rate": open_rate_v*(1+open_rate*3),
                "fee_currency": "BTC",
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
                    "xvg": -amount,
                    "btc": 10100.0
                },
                "pair": "xvg_btc",
                "rate": open_rate_v*(1+open_rate*2),
                "fee_currency": "BTC",
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
                    "xvg": amount/5,
                    "btc": -amount*rate/5
                },
                "pair": "xvg_btc",
                "rate": open_rate_v*1.02,
                "fee_currency": "XVG",
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
                    "xvg": amount/3,
                    "btc": -amount*rate/3
                },
                "pair": "xvg_btc",
                "rate": open_rate_v*1.01,
                "fee_currency": "XVG",
                "fee": 6.135,
                "liquidity": "T",
                "side": "buy"
            },
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "xvg": amount*2/3,
                    "btc": -amount*rate*2/3
                },
                "pair": "xvg_btc",
                "rate": open_rate_v,
                "fee_currency": "XVG",
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
        open_rate = -0.1
        close_rate = 0.1
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=open_rate,
                                   sell_div_rate_from_buy_value=close_rate,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        pair="eth_btc"
        one_pos = OnePositionTrader(decider, dummy_api, pair=pair, use_leverage=False)
        default_money = 0.25
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 0.12)
        chart.add_new_data(time_offset+1+60, 0.11)
        chart.add_new_data(time_offset+2+60, 0.105)
        chart.add_new_data(time_offset+2+60*2, 0.098)
        chart.add_new_data(time_offset+3+60*2, 0.0999)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 0.0975)
        rate = (0.0999+0.105+0.12)/3*(1+open_rate)
        rate = rate - math.fmod(rate, dummy_api.order.tick_price(pair))
        max_amount = default_money / rate
        max_amount = max_amount - math.fmod(max_amount, dummy_api.order.tick_amount(pair))
        one_pos.update_new_orders(chart)
        new_id = one_pos.exist_order_info_list[0]["id"]

        created_time_str = "2015-12-02T05:27:53.000Z"
        created_time_str2 = "2015-12-05T05:27:53.000Z"
        created_time     = datetime(year=2015,month=12,day=2,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        created_time2     = datetime(year=2015,month=12,day=5,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        open_rate_v = rate*(1+open_rate)
        amount = max_amount/2
        transaction_status = [
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "eth": amount*2/3,
                    "btc": -open_rate_v*amount*2/3
                },
                "pair": pair,
                "rate": open_rate_v,
                "fee_currency": "ETH",
                "fee": 0.001,
                "liquidity": "T",
                "side": "buy"
            },
        ]
        one_pos._update_transaction_status(transaction_status)
        
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
                    "eth": -amount/6,
                    "btc": open_rate_v*amount/6
                },
                "pair": pair,
                "rate": open_rate_v*(1+close_rate*2),
                "fee_currency": "BTC",
                "fee": 0.0001,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # this is not relevant to this position
                "id": 45,
                "order_id": close_order_id2*2,
                "created_at": created_time_str2,
                "funds": {
                    "eth": -amount/2,
                    "btc": open_rate_v*amount/2
                },
                "pair": pair,
                "rate": open_rate_v*(1+close_rate*3),
                "fee_currency": "BTC",
                "fee": 0.0003,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # close position order
                "id": 43,
                "order_id": close_order_id1,
                "created_at": created_time_str2,
                "funds": {
                    "eth": -amount*7/10,
                    "btc": open_rate_v*amount*7/10,
                },
                "pair": pair,
                "rate": open_rate_v*(1+open_rate*2),
                "fee_currency": "BTC",
                "fee": 0.001,
                "liquidity": "M",
                "side": "sell"
            },
            {
                # another position (will not be grouped)
                "id": 42,
                "order_id": new_id,
                "created_at": created_time_str2,
                "funds": {
                    "eth": amount/5,
                    "btc": -open_rate_v*amount/5
                },
                "pair":pair,
                "rate": open_rate_v*1.02,
                "fee_currency": "ETH",
                "fee": 0.001,
                "liquidity": "T",
                "side": "buy"
            },
            {
                # 40&41 => will be grouped
                "id": 41,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "eth": amount/3,
                    "btc": -open_rate_v*amount/3
                },
                "pair": pair,
                "rate": open_rate_v*1.01,
                "fee_currency": "ETH",
                "fee": 0.001,
                "liquidity": "T",
                "side": "buy"
            },
            {
                "id": 40,
                "order_id": new_id,
                "created_at": created_time_str,
                "funds": {
                    "eth": amount*2/3,
                    "btc": -open_rate_v*amount/3
                },
                "pair": pair,
                "rate": open_rate_v,
                "fee_currency": "ETH",
                "fee": 0.001,
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

        got_margin = 0.2
        one_pos.set_max_total_position_price_base(got_margin)
        self.assertAlmostEqual(amount/5+amount*2/3+amount/3-amount*7/10-amount/6, one_pos.positioned_value_in_qty)
        expected_position_price = amount/5*open_rate_v*1.02 + amount*2/3*open_rate_v+ amount/3*open_rate_v*1.01 -(amount*7/10+amount/6)*average_rate
        self.assertAlmostEqual(expected_position_price, one_pos.positioned_price_base)
        self.assertAlmostEqual(amount/5*open_rate_v*1.02 + (amount*2/3+amount/3 -amount*7/10-amount/6)*average_rate, one_pos.positioned_price_base)

        self.assertAlmostEqual(got_margin, one_pos.get_max_total_position_price_base())

if __name__ == "__main__":
    unittest.main()

