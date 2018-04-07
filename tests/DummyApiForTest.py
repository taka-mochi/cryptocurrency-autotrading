# coding: utf-8

import json

class ApiDummyOrderTrade(object):
    def __init__(self, test, _tick_price, _tick_amount, _min_amount, is_leverage):
        self.test = test
        self.latest_id = 0
        self.api_success_state = True
        self.required_create_params = None
        self.not_required_create_params = None
        self.create_api_call_ok = True
        self.cancel_api_call_ok = True
        self.create_called_count = 0
        self.cancel_called_count = 0
        self.is_leverage = is_leverage

        self._tick_price = _tick_price
        self._tick_amount = _tick_amount
        self._min_amount = _min_amount

    def tick_price(self, symbol = None):
        self.test.assertNotEqual(symbol, None)
        return self._tick_price
        
    def tick_amount(self, symbol = None):
        self.test.assertNotEqual(symbol, None)
        return self._tick_amount

    def min_create_amount(self, symbol = None):
        self.test.assertNotEqual(symbol, None)
        return self._min_amount

    def set_api_success_state(self, success):
        self.api_success_state = success
        
    def set_create_api_call_ok(self, ok):
        self.create_api_call_ok = ok

    def set_cancel_api_call_ok(self, ok):
        self.cancel_api_call_ok = ok
        
    def set_create_required_param_once(self, required_params):
        self.required_create_params = required_params

    def set_create_not_required_param_once(self, not_required_params):
        self.not_required_create_params = not_required_params

    def reset_called_count(self):
        self.create_called_count = 0
        self.cancel_called_count = 0

    def get_create_called_count(self):
        return self.create_called_count

    def get_cancel_called_count(self):
        return self.cancel_called_count

    def create(self, params):
        test = self.test
        
        if not self.create_api_call_ok:
            test.assertTrue(False)

        test.assertTrue('order_type' in params)
        test.assertTrue('amount' in params)
        test.assertTrue('pair' in params)

        test.assertTrue(float(params['amount']) > 0)
        if 'rate' in params:
            test.assertTrue(float(params['rate']) > 0)
            
        if self.is_leverage:
            if params['order_type'] == 'leverage_buy' or \
               params['order_type'] == 'leverage_sell' or \
               params['order_type'] == 'close_long' or  \
               params['order_type'] == 'close_short':
                test.assertEqual(params['pair'], 'btc_jpy')
        
            if params['order_type'] == 'close_long' or  \
               params['order_type'] == 'close_short':
                test.assertTrue('position_id' in params)
                test.assertTrue(params['position_id'] > 0)

        else:
            if 'rate' in params:
                test.assertTrue(params['order_type'] == "buy" or params['order_type'] == "sell")
            else:
                test.assertTrue(params['order_type'] == "market_buy" or params['order_type'] == "market_sell")

            test.assertNotEqual(params['order_type'], 'leverage_buy')
            test.assertNotEqual(params['order_type'], 'leverage_sell')
            test.assertNotEqual(params['order_type'], 'close_long')
            test.assertNotEqual(params['order_type'], 'close_short')

            test.assertFalse('position_id' in params)
        
        self.check_create_required(params)

        self.create_called_count += 1

        if self.api_success_state is True:
            self.latest_id += 1
            ret_param = {'success':True, 'id': self.latest_id, 'amount': params['amount'], 'order_type': params['order_type']}
            if 'rate' in params:
                ret_param['rate'] = params['rate']
            if 'stop_loss_rate' in params:
                ret_param['stop_loss_rate'] = params['stop_loss_rate']
            return json.dumps(ret_param)
        elif self.api_success_state is False:
            return json.dumps({'success':False})
        else:
            return "<html>502 bad gateway</html>"

    def cancel(self, params):
        test = self.test
        if self.cancel_api_call_ok is False:
            test.assertTrue(False)

        test.assertTrue('id' in params)
        test.assertTrue(params['id'] > 0)
        test.assertTrue(params['id'] <= self.latest_id)
        test.assertTrue('pair' in params)

        self.cancel_called_count += 1
        
        if self.api_success_state is True:
            return json.dumps({'success': True, 'id': params['id']})
        elif self.api_success_state is False:
            return json.dumps({'success': False})
        else:
            return "<html>502 bad gateway</html>"
            
    def check_create_required(self, params):
        # check required params
        if self.required_create_params is not None:
            for key in self.required_create_params.keys():
                req_param = self.required_create_params[key]
                if type(req_param) == type(params[key]):
                    if isinstance(req_param, float):
                        self.test.assertAlmostEqual(req_param, params[key])
                    else:
                        self.test.assertEqual(req_param, params[key])
                elif isinstance(req_param, int) and isinstance(params[key], str) and '.' not in params[key]:
                    self.test.assertEqual(req_param, int(params[key]))
                elif (isinstance(req_param, float) or isinstance(req_param, int)) and isinstance(params[key], str):
                    self.test.assertAlmostEqual(req_param, float(params[key]))
                else:
                    self.test.assertEqual(str(req_param), str(params[key]))
        if self.not_required_create_params is not None:
            for key in self.not_required_create_params:
                print(params)
                self.test.assertFalse(key in params)

        self.required_create_params = None
        self.not_required_create_params = None

class ApiDummyForTest(object):
    # dummy class for coincheck api
    def __init__(self, test, _tick_price, _tick_amount, _min_amount, is_leverage):
        self.order = ApiDummyOrderTrade(test, _tick_price, _tick_amount, _min_amount, is_leverage)

    def set_api_success(self):
        self.order.set_api_success_state(True)
    def set_api_fail(self):
        self.order.set_api_success_state(False)
    def set_api_fail_by_none(self):
        self.order.set_api_success_state(None)
    
    def test_create_api_be_called_ok(self):
        self.order.set_create_api_call_ok(True)
    def test_create_api_must_not_be_called(self):
        self.order.set_create_api_call_ok(False)
    def set_create_required_param_once(self, required_params):
        self.order.set_create_required_param_once(required_params)
