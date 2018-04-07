# coding: utf-8

import math
import dateutil
import dateutil.parser
import json

from ChartBars import Chart
from ChartUpdaterByCCWebsocket import ChartUpdaterByCoincheckWS
from Util import BitcoinUtil

def adjust_price_to_tick(price, tick):
    return price - math.fmod(price, tick)

def adjust_amount_to_tick(amount, tick):
    return amount - math.fmod(amount, tick)

# a class for one position
class OnePositionTrader(object):
    def __init__(self, price_decide_algorithm, api, pair="btc_jpy", use_leverage = True):
        self.max_total_position_price_base = 0  # total maximum position size in base currency
        self.positioned_price_base = 0          # total position price in base currency (actually paired currency)
        self.positioned_value_in_qty = 0   # used only for genbutsu
        self.max_free_margin_of_base_currency = 0  # max free margin. we cannot use orders that exceed this margin
        
        self.positions = []
        self.position_id_to_sellids = {}
        self.got_all_order_ids = []
        self.got_close_order_ids = []
        self.exist_order_info_list = None
        self.exist_close_order_info_list = None
        self.last_checked_transaction_id = 0
        self.api = api                         # api: e.g. instance of CoinCheck
        self.use_leverage = use_leverage
        self.timelimit_to_grouping_transaction = 2 # 約定時刻がこの秒数以下なら同一ポジションとみなす（use_leverage == False の場合のみ）
        self.__pair = pair

        self.price_decide_algorithm = price_decide_algorithm

        print("PositionTrader: inst=" + str(self) + ", pair=" + str(pair))

    @property
    def pair(self):
        return self.__pair

    def get_base_currency(self):
        return self.pair.split("_")[1].lower()

    def get_qty_currency(self):
        return self.pair.split("_")[0].lower()

    # set usable jpy (available_margin + reserved_margin + (positioned))
    def set_max_total_position_price_base(self, p):
        self.set_max_total_position_price_of_base_currency(p)

    def set_max_total_position_price_of_base_currency(self, p):
        self.max_total_position_price_base = p
        
    def set_max_free_margin_of_base_currency(self, p):
        self.max_free_margin_of_base_currency = p

    def get_max_total_position_price_base(self):
        return self.get_max_total_position_price_of_base_currency()

    def get_max_total_position_price_of_base_currency(self):
        return self.max_total_position_price_base

    def get_positioned_price_base(self):
        return self.positioned_price_base
        
    def set_timelimit_to_grouping_transaction(self, timelimit_to_grouping_transaction):
        self.timelimit_to_grouping_transaction = timelimit_to_grouping_transaction

    # check current status and make new positions according to algorithm
    # notice: this method should be called after update_status
    def update_new_orders(self, chart, do_not_create_new_order=False):
        assert (self.price_decide_algorithm is not None)

        position_type = None
        target_value = None
        stoploss_rate = None

        decide_make_ret = self.price_decide_algorithm.decide_make_position_order(chart)
        if len(decide_make_ret) == 3:
            (position_type, target_value, stoploss_rate) = decide_make_ret
        else:
            (position_type, target_value) = decide_make_ret

        if target_value is None or position_type is None:
            # algorithm says this instance should not make order. cancel all
            if self.exist_order_info_list is not None:
                for exist_order_info in self.exist_order_info_list:
                    self._cancel_order(exist_order_info["id"])
                self.exist_order_info_list = None
            return False
        
        # round to possible price
        tick = self.api.order.tick_price(self.pair)
        target_value = adjust_price_to_tick(target_value, tick)
        if stoploss_rate is not None:
            stoploss_rate = adjust_price_to_tick(stoploss_rate, tick)

        # !!round to possible amount
        possible_make_total_price_base_cur = self.get_max_total_position_price_of_base_currency() - self.positioned_price_base
        possible_make_total_price_base_cur = min(possible_make_total_price_base_cur, self.max_free_margin_of_base_currency)
        amount_tick = self.api.order.tick_amount(self.pair)
        possible_amount = 1.0 * possible_make_total_price_base_cur / target_value
        possible_amount = adjust_amount_to_tick(possible_amount,amount_tick)
        
        print("possible_create_in_base = %f, want to make amount in base = %f, possible amount = %f" %
                    (self.get_max_total_position_price_of_base_currency() - self.positioned_price_base,
                     possible_make_total_price_base_cur, possible_amount))

        #print("base_cur = %f, positioned = %f, others = %f" % (self.get_max_total_position_price_of_base_currency(), self.positioned_price_base, self.other_reserved_base,))
        #print("target_value = %f, possible_base = %f" % (target_value, possible_make_total_price_base_cur,))

        if possible_amount <= 0.000001:
            # too few btc
            print("want to make (price,amount) = (%f,%f) but too few amount" % (target_value, possible_amount))
            return False

        if not do_not_create_new_order:
            success, new_order_created = self._update_or_create_order(position_type, target_value, possible_amount, stop_loss_rate=stoploss_rate)
            return new_order_created
        else:
            self._cancel_exist_all_buy_orders()
            print("algorithm wants to create a new order but DO_NOT_CREATE_NEW flag = true")
            return False

    # update close orders according to current positions
    # this class should be called after update_status
    def update_close_orders(self, chart, current_time_timezone_aware):
        
        for position in self.positions:
            open_rate = float(position["open_rate"])
            amount = float(position["amount"])
            created_time = position["created_at_datetime"]

            target_value = None
            if self.price_decide_algorithm.market_sell_decide_algorithm(chart, open_rate, created_time, current_time_timezone_aware) is True:
                # market order close
                pass
            else:
                target_value = self.price_decide_algorithm.sell_price_decide_algorithm(open_rate)
                target_value = adjust_price_to_tick(target_value, self.api.order.tick_price(self.pair))

            self._update_or_create_close_order(position, target_value)

    # interface to update internal position & order status
    def update_status(self, valid_position_info, valid_transaction_info, valid_order_info):
        # update position/order status (assume: pagenations are already cleared)
        self._update_order_id_status(valid_order_info)

        if self.use_leverage:
            self._update_position_status(valid_position_info)
        else:
            self._update_transaction_status(valid_transaction_info)
        
    def _update_position_status(self, valid_position_info):
        # apply real positions status to this instance
        # レバレッジ用
        if not self.use_leverage:
            return

        """
        position example (array of "data" will be passed)
        {
          "data": [
            {
              "id": 10,
              "pair": "btc_jpy",
              "status": "open",
              "created_at": "2015-12-02T05:27:53.000Z",
              "closed_at": null,
              "open_rate": "43553.0",
              "closed_rate": null,
              "amount": "1.51347797",
              "all_amount": "1.51045705",
              "side": "sell",
              "pl": "-8490.81029287",
              "new_order": {
                "id": 23104033,
                "side": "sell",
                "rate": null,
                "amount": null,
                "pending_amount": "0",
                "status": "complete",
                "created_at": "2015-12-02T05:27:52.000Z"
              },
              "close_orders": [
                {
                  "id": 23755132,
                  "side": "buy",
                  "rate": "10000.0",
                  "amount": "1.0",
                  "pending_amount": "0.0",
                  "status": "cancel",
                  "created_at": "2015-12-05T05:03:56.000Z"
                }
              ]
            }
          ]
        }
        """

        ####
        # parse positions
        ####
        self.positions = []
        self.position_id_to_sellids = {}
        all_positions = valid_position_info
        positioned_value_in_base = 0

        for position in all_positions:
            status = position["status"]
            if status != "open":
                continue
                
            pair = position["pair"]
            if pair != self.pair:
                continue

            position_id = position["id"]

            # check position that is created by the new_order that is self.order_id:
            new_order = position["new_order"]
            if new_order["status"] == "cancel":
                print("new order: " + str(new_order["id"]) + " state is 'cancel'. probably partially contracted and remain is canceled. this position is not ignored")
                #continue

            new_order_id = new_order["id"]

            if new_order_id in self.got_all_order_ids:
                # this position is created by this class's order
                created_time = dateutil.parser.parse(position["created_at"])
                position["created_at_datetime"] = created_time

                amount = position["amount"]
                all_amount = position["all_amount"]
                if all_amount is not None and all_amount < amount:
                    amount = all_amount

                position["amount"] = position["all_amount"] = amount
                self.positions.append(position)

                open_rate = position["open_rate"]
                positioned_value_in_base += float(amount) * float(open_rate)

                # check close orders
                self.position_id_to_sellids[position_id] = \
                    list(map(lambda x:x["id"], filter(lambda x:x["status"] != "cancel", position["close_orders"])))

        self.positioned_price_base = positioned_value_in_base

    def _update_transaction_status(self, valid_transaction_info):
        if self.use_leverage:
            return

        # 現物用。transactionの結果からポジションの状態を解析. 基本的にupdate_position_statusと挙動は同じ。parseするjsonが異なる
        # * ただし、前フレームからの情報を引き継ぐところがupdate_position_statusと違う (現物にはpositionという概念が無い)
        positions = self.positions
        position_id_to_sellids = self.position_id_to_sellids
        close_transactions = []
        
        all_transactions = valid_transaction_info
        positioned_value_in_qty = self.positioned_value_in_qty

        qty_cur = self.get_qty_currency()
        base_cur = self.get_base_currency()

        last_transaction_id_in_this_frame = self.last_checked_transaction_id

        for transaction in all_transactions:
            transaction_id = int(transaction["id"]) # transaction_id means position_id
            transaction["id"] = transaction_id
            # check only new id
            if self.last_checked_transaction_id >= transaction_id:
                continue
            
            last_transaction_id_in_this_frame = max(last_transaction_id_in_this_frame, transaction_id)
            
            # check pair
            this_pair = transaction["pair"]
            if this_pair != self.pair:
                continue

            # check position that is created by the new_order that is self.order_id:
            new_order_id = int(transaction["order_id"])
            transaction["order_id"] = new_order_id

            is_position_transaction = new_order_id in self.got_all_order_ids
            is_close_transaction = new_order_id in self.got_close_order_ids

            if not is_position_transaction and not is_close_transaction:
                continue

            # other pair
            if qty_cur not in transaction["funds"] or base_cur not in transaction["funds"]:
            	continue

            # this position is created by this class's order
            qty_amount = float(transaction["funds"][qty_cur])
            transaction["amount"] = transaction["amount"] = qty_amount

            transaction["open_rate"] = float(transaction["rate"])
            
            open_rate = float(transaction["open_rate"])
            positioned_value_in_qty += float(qty_amount)

            created_time = dateutil.parser.parse(transaction["created_at"])
            transaction["created_at_datetime"] = created_time

            if is_position_transaction:
                # check close orders
                # 漏れがあるとまずい（cancelしなくなる）ので、とりあえずあるだけリンクしておく
                
                position_id_to_sellids[transaction_id] = []
                transaction["close_orders"] = []
                positions.append(transaction)

            else:
                close_transactions.append(transaction)

        # in next frame, only transaction_id > self.last_checked_transaction_id will be checked
        self.last_checked_transaction_id = last_transaction_id_in_this_frame
        print("last_checked_transaction_id = ", self.last_checked_transaction_id)

        print("self.exist_close_order_info_list", self.exist_close_order_info_list)
        if self.exist_close_order_info_list is not None:
            for pos_i, position in enumerate(positions):
                transaction_id = position["id"]
                position_id_to_sellids[transaction_id] = list(map(lambda x:x["id"], self.exist_close_order_info_list))
                position["close_orders"] = self.exist_close_order_info_list
                for i, order in enumerate(position["close_orders"]):
                    order["status"] = "open"
                    order["side"] = order["order_type"]
                    if "amount" not in order:
                        order["amount"] = float(order["pending_amount"])
                        position["close_orders"][i] = order
                positions[pos_i] = position

        # round very small value
        if abs(positioned_value_in_qty) < self.api.order.min_create_amount(self.pair)*0.1:
            positioned_value_in_qty = 0

        positions = sorted(positions, key=lambda x:-x["id"])  # order by desc

        # concat very near created_at transactions
        grouped_positions = self._group_near_transactions(positions)

        # remove closed position & update positioned_value_in_jpy
        valid_positions, positioned_value_in_base = self._remain_non_closed_transactions(grouped_positions, positioned_value_in_qty)
        
        if abs(positioned_value_in_base) < self.api.order.tick_price(self.pair) * self.api.order.min_create_amount(self.pair) * 0.1:
            positioned_value_in_base = 0

        # merge position_id_to_sellids
        self.position_id_to_sellids = {}
        for position in valid_positions:
            pos_id = position["id"]
            self.position_id_to_sellids[pos_id] = position_id_to_sellids[pos_id]
            
        self.positioned_price_base    = positioned_value_in_base
        self.positioned_value_in_qty = positioned_value_in_qty
        self.position_id_to_sellids  = position_id_to_sellids

        self.positions = valid_positions
        print("position_count=%d, positioned_%s=%f, positioned_%s=%f" % (len(self.positions), base_cur, self.positioned_price_base, qty_cur, self.positioned_value_in_qty,))

        # close したかどうか、残っているポジション残量を計算するのに、全て遡らないといけないのは現実的ではない
        # 既にこの段階で解決できるポジション状態(close order id見て、それがあれば反対売買が成立している)
        # を用い、↑で貯めたpositionsから、反対売買済みのものを(amount基準で)消していき(前回フレームで残っていたpositionも含めて)、残ったpositionだけを生きているポジションとし、1つに集約する（現物用なので、idが分かれている意味はない)
        # その残ったpositionID, 消費した反対売買IDのIDを持っておき、次回からはそれより新しいIDのみを反映する
        # ただし、ずっと続けると計算誤差がたまるので、jpyもしくはbtcベースでその合計値が極めて小さくなったら丸めてノーポジ扱いにする

        # うーん...現物とレバレッジで管理が結構変わるから同じクラスにするのはまずかった？ごちゃごちゃしてきてしまった


    # 時間的に約定時刻が近いpositionをまとめる
    def _group_near_transactions(self, target_transactions):
        grouped_positions = []
        positions = target_transactions
        
        if len(positions) > 0:
        
            def grouping(desced_position_array):
                ret_pos = dict(desced_position_array[0])
                total_amount = 0
                total_jpy = 0
                for p in desced_position_array:
                    total_amount += p["amount"]
                    total_jpy    += p["amount"] * p["open_rate"]
                ret_pos["amount"]    = total_amount
                ret_pos["open_rate"] = total_jpy / total_amount
                return ret_pos
        
            concat_start_index = 0
            prev_created_at = positions[0]["created_at_datetime"]
            for idx, pos in enumerate(positions):
                cur_created_at = pos["created_at_datetime"]
                if abs((cur_created_at - prev_created_at).total_seconds()) <= self.timelimit_to_grouping_transaction:
                    # can group
                    prev_created_at = cur_created_at
                    continue
                
                # this position cannot be grouped. make a new group from pos[start_index] - pos[idx-1]
                grouped_positions.append(grouping(positions[concat_start_index:idx]))
                #print(grouped_positions[-1])
                concat_start_index = idx
                prev_created_at = cur_created_at
                
            # remain positioned not be grouped
            grouped_positions.append(grouping(positions[concat_start_index:]))
            
        return grouped_positions
        
    # まだcloseされていないtransactionだけを残す
    def _remain_non_closed_transactions(self, target_transactions, positioned_value_in_qty):
        valid_positions = []
        remain_qty = positioned_value_in_qty
        total_base = 0

        for position in target_transactions:
            if remain_qty <= 0: break

            amount = position["amount"]
            if remain_qty >= amount:
                remain_qty -= amount
            else:
                position["amount"] = remain_qty
                remain_qty = 0

            valid_positions.append(position)
            
            total_base += position["amount"] * position["open_rate"]
            
        return valid_positions, total_base

    def _update_order_id_status(self, valid_order_info):
        
        ####
        # parse orders
        ####

        """
        orders example (array of "orders" will be passed)
        {
          "success": true,
          "orders": [
            {
              "id": 202835,
              "order_type": "buy",
              "rate": 26890,
              "pair": "btc_jpy",
              "pending_amount": "0.5527",
              "pending_market_buy_amount": null,
              "stop_loss_rate": null,
              "created_at": "2015-01-10T05:55:38.000Z"
            },
            {
              "id": 202836,
              "order_type": "sell",
              "rate": 26990,
              "pair": "btc_jpy",
              "pending_amount": "0.77",
              "pending_market_buy_amount": null,
              "stop_loss_rate": null,
              "created_at": "2015-01-10T05:55:38.000Z"
            },
            {
              "id": 38632107,
              "order_type": "buy",
              "rate": null,
              "pair": "btc_jpy",
              "pending_amount": null,
              "pending_market_buy_amount": "10000.0",
              "stop_loss_rate": "50000.0",
              "created_at": "2016-02-23T12:14:50.000Z"
            }
          ]
        }
        """

        #exist_order_ids = list(map(lambda x:x["id"], valid_order_info))

        exist_orders = []
        exist_close_orders = []
        other_orders = []
        for idx, order in enumerate(valid_order_info):
            order_id = order["id"]
            order_pair = order["pair"]
            is_added = False
            
            if order_pair == self.pair:
                if order_id in self.got_all_order_ids:
                    is_added = True
                    exist_orders.append(order)
                elif order_id in self.got_close_order_ids:
                    is_added = True
                    exist_close_orders.append(order)

            if not is_added:
                other_orders.append(order)

        print("exist_create_orders", exist_orders)
        print("exist_close_orders", exist_close_orders)
        self.exist_order_info_list = exist_orders if len(exist_orders) > 0 else None
        self.exist_close_order_info_list = exist_close_orders if len(exist_close_orders) > 0 else None

        #self.other_reserved_base = 0
        #if not self.use_leverage:
        #    for o in other_orders:
        #        if o["order_type"] == "buy":
        #            self.other_reserved_base += float(o["pending_amount"]) * float(o["rate"])

            

    # returns: (is_success, is_new_order_created)
    def _update_or_create_order(self, position_type, target_value, possible_qty, stop_loss_rate = None):
        assert (self.api is not None)

        # order list は現物とleverageで変わらない
        if self.exist_order_info_list is not None:
            # check the same value or not
            if len(self.exist_order_info_list) == 1:
                exist_order_info = self.exist_order_info_list[0]
                cur_rate = exist_order_info["rate"] if "rate" in exist_order_info else None
                # get current stoploss
                cur_stoploss = exist_order_info["stop_loss_rate"] if "stop_loss_rate" in exist_order_info else None
                cur_stoploss_float_or_none = None
                if cur_stoploss is not None:
                    cur_stoploss_float_or_none = float(cur_stoploss)
                target_stoploss_float_or_none = None
                if stop_loss_rate is not None:
                    target_stoploss_float_or_none = float(stop_loss_rate)
          
                cur_amount = None
                if "amount" in exist_order_info:
                    cur_amount = exist_order_info["amount"]
                elif "pending_amount" in exist_order_info:
                    cur_amount = exist_order_info["pending_amount"]

                order_type = None
                if "order_type" in exist_order_info:
                    if exist_order_info["order_type"] == "buy" or\
                       exist_order_info["order_type"] == "leverage_buy":
                        order_type = "long"
                    if exist_order_info["order_type"] == "sell" or \
                       exist_order_info["order_type"] == "leverage_sell":
                        order_type = "short"

                if cur_rate is not None and cur_amount is not None and order_type is not None:
                    if abs(float(cur_rate)-float(target_value)) < 0.00001 and \
                       abs(float(cur_amount)-float(possible_qty)) < 0.00001 and \
                       cur_stoploss_float_or_none == target_stoploss_float_or_none and \
                       order_type == position_type: 
                        # same order. do nothing
                        print("You already ordered this order: rate=%.1f, amount=%f, stoploss_rate=%s, position_type=%s" % (target_value, possible_qty, str(stop_loss_rate), position_type,))
                        return True, False

            # cancel all exist orders
            if not self._cancel_exist_all_buy_orders():
                return False, False

        # check minimum btc
        min_qty = self.api.order.min_create_amount(self.pair)
        if possible_qty < min_qty:
            print("Minimum order btc = %f, you requested = %f" % (min_qty, possible_qty,))
            return False, False


        # make new order
        """
        ret val example
        "success": true,
        "id": 12345,
        "rate": "30010.0",
        "amount": "1.3",
        "order_type": "sell",
        "stop_loss_rate": null,
        "pair": "btc_jpy",
        "created_at": "2015-01-10T05:55:38.000Z"
        """
        is_long = position_type == "long"
        order_type = 'leverage_buy' if is_long else 'leverage_sell'
        if not self.use_leverage:
            order_type = 'buy' if is_long else 'sell'

        order = {
            'rate': "%.8f" % target_value,
            'amount': "%.8f" % possible_qty,
            'order_type': order_type,
            'pair': self.pair
        }
        # not correct
        # this "stop_loss_rate" means: if a value >= stop_loss_rate, sashine will be placed at "rate"
        if stop_loss_rate is not None:
            order["stop_loss_rate"] = stop_loss_rate

        ret_str = self.api.order.create(order)
            
        ret = None
        if ret_str is not None:
            try:
                ret = json.loads(ret_str)
            except:
                print("failed to parse api.order.create result")
                try:
                    print(ret_str)
                except Exception as e:
                    print("failed to show returned json str")
                    print(e)

        if ret is None or ret["success"] is not True or "id" not in ret:
            print("Failed to create order!!")
            try:
                print(ret_str)
            except Exception as e:
                print("failed to show returned json str")
                print(e)

            return False, False

        self.exist_order_info_list = [ret]
        self.got_all_order_ids.append(ret["id"])

        # remove very old orders
        if len(self.got_all_order_ids) > 500:
            self.got_all_order_ids = self.got_all_order_ids[-500:]

        print("order success!", ret_str)

        return True, True

    def _cancel_exist_all_buy_orders(self):
        failed_to_cancel = False
        exist_order_i = 0
        while exist_order_i < len(self.exist_order_info_list):
            exist_order_info = self.exist_order_info_list[exist_order_i]
            if self._cancel_order(exist_order_info["id"]) is False:
                # something error happened!!
                print("order cancel failed %d even if there is a valid order in internal state" % (exist_order_info["id"],))
                failed_to_cancel = True
                del self.exist_order_info_list[exist_order_i]
            else:
                exist_order_i += 1

        if len(self.exist_order_info_list) == 0:
            self.exist_order_info_list = None

        if failed_to_cancel:
            return False

        return True


    # target_value: sashine value. if None, market-make
    def _update_or_create_close_order(self, position, target_value):
        position_id = position["id"]
        if position_id not in self.position_id_to_sellids:
            return False

        sell_qty = float(position["amount"])
        sell_ids = self.position_id_to_sellids[position_id]

        position_type = position["side"]
        # convert position type name
        if position_type == "buy": position_type = "long"
        if position_type == "sell": position_type = "short"

        is_close_long = True
        if position_type == "long": is_close_long = True
        if position_type == "short": is_close_long = False

        # check exist sell-orders. if target value and amount are completely same, do not pass new order
        valid_close_orders = list(filter(lambda x:x["status"] != "cancel" and x["id"] in sell_ids, position["close_orders"]))
        print("valid_close_order count = %d" % len(valid_close_orders))

        if len(valid_close_orders) == 1 and target_value is not None:
            # check the order is already created on exchanger
            valid_close_order = valid_close_orders[0]
            print("your order: rate=%f, amount=%f" % (target_value, sell_qty,))
            print("valid_close_order[0]:")
            print(valid_close_order)
            rate   = None
            if "rate" in valid_close_order:
                rate = float(valid_close_order["rate"])
            amount = valid_close_order["amount"]
            
            is_cur_close_long = False
            if "side" in valid_close_order:
                is_cur_close_long = valid_close_order["side"] == "sell"
            elif "order_type" in valid_close_order:
                is_cur_close_long = valid_close_order["order_type"] == "sell"

            if abs(float(rate)-float(target_value)) < 0.00001 and \
               abs(float(amount)-float(sell_qty)) < 0.00001 and \
               is_close_long == is_cur_close_long:
                # completely same!!
                print("requested close order is already ordered on server:")
                print(" position id:%s, target_value:%s, amount:%s, close_long:%s" % (str(position_id), str(target_value), str(amount), str(is_cur_close_long),))
                return True

        min_qty = self.api.order.min_create_amount(self.pair)
        if sell_qty < min_qty:
            qty_cur = self.get_qty_currency()
            print("Minimum order %s = %f, you requested = %f" % (qty_cur, min_qty, sell_qty,))
            return False

        # cancel all
        for sell_id in sell_ids:
            self._cancel_order(sell_id)
        self.position_id_to_sellids[position_id] = []

        # make new order
        order = {}
        if self.use_leverage:
            order = {
                'amount': '%.8f' % BitcoinUtil.roundBTCby1satoshi(sell_qty),
                'position_id': position_id,
                'order_type': 'close_long' if is_close_long else 'close_short',
                'pair': 'btc_jpy',
            }
            if target_value is not None:
                order['rate'] = target_value

        else:
            # if not leverage order, close order is always "sell"
            if not is_close_long:
                print("normal order cannot make short position!")
                print("you passed close 'short' for normal order")
                return False

            order = {
                'amount': '%.8f' % BitcoinUtil.roundBTCby1satoshi(sell_qty),
                'order_type': 'sell',
                'pair': self.pair,
            }
            if target_value is None:
                # market_sell
                order['order_type'] = "market_sell"
            else:
                order['rate'] = target_value

        ret = self.api.order.create(order)
        ret_str = ret
        if ret is not None:
            try:
                ret = json.loads(ret)
            except:
                print("failed to parse close_long order result")
                try:
                    print(ret_str)
                except Exception as e:
                    print("failed to print error")
                    print(e)

        if ret is None or ret["success"] is not True or "id" not in ret or ret["id"] is None:
            print("sell order canceled but failed to create new sell order!!: position id: %s" % (str(position_id),))
            try:
                print(ret_str)
            except Exception as e:
                print("failed to print error")
                print(e)
            return False

        sell_ids = [ret["id"]]
        self.position_id_to_sellids[position_id] = sell_ids
        self.got_close_order_ids.append(ret["id"])

        if len(self.got_close_order_ids) > 500:
            self.got_close_order_ids = self.got_close_order_ids[-500:]

        return True

    def _cancel_order(self, order_id):
        # call apis for current orders
        if order_id is None:
            print("order is already canceled")
            return True

        # do something
        ret_str = self.api.order.cancel({"id": order_id, "pair": self.pair})
        ret = None
        if ret_str is not None:
            try:
                ret = json.loads(ret_str)
            except:
                print("failed to parse cancel order ret str")
                try:
                    print(ret_str)
                except Exception as e:
                    print("failed to print returned error json")
                    print(e)

        if ret is None or ret["success"] is not True or "id" not in ret:
            print("Failed to cancel order %s: %s" % (str(order_id), str(ret_str),))
            return False
        
        return True

