# coding: utf-8
import unittest
import random
from datetime import datetime
import pytz
import json
from real_trade.ChartBars import Chart
from real_trade.Algorithm_PriceDeciderByMA import PriceDeciderByMA
from real_trade.Algorithm_PriceDeciderByContinuousPositiveLine import PriceDeciderByContinuousPositiveLine
from real_trade.TechnicalCalculator import TechnicalCalculator
from real_trade.MoveAverageTradePosition import OnePositionTrader
from real_trade.Util import BitcoinUtil

from tests import DummyApiForTest

time_offset = 10000*60

class TestOnePositionTrader(unittest.TestCase):
    def create_chartbase(self):
        chart = Chart(span_minutes=1, technical_calculator=TechnicalCalculator([3]))
        return chart

    def create_dummyapi(self):
        return DummyApiForTest.ApiDummyForTest(self, _tick_price=1.0, _tick_amount=0.00000001, _min_amount=0.005, is_leverage=True)

    def test_update_new_order(self):
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=-0.1,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        default_money = 100000
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
        chart.add_new_data(time_offset+1+60, 1000)
        chart.add_new_data(time_offset+1+60*2, 1100)
        chart.add_new_data(time_offset+1+60*3, 1200)
        dummy_api.test_create_api_must_not_be_called()
        dummy_api.set_api_fail()
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.set_api_fail_by_none()
        self.assertFalse(one_pos.update_new_orders(chart))

        # enough bar
        chart.add_new_data(time_offset+1+60*4, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": (1000+1100+1200)/3*0.9,
            "amount": BitcoinUtil.roundBTCby1satoshi(default_money/((1000+1100+1200)/3*0.9)),
            "order_type": "leverage_buy",
        })
        self.assertTrue(one_pos.update_new_orders(chart))

        # dont request same order
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(False)
        chart.add_new_data(time_offset+2+60*4, 1050)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        # minimum
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(2)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)
        
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(2)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money)

        # next
        chart.add_new_data(time_offset+30+60*4, 900)
        chart.add_new_data(time_offset+5+60*5, 1500)
        one_pos.set_max_total_position_price_base(90000)
        one_pos.set_max_free_margin_of_base_currency(70000)
        dummy_api.set_create_required_param_once({
            "rate": float(int((900+1100+1200)/3.0*0.9)),
            "amount": BitcoinUtil.roundBTCby1satoshi(70000.0/int((900+1100+1200)/3.0*0.9)),
        })
        self.assertTrue(one_pos.update_new_orders(chart))

    def test_update_new_order_stoploss(self):
        decider = PriceDeciderByContinuousPositiveLine(
            cont_positive_line_count=2,
            buy_order_up_rate=0.1,
            close_div_rate_from_buy_value=0.1,
            stop_loss_rate=0.98,
            close_bar_count_to_hold=3,
            do_filter_by_ma_slope=False)

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
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.set_api_fail_by_none()
        self.assertFalse(one_pos.update_new_orders(chart))

        # not enough bar
        # enough bar
        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+2, 1050)
        chart.add_new_data(time_offset+1+60, 1050)
        chart.add_new_data(time_offset+2+60, 1100)
        chart.add_new_data(time_offset+1+60*2, 1100)
        chart.add_new_data(time_offset+2+60*2, 1200)
        
        dummy_api.order.reset_called_count()
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": 1100*1.1,
            "amount": BitcoinUtil.roundBTCby1satoshi(default_money/(1100*1.1)),
            "order_type": "buy",
            "stop_loss_rate": float(int(1100*0.98)),
        })
        self.assertTrue(one_pos.update_new_orders(chart))
        self.assertEqual(1, dummy_api.order.get_create_called_count())

    def test_update_new_short_order(self):
        open_div_rate = 0.1
        close_div_rate = -0.1
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=open_div_rate,
                                   sell_div_rate_from_buy_value=close_div_rate,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        default_money = 100000
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
        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+1+60*2, 1200)
        dummy_api.test_create_api_must_not_be_called()
        dummy_api.set_api_fail()
        dummy_api.order.set_create_api_call_ok(False)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.set_api_fail_by_none()
        self.assertFalse(one_pos.update_new_orders(chart))

        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.order.set_create_api_call_ok(True)
        expected_rate = float(int((1000+1100+1200)/3*(1+open_div_rate)))
        dummy_api.set_create_required_param_once({
            "rate": expected_rate,
            "amount": BitcoinUtil.roundBTCby1satoshi(default_money/expected_rate),
            "order_type": "leverage_sell",
        })
        self.assertTrue(one_pos.update_new_orders(chart))

        # dont request same order
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(False)
        chart.add_new_data(time_offset+2+60*3, 1050)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        # minimum
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(2)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(True)
        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(2)
        self.assertFalse(one_pos.update_new_orders(chart))
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        one_pos.set_max_total_position_price_base(default_money)
        one_pos.set_max_free_margin_of_base_currency(default_money)

        # next
        chart.add_new_data(time_offset+30+60*3, 900)
        dummy_api.set_api_success()
        expected_rate = float(int((1000+1100+1200)/3*(1+open_div_rate)))
        dummy_api.set_create_required_param_once({
            "rate": expected_rate,
            "amount": BitcoinUtil.roundBTCby1satoshi(default_money/expected_rate),
            "order_type": "leverage_sell",
        })
        self.assertFalse(one_pos.update_new_orders(chart))
        
        chart.add_new_data(time_offset+5+60*4, 1500)
        one_pos.set_max_total_position_price_base(90000)
        one_pos.set_max_free_margin_of_base_currency(90000)
        expected_rate = float(int((900+1100+1200)/3.0*(1+open_div_rate)))
        dummy_api.set_create_required_param_once({
            "rate": expected_rate,
            "amount": BitcoinUtil.roundBTCby1satoshi(90000.0/expected_rate),
            "order_type": "leverage_sell",
        })
        self.assertTrue(one_pos.update_new_orders(chart))
        
    def test_cancel(self):
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=-0.1,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        dummy_api.order.create({"amount":1, "order_type":"leverage_buy", "pair": "btc_jpy"})
        dummy_api.order.create({"amount":1, "order_type":"leverage_buy", "pair": "btc_jpy"})
        dummy_api.order.create({"amount":1, "order_type":"leverage_buy", "pair": "btc_jpy"})

        one_pos = OnePositionTrader(decider, dummy_api)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)

        dummy_api.set_api_success()
        self.assertTrue(one_pos._cancel_order(1))

        dummy_api.set_api_fail()
        self.assertFalse(one_pos._cancel_order(2))
        
        dummy_api.set_api_fail_by_none()
        self.assertFalse(one_pos._cancel_order(3))

        dummy_api.order.set_cancel_api_call_ok(False)
        self.assertTrue(one_pos._cancel_order(None))

    def test_update_positions(self):

        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=-0.1,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()
        

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+1+60*2, 1200)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": (1000+1100+1200)/3*0.9,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/((1000+1100+1200)/3*0.9)),
        })
        one_pos.update_new_orders(chart)

        position_status = {
            "data": [
                {
                    "id":10,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": "2015-12-02T05:27:53.000Z",
                    "closed_at": None,
                    "amount": 1.5275,
                    "all_amount": 1.51,
                    "open_rate": 43553.0,
                    "side": "buy",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "buy",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 100,
                            "side": "sell",
                            "status": "cancel",
                        },
                        {
                            "id": 1010,
                            "side": "sell",
                            "status": "open",
                        }
                    ]
                },
                {
                    "id":12,
                    "pair": "btc_jpy",
                    "status": "closed",
                    "created_at": "2015-12-02T05:27:53.000Z",
                    "closed_at": None,
                    "amount": 1.5275,
                    "all_amount": 1.51,
                    "open_rate": 43553.0,
                    "side": "buy",
                    "pl": -1500,
                    "new_order": {
                        "id": 3,
                        "side": "buy",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 102,
                            "side": "sell",
                            "status": "cancel",
                        }
                    ]
                },
                {
                    "id":15,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": "2017-01-02T05:34:53.000Z",
                    "closed_at": None,
                    "amount": 1.5075,
                    "all_amount": 1.51,
                    "open_rate": 43453.0,
                    "side": "buy",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "sell",
                        "status": "complete",
                        "created_at": "2017-01-02T05:34:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 100,
                            "side": "buy",
                            "status": "open",
                        },
                        {
                            "id": 1010,
                            "side": "buy",
                            "status": "cancel",
                        }
                    ]
                },
                {
                    "id":11,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": "2015-12-02T05:27:53.000Z",
                    "closed_at": None,
                    "amount": 1.5275,
                    "all_amount": 1.51,
                    "open_rate": 43553.0,
                    "side": "buy",
                    "pl": -1500,
                    "new_order": {
                        "id": 3,
                        "side": "buy",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 101,
                            "side": "sell",
                            "status": "cancel",
                        }
                    ]
                }
            ]
        }
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_position_status(position_status["data"])
        
        self.assertEqual(2, len(one_pos.positions))
        self.assertEqual(10, one_pos.positions[0]["id"])
        self.assertEqual("buy", one_pos.positions[0]["side"])
        self.assertEqual(1.51, one_pos.positions[0]["amount"])
        self.assertEqual(1.51, one_pos.positions[0]["all_amount"])
        self.assertEqual(43553.0, one_pos.positions[0]["open_rate"])
        self.assertTrue(10 in one_pos.position_id_to_sellids)
        self.assertEqual([1010], one_pos.position_id_to_sellids[10])
        self.assertEqual((datetime(year=2015,month=12,day=2,hour=5,minute=27,second=53,tzinfo=pytz.utc) - one_pos.positions[0]["created_at_datetime"]).total_seconds(), 0)

        self.assertEqual(15, one_pos.positions[1]["id"])
        self.assertEqual("buy", one_pos.positions[1]["side"])
        self.assertEqual(1.5075, one_pos.positions[1]["amount"])
        self.assertEqual(1.5075, one_pos.positions[1]["all_amount"])
        self.assertEqual(43453.0, one_pos.positions[1]["open_rate"])
        self.assertTrue(15 in one_pos.position_id_to_sellids)
        self.assertEqual([100], one_pos.position_id_to_sellids[15])
        self.assertEqual((datetime(year=2017,month=1,day=2,hour=5,minute=34,second=53,tzinfo=pytz.utc) - one_pos.positions[1]["created_at_datetime"]).total_seconds(), 0)

        self.assertAlmostEqual(43553*1.51 + 43453*1.5075, one_pos.positioned_price_base)

    def test_update_short_positions(self):

        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=0.1,
                                   sell_div_rate_from_buy_value=-0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()
        

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+1+60*2, 1200)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": (1000+1100+1200)/3*1.1,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/((1000+1100+1200)/3*1.1)),
            "order_type": "leverage_sell",
        })
        one_pos.update_new_orders(chart)

        position_status = {
            "data": [
                {
                    "id":10,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": "2015-12-02T05:27:53.000Z",
                    "closed_at": None,
                    "amount": 1.5275,
                    "all_amount": 1.51,
                    "open_rate": 43553.0,
                    "side": "sell",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "sell",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 100,
                            "side": "buy",
                            "status": "cancel",
                        },
                        {
                            "id": 1010,
                            "side": "buy",
                            "status": "open",
                        }
                    ]
                },
                {
                    "id":12,
                    "pair": "btc_jpy",
                    "status": "closed",
                    "created_at": "2015-12-02T05:27:53.000Z",
                    "closed_at": None,
                    "amount": 1.5275,
                    "all_amount": 1.51,
                    "open_rate": 43553.0,
                    "side": "sell",
                    "pl": -1500,
                    "new_order": {
                        "id": 3,
                        "side": "sell",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 102,
                            "side": "buy",
                            "status": "cancel",
                        }
                    ]
                },
                {
                    "id":15,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": "2017-01-02T05:34:53.000Z",
                    "closed_at": None,
                    "amount": 1.5075,
                    "all_amount": 1.51,
                    "open_rate": 43453.0,
                    "side": "sell",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "sell",
                        "status": "complete",
                        "created_at": "2017-01-02T05:34:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 100,
                            "side": "buy",
                            "status": "open",
                        },
                        {
                            "id": 1010,
                            "side": "buy",
                            "status": "cancel",
                        }
                    ]
                },
                {
                    "id":11,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": "2015-12-02T05:27:53.000Z",
                    "closed_at": None,
                    "amount": 1.5275,
                    "all_amount": 1.51,
                    "open_rate": 43553.0,
                    "side": "sell",
                    "pl": -1500,
                    "new_order": {
                        "id": 3,
                        "side": "sell",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 101,
                            "side": "buy",
                            "status": "cancel",
                        }
                    ]
                }
            ]
        }
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_position_status(position_status["data"])
        
        self.assertEqual(2, len(one_pos.positions))
        self.assertEqual(10, one_pos.positions[0]["id"])
        self.assertEqual(1.51, one_pos.positions[0]["amount"])
        self.assertEqual("sell", one_pos.positions[0]["side"])
        self.assertEqual(1.51, one_pos.positions[0]["all_amount"])
        self.assertEqual(43553.0, one_pos.positions[0]["open_rate"])
        self.assertTrue(10 in one_pos.position_id_to_sellids)
        self.assertEqual([1010], one_pos.position_id_to_sellids[10])
        self.assertEqual((datetime(year=2015,month=12,day=2,hour=5,minute=27,second=53,tzinfo=pytz.utc) - one_pos.positions[0]["created_at_datetime"]).total_seconds(), 0)

        self.assertEqual(15, one_pos.positions[1]["id"])
        self.assertEqual("sell", one_pos.positions[1]["side"])
        self.assertEqual(1.5075, one_pos.positions[1]["amount"])
        self.assertEqual(1.5075, one_pos.positions[1]["all_amount"])
        self.assertEqual(43453.0, one_pos.positions[1]["open_rate"])
        self.assertTrue(15 in one_pos.position_id_to_sellids)
        self.assertEqual([100], one_pos.position_id_to_sellids[15])
        self.assertEqual((datetime(year=2017,month=1,day=2,hour=5,minute=34,second=53,tzinfo=pytz.utc) - one_pos.positions[1]["created_at_datetime"]).total_seconds(), 0)

        self.assertAlmostEqual(43553*1.51 + 43453*1.5075, one_pos.positioned_price_base)


    def test_update_orders(self):
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=-0.1,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+1+60*2, 1200)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": (1000+1100+1200)/3*0.9,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/((1000+1100+1200)/3*0.9)),
        })
        one_pos.update_new_orders(chart)
        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertTrue(isinstance(one_pos.exist_order_info_list[0], dict))

        order_id = one_pos.exist_order_info_list[0]["id"]

        order_status = [
            {
                "id": order_id,
                "order_type": "buy",
                "rate": (1000+1100+1200)/3*0.9,
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
        self.assertEqual(1, len(one_pos.exist_order_info_list))

        dummy_api.order.set_cancel_api_call_ok(False)
        dummy_api.order.set_create_api_call_ok(False)
        one_pos._update_or_create_order("long", (1000+1100+1200)/3*0.9, 1.2)
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        cur_id = one_pos.exist_order_info_list[0]["id"]

        order_status = [
            {
                "id": cur_id+1,
                "order_type": "buy",
                "rate": (1000+1100+1200)/3*0.9,
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
                "rate": (1000+1100+1200)/3*0.9,
                "pair": "btc_jpy",
                "pending_amount": 1.2,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "2015-01-10T05:55:38.000Z"
            },
            {
              "id": new_id,
              "order_type": "buy",
              "rate": 26990,
              "pair": "btc_jpy",
              "pending_amount": 0.77,
              "pending_market_buy_amount": None,
              "stop_loss_rate": None,
              "created_at": "2015-01-10T05:55:38.000Z"
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

    def test_update_short_orders(self):
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=0.1,
                                   sell_div_rate_from_buy_value=-0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = self.create_chartbase()

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+60, 1100)
        chart.add_new_data(time_offset+1+60*2, 1200)
        # enough bar
        chart.add_new_data(time_offset+1+60*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": (1000+1100+1200)/3*1.1,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/((1000+1100+1200)/3*1.1)),
            "order_type": "leverage_sell",
        })
        one_pos.update_new_orders(chart)
        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertTrue(isinstance(one_pos.exist_order_info_list[0], dict))

        order_id = one_pos.exist_order_info_list[0]["id"]

        order_status = [
            {
                "id": order_id,
                "order_type": "sell",
                "rate": (1000+1100+1200)/3*1.1,
                "pair": "btc_jpy",
                "pending_amount": 1.2,
                "pending_market_sell_amount": None,
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

        dummy_api.order.set_cancel_api_call_ok(False)
        dummy_api.order.set_create_api_call_ok(False)
        one_pos._update_or_create_order("short", (1000+1100+1200)/3*1.1, 1.2)
        dummy_api.order.set_create_api_call_ok(True)
        dummy_api.order.set_cancel_api_call_ok(True)

        cur_id = one_pos.exist_order_info_list[0]["id"]

        order_status = [
            {
                "id": cur_id+1,
                "order_type": "sell",
                "rate": (1000+1100+1200)/3*1.1,
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
                "order_type": "sell",
                "rate": (1000+1100+1200)/3*1.1,
                "pair": "btc_jpy",
                "pending_amount": 1.2,
                "pending_market_buy_amount": None,
                "stop_loss_rate": None,
                "created_at": "2015-01-10T05:55:38.000Z"
            },
            {
              "id": new_id,
              "order_type": "sell",
              "rate": 26990,
              "pair": "btc_jpy",
              "pending_amount": 0.77,
              "pending_market_buy_amount": None,
              "stop_loss_rate": None,
              "created_at": "2015-01-10T05:55:38.000Z"
            }
        ]

        # zero orders
        one_pos._update_order_id_status(order_status)
        self.assertEqual(2, len(one_pos.exist_order_info_list))
        self.assertEqual(cur_id, one_pos.exist_order_info_list[0]["id"])
        self.assertEqual(new_id, one_pos.exist_order_info_list[1]["id"])
        self.assertEqual("sell", one_pos.exist_order_info_list[0]["order_type"])
        self.assertEqual("sell", one_pos.exist_order_info_list[1]["order_type"])

        one_pos.update_new_orders(chart)
        self.assertEqual(1, len(one_pos.exist_order_info_list))
        self.assertNotEqual(cur_id, one_pos.exist_order_info_list[0]["id"])
        self.assertNotEqual(new_id, one_pos.exist_order_info_list[0]["id"])
        
        
    def test_update_close_order(self):
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=-0.1,
                                   sell_div_rate_from_buy_value=0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = Chart(span_minutes=5, technical_calculator=TechnicalCalculator([3]))

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+300, 1100)
        chart.add_new_data(time_offset+1+300*2, 1200)
        # enough bar
        chart.add_new_data(time_offset+1+300*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": (1000+1100+1200)/3*0.9,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/((1000+1100+1200)/3*0.9)),
        })
        one_pos.update_new_orders(chart)

        created_time_str = "2015-12-02T05:27:53.000Z"
        created_time     = datetime(year=2015,month=12,day=2,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        open_rate = 43553.0
        amount = 1.5234
        position_status = {
            "data": [
                {
                    "id":10,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": created_time_str,
                    "closed_at": None,
                    "amount": amount,
                    "all_amount": amount,
                    "open_rate": open_rate,
                    "side": "buy",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "buy",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 100,
                            "side": "sell",
                            "status": "cancel",
                        },
                    ]
                }
            ]
        }
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_position_status(position_status["data"])

        self.assertEqual(1, len(one_pos.positions))

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=30,second=3, tzinfo=pytz.utc)      
        require_params = {}
        require_params["amount"] = amount
        require_params["order_type"] = "close_long"
        require_params["position_id"] = 10
        require_params["rate"] = float(int(open_rate * 1.1))
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once(require_params)
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=40,second=54, tzinfo=pytz.utc)        
        dummy_api.set_create_required_param_once(require_params)  # not market sell
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        self.assertEqual(1, dummy_api.order.get_cancel_called_count())
        
        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=49,second=59, tzinfo=pytz.utc)        
        dummy_api.set_create_required_param_once(require_params)  # 5 bar is not finished. not market sell
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        self.assertEqual(1, dummy_api.order.get_cancel_called_count())

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=50,second=0, tzinfo=pytz.utc) 
        del require_params["rate"]
        dummy_api.set_create_required_param_once(require_params)  # market sell is required
        dummy_api.order.set_create_not_required_param_once(["rate"])
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        self.assertEqual(1, dummy_api.order.get_cancel_called_count())

        position_status = {
            "data": [
                {
                    "id":10,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": created_time_str,
                    "closed_at": None,
                    "amount": amount,
                    "all_amount": amount,
                    "open_rate": open_rate,
                    "side": "buy",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "buy",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 1,
                            "side": "sell",
                            "status": "open",
                            "amount": str(amount),
                            "rate": str(float(int(open_rate*1.1))),
                        },
                    ]
                }
            ]
        }
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_position_status(position_status["data"])

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=49,second=59, tzinfo=pytz.utc)        
        dummy_api.set_create_required_param_once(require_params)  # 5 bar is not finished. not market sell
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(False)
        one_pos.update_close_orders(chart, check_time)

    def test_update_close_short_order(self):
        decider = PriceDeciderByMA(use_ma_count=3,
                                   buy_ma_div_rate=0.1,
                                   sell_div_rate_from_buy_value=-0.1,
                                   sell_bar_count_to_hold=5)
                                   
        dummy_api = self.create_dummyapi()
        one_pos = OnePositionTrader(decider, dummy_api)
        one_pos.set_max_total_position_price_base(100000)
        one_pos.set_max_free_margin_of_base_currency(100000)
        self.assertEqual(100000, one_pos.max_total_position_price_base)
        
        chart = Chart(span_minutes=5, technical_calculator=TechnicalCalculator([3]))

        chart.add_new_data(time_offset+1, 1000)
        chart.add_new_data(time_offset+1+300, 1100)
        chart.add_new_data(time_offset+1+300*2, 1200)
        # enough bar
        chart.add_new_data(time_offset+1+300*3, 1000)
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once({
            "rate": (1000+1100+1200)/3*1.1,
            "amount": BitcoinUtil.roundBTCby1satoshi(100000/((1000+1100+1200)/3*1.1)),
        })
        one_pos.update_new_orders(chart)

        created_time_str = "2015-12-02T05:27:53.000Z"
        created_time     = datetime(year=2015,month=12,day=2,hour=5,minute=27,second=53, tzinfo=pytz.utc)
        open_rate = 43553.0
        amount = 1.5234
        position_status = {
            "data": [
                {
                    "id":10,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": created_time_str,
                    "closed_at": None,
                    "amount": amount,
                    "all_amount": amount,
                    "open_rate": open_rate,
                    "side": "sell",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "sell",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 100,
                            "side": "buy",
                            "status": "cancel",
                        },
                    ]
                }
            ]
        }
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_position_status(position_status["data"])

        self.assertEqual(1, len(one_pos.positions))

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=30,second=3, tzinfo=pytz.utc)      
        require_params = {}
        require_params["amount"] = amount
        require_params["order_type"] = "close_short"
        require_params["position_id"] = 10
        require_params["rate"] = float(int(open_rate * 0.9))
        dummy_api.set_api_success()
        dummy_api.test_create_api_be_called_ok()
        dummy_api.set_create_required_param_once(require_params)
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        
        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=40,second=54, tzinfo=pytz.utc)        
        dummy_api.set_create_required_param_once(require_params)  # not market sell
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        self.assertEqual(1, dummy_api.order.get_cancel_called_count())
        
        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=49,second=59, tzinfo=pytz.utc)        
        dummy_api.set_create_required_param_once(require_params)  # 5 bar is not finished. not market sell
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        self.assertEqual(1, dummy_api.order.get_cancel_called_count())

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=50,second=0, tzinfo=pytz.utc) 
        del require_params["rate"]
        dummy_api.set_create_required_param_once(require_params)  # market sell is required
        dummy_api.order.set_create_not_required_param_once(["rate"])
        dummy_api.order.reset_called_count()
        one_pos.update_close_orders(chart, check_time)
        self.assertEqual(1, dummy_api.order.get_create_called_count())
        self.assertEqual(1, dummy_api.order.get_cancel_called_count())

        position_status = {
            "data": [
                {
                    "id":10,
                    "pair": "btc_jpy",
                    "status": "open",
                    "created_at": created_time_str,
                    "closed_at": None,
                    "amount": amount,
                    "all_amount": amount,
                    "open_rate": open_rate,
                    "side": "sell",
                    "pl": -1500,
                    "new_order": {
                        "id": 1,
                        "side": "sell",
                        "status": "complete",
                        "created_at": "2015-12-02T05:27:53.000Z",
                    },
                    "close_orders": [
                        {
                            "id": 1,
                            "side": "buy",
                            "status": "open",
                            "amount": str(amount),
                            "rate": str(float(int(open_rate*0.9))),
                        },
                    ]
                }
            ]
        }
        one_pos.set_max_total_position_price_base(200000)
        one_pos.set_max_free_margin_of_base_currency(200000)
        one_pos._update_position_status(position_status["data"])

        check_time = datetime(year=2015,month=12,day=2,hour=5,minute=49,second=59, tzinfo=pytz.utc)
        dummy_api.set_create_required_param_once(require_params)  # 5 bar is not finished. not market sell
        dummy_api.order.set_create_api_call_ok(False)
        dummy_api.order.set_cancel_api_call_ok(False)
        one_pos.update_close_orders(chart, check_time)
        
if __name__ == "__main__":
    unittest.main()

