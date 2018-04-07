# coding: utf-8

import argparse
import json
import threading
import signal
import sys
import time
import traceback
from datetime import datetime
from datetime import timedelta
import dateutil.parser

from ChartUpdaterByCCWebsocket import ChartUpdaterByCoincheckWS
from MoveAverageTradePosition import OnePositionTrader
from ChartBars import Chart
from TechnicalCalculator import TechnicalCalculator
from Algorithm_PriceDeciderByMA import PriceDeciderByMA
from Util import TimeUtil
from AlgorithmConfig import AlgorithmConfig

import os
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

import coincheck.coincheck

GLOBAL_LOCK_PROCESS_ONE_FRAME = threading.Lock()
LATEST_FREEZED_BAR = {}

GLOBAL_IS_TEST_BOT=False

GLOBAL_STOP_MAKE_POSITION_FILE=None

def query_margin(api_inst, symbols=["jpy"]):
    balance_ret_str = api_inst.account.balance()
    balance_ret = None
    try:
        balance_ret = json.loads(balance_ret_str)
    except:
        print("failed to parse balance_ret_str")
        print(balance_ret_str)
        return None

    if balance_ret is None or \
       balance_ret["success"] is False:
        return None

    results = {}
    for symbol in symbols:
        if symbol in balance_ret:
            remain   = float(balance_ret[symbol])
            reserved = float(balance_ret[symbol + "_reserved"])
            results[symbol] = remain + reserved
            results[symbol + "_free"] = remain

    return results

def query_leverage_margin(api):
    leverage_balance_ret_str = api.account.leverage_balance()
    leverage_balance_ret = None
    try:
        leverage_balance_ret = json.loads(leverage_balance_ret_str)
    except:
        print("failed to parse leverage_balance_ret_str")
        print(leverage_balance_ret_str)

    if leverage_balance_ret is None or \
       leverage_balance_ret["success"] is False:
        return None

    margin_total     = leverage_balance_ret["margin"]
    available_mergin = leverage_balance_ret["margin_available"]

    return margin_total

def query_leverage_positions(api):

    ret = []
    latest_got_id = None

    #while True:
    query_count = 25
    pagenation_params = {
        "limit": query_count,
        "order": "desc",
    }
    if latest_got_id is not None:
        pagenation_params["starting_after"] = str(latest_got_id)
        
    positions_ret_str = api.leverage.positions(pagenation_params)
    positions_ret = None
    try:
        positions_ret = json.loads(positions_ret_str)
    except:
        print("could not parse positions_ret_str")
        print(positions_ret_str)

    if positions_ret is None:
        return None

    if not positions_ret["success"]:
        return None

    got_data = positions_ret["data"]
    filtered_got_data = list(filter(lambda x:x["status"] != "closed", got_data))
    ret += filtered_got_data

    #if len(got_data) >= query_count:
    #    latest_got_id = got_data[-1]["id"]
    #else:
                
    return ret
    
def query_transactions(api_inst, pairs):

    ret = []
    latest_got_id = None

    #while True:
    query_count = 100
    pagenation_params = {
        "limit": query_count,
        "order": "desc",
        "pair": pairs,
    }
    if latest_got_id is not None:
        pagenation_params["starting_after"] = str(latest_got_id)
        
    transactions_ret_str = api_inst.order.transactions(pagenation_params)
    transactions_ret = None
    try:
        transactions_ret = json.loads(transactions_ret_str)
    except:
        print("could not parse transactions_ret_str")
        print(transactions_ret_str)

    if transactions_ret is None:
        return None

    if not transactions_ret["success"]:
        return None

    got_data = transactions_ret["transactions"]
    ret += got_data

    return ret

def query_orders(api, pairs):
    order_ret_str = api.order.opens({"pair":pairs})
    order_ret = None
    try:
        order_ret = json.loads(order_ret_str)
    except:
        print("failed to parse order_ret_str")
        print(order_ret_str)

    if order_ret is None:
        return None

    if not order_ret["success"]:
        return None

    got_data = order_ret["orders"]
    #got_data = list(filter(lambda x:x["pair"] == "btc_jpy", got_data))
            
    return got_data

def update_all_status_by_api(api, currencies, pairs):
    margin = query_margin(api, currencies)
    print("query margin starts...")
    if margin is None:
        print(str(datetime.now()) + ": Failed to get balance")
        return None, None, None, None, None
    for currency in currencies:
        if currency not in margin:
            print(str(datetime.now()) + ":" + currency + " margin is failed to get")
            return None, None, None, None, None

    # currently, leverage_margin except for jpy is not supported
    #leverage_margin = query_leverage_margin(api, currencies)
    leverage_margin = query_leverage_margin(api)
    print("query leverage margin starts...")
    if leverage_margin is None:
        print(str(datetime.now()) + ": Failed to get leverage margin balance")
        return None, None, None, None, None

    print("query position starts...")
    positions = query_leverage_positions(api)
    if positions is None:
        print(str(datetime.now()) + ": Failed to get leverage positions")
        return None, None, None, None, None

    print("query transactions starts...")
    transactions = query_transactions(api, pairs)
    if query_transactions is None:
        print(str(datetime.now()) + ": Failed to get transactions")
        return None, None, None, None, None
        
    print("query orders starts...")
    orders = query_orders(api, pairs)
    if orders is None:
        print(str(datetime.now()) + ": Failed to get orders")
        return None, None, None, None, None

    return margin, leverage_margin, positions, transactions, orders


# "target_symbol": if None, all symbols are checked
def process_status_and_orders(api, chart_updater, target_symbol, position_traders, lots, recursive_called = False):
    global GLOBAL_LOCK_PROCESS_ONE_FRAME
    global GLOBAL_IS_TEST_BOT
    global GLOBAL_STOP_MAKE_POSITION_FILE

    do_not_create_new_order = False
    if GLOBAL_STOP_MAKE_POSITION_FILE is not None:
        do_not_create_new_order = os.path.exists(GLOBAL_STOP_MAKE_POSITION_FILE)
        if do_not_create_new_order:
            print("-----creating new order is stopped!!-----")

    immediate_re_update_required = False
    with GLOBAL_LOCK_PROCESS_ONE_FRAME:
        # query current states by api
        print("----------------------")
        print(str(datetime.now()) + ", update" + (": immediate recursive call" if recursive_called else ""))

        # base currencies (to get margin)
        #WIPWIPWIP: use_target_symbol
        base_currencies = list(set(map(lambda x:x.get_base_currency(), position_traders)))
        pairs = list(set(map(lambda x:x.pair, position_traders)))

        try:
            margin, leverage_margin, positions_ret, transactions, orders = update_all_status_by_api(api, base_currencies, pairs)

            if margin is None or leverage_margin is None or positions_ret is None or transactions is None or orders is None:
                print("Failed to request")
                return

            print("leverage margin:", leverage_margin)
            print("wallet total margin:", margin)
            
            if len(positions_ret) > 0:
                print("positions")
                show_info = []
                for x in positions_ret:
                    pos_id = x["id"]
                    new_order_id = None
                    if "new_order" in x and "id" in x["new_order"]:
                        new_order_id = x["new_order"]["id"]
                    show_info.append((pos_id, new_order_id))
                print(show_info)
            if len(orders) > 0:
                print("orders")
                print(orders)

            
            if GLOBAL_IS_TEST_BOT:
                max_margin_to_test = {}
                max_margin_to_test['jpy'] = 18000
                max_margin_to_test['btc'] = 0.01
                print("!!!!!!!!!!!!!!!!!!!BOT IS TEST MODE: max_margin_jpy = %f!!!!!!!!!!!!!!!!!!!!!!" % max_margin_to_test['jpy'])
                print("!!!!!!!!!!!!!!!!!!!BOT IS TEST MODE: max_margin_btc = %f!!!!!!!!!!!!!!!!!!!!!!" % max_margin_to_test['btc'])
                leverage_margin['jpy'] = min(max_margin_to_test['jpy'], float(leverage_margin['jpy']))
                if 'btc' in leverage_margin:
                    leverage_margin['btc'] = min(max_margin_to_test['btc'], float(leverage_margin['btc']))
                if 'jpy' in margin:
                    margin['jpy'] = min(max_margin_to_test['jpy'], margin['jpy'])
                if 'btc' in margin:
                    margin['btc'] = min(max_margin_to_test['btc'], margin['btc'])

            # get all trader position values
            all_positioned = {}
            for pos_i, position in enumerate(position_traders):
                currency = position.get_base_currency()
                if currency not in all_positioned:
                    all_positioned[currency] = 0
                all_positioned[currency] += position.get_positioned_price_base()
                
            # update for each traders
            for pos_i, position in enumerate(position_traders):
                currency = position.get_base_currency()
                # set usable money
                if position.use_leverage:
                    leverage_margin[currency] = float(leverage_margin[currency])
                    position.set_max_total_position_price_base(lots[pos_i]*leverage_margin[currency])
                    position.set_max_free_margin_of_base_currency(lots[pos_i]*leverage_margin[currency])
                else:
                    # margin = all - positioned
                    # => all should be set to set_max_total_position_price_jpy
                    this_margin = margin[currency]
                    possible_total = this_margin + all_positioned[currency]
                    if GLOBAL_IS_TEST_BOT:
                        possible_total = min(possible_total, max_margin_to_test[currency])
                        #possible_total = 0.1 # dummy
                    total = possible_total *lots[pos_i]
                    position.set_max_total_position_price_base(total)
                    position.set_max_free_margin_of_base_currency(margin[currency + "_free"])
                    
                # update position & order status
                position.update_status(positions_ret, transactions, orders)

            # update close orders
            now_time = TimeUtil.now_utc()
            for position in position_traders:
                chart  = chart_updater.get_chart(position.pair)
                print("pair:", position.pair, " chart:", chart)
                position.update_close_orders(chart, now_time)

            # update orders (when recursive calling, status updating and place sell order is objective. not update new orders
            if not recursive_called:
                for position in position_traders:
                    # udpate orders
                    chart  = chart_updater.get_chart(position.pair)
                    update_ret = position.update_new_orders(chart, do_not_create_new_order=do_not_create_new_order)
                    if update_ret is True:
                        immediate_re_update_required = True

        except Exception as exp:
            print("Error has occurred!!! Program continues to work but should be fixed!!")
            print(traceback.format_exc())
            print(exp)
            print(exp.args)
    
    # if immediate update is required, call this method recursively
    if immediate_re_update_required is True and recursive_called is False:
        process_status_and_orders(api, chart_updater, target_symbol, position_traders, lots, recursive_called = True)

def process_status_and_orders_with_chart_check(api, chart_updater, target_symbol, position_traders, lots):
    global GLOBAL_LOCK_PROCESS_ONE_FRAME
    global LATEST_FREEZED_BAR

    update_require = False

    with GLOBAL_LOCK_PROCESS_ONE_FRAME:

        chart = chart_updater.get_chart(target_symbol)
        last_bar = chart.get_bar_from_last(get_copy=False)

        if target_symbol not in LATEST_FREEZED_BAR:
            LATEST_FREEZED_BAR[target_symbol] = None

        if last_bar != LATEST_FREEZED_BAR[target_symbol]:
            print("!!!!!!!!!!!bar changed", datetime.now(), last_bar)
            if LATEST_FREEZED_BAR[target_symbol] is not None:
                bar = LATEST_FREEZED_BAR[target_symbol]
                print("latest_bar = b/e/h/l = ", bar.begin, bar.end, bar.high, bar.low)
            LATEST_FREEZED_BAR[target_symbol] = last_bar
            update_require = True
            
    if update_require:
        process_status_and_orders(api, chart_updater, target_symbol, position_traders, lots)

def preload_chart(chart, file_path, allow_time_gap_in_sec = 90):
    loaded_bar = {}
    for line in open(file_path):
        line = line.strip()
        if len(line) == 0: continue

        # DATE,BEGIN,END,LOW,HIGH
        data = line.split(",")
        
        start_date = dateutil.parser.parse(data[0])
        begin = float(data[1])
        end = float(data[2])
        low = float(data[3])
        high = float(data[4])

        timestamp = TimeUtil.timestamp_utc(start_date)
        
        loaded_bar[timestamp] = (begin, end, low, high)

    keys = sorted(loaded_bar.keys())

    latest_date = keys[-1]
    if (TimeUtil.now_timestamp_utc() - latest_date) > allow_time_gap_in_sec:
        print("Cannot load preloaded chart due to timegap: ", (TimeUtil.now_timestamp_utc() - latest_date))
        return

    one_sec = 1
    for timestamp in keys:
        begin, end, low, high = loaded_bar[timestamp]
        chart.add_new_data(timestamp + one_sec, begin)
        chart.add_new_data(timestamp + one_sec, low)
        chart.add_new_data(timestamp + one_sec, high)
        chart.add_new_data(timestamp + one_sec, end)

    print("Load preloaded chart!!")

def select_api_and_chartupdater(trade_center_name, bar_minutes, technical_calculator, pairs):

    if trade_center_name == "coincheck":
        accessKey = None
        secretKey = None
        with open("keys/coincheck.txt", "r") as fr:
            accessKey = fr.readline().strip()
            secretKey = fr.readline().strip()

        api = coincheck.coincheck.CoinCheck(accessKey, secretKey)

        # instances for trading algorithm
        chart_updater = ChartUpdaterByCoincheckWS(chart_span_minutes=bar_minutes,
                                                  technical_calculator=technical_calculator,
                                                  run_immediately=True)

        return api, chart_updater

    
    elif trade_center_name == "binance":
        import binance_api.binance_api
        from ChartUpdaterByBinanceWebsocket import ChartUpdaterByBinanceWS
    
        accessKey = None
        secretKey = None
        with open("keys/binance.txt", "r") as fr:
            accessKey = fr.readline().strip()
            secretKey = fr.readline().strip()

        api = binance_api.binance_api.Binance(accessKey, secretKey)

        chart_updater = ChartUpdaterByBinanceWS(binance_api_client=api,
                                                chart_span_minutes=bar_minutes,
                                                pairs_or_symbols=pairs,
                                                technical_calculator=technical_calculator)

        return api, chart_updater

    return None, None

def main():
    parser = argparse.ArgumentParser(description='Move Average Algorithm Main')
    parser.add_argument('--config_json', type=str, default=None, required=True,
                        help="Set the config file instead of set parameters directly")
    parser.add_argument('--check_stop_make_position_file', type=str, default=None)
    parser.add_argument('--bar_minutes', type=int, required=True,
                        help='Use bar minutes')
    parser.add_argument('--use_ma_bar_counts', nargs="+", type=int, default=None,
                        help='Use move average bar counts')
    parser.add_argument("--open_div_rates", nargs="+", type=float, default=None,
                        help='Open diverge rates to move average')
    parser.add_argument("--close_div_rates", nargs="+", type=float, default=None,
                        help='Close diverge rate to buy value')
    parser.add_argument("--max_hold_bar_counts", nargs="+", type=int, default=None,
                        help='Bar counts to hold buy position')
    parser.add_argument("--lots", nargs="+", type=float, default=None,
                        help='lots for each. default=all 1.0')
    parser.add_argument("--preload_chart", default=None,
                        help='preload chart data')
    parser.add_argument("--test_bot", action="store_true", default=False,
                        help="set this when test this bot")
    parser.add_argument("--trade_center", type=str, default="coincheck")

    args = parser.parse_args()
    print(args)

    global GLOBAL_IS_TEST_BOT
    GLOBAL_IS_TEST_BOT = args.test_bot

    global GLOBAL_STOP_MAKE_POSITION_FILE
    GLOBAL_STOP_MAKE_POSITION_FILE = args.check_stop_make_position_file

    price_deciders = []
    use_bar_counts = []
    lots = []
    use_leverage = []
    pairs = []
    timelimits_to_grouping_transaction = []

    assert (args.bar_minutes is not None)

    if args.config_json is None:
        # if config file is not set, parameters must be directly set
        assert (args.open_div_rates is not None)
        assert (args.close_div_rates is not None)
        assert (args.use_ma_bar_counts is not None)
        assert (args.max_hold_bar_counts is not None)

        # check parameters
        assert (len(args.open_div_rates) == len(args.close_div_rates))
        assert (len(args.open_div_rates) == len(args.use_ma_bar_counts))
        assert (len(args.open_div_rates) == len(args.max_hold_bar_counts))

        make_position_count = len(args.open_div_rates)
        if args.lots is not None:
            assert (len(args.lots) == make_position_count)
            lots = args.lots
        else:
            lots = [1.0 for _ in range(make_position_count)]
        print("lots,", lots)

        # make price deciders
        for pos_i in range(make_position_count):
            open_div_rate  = args.open_div_rates[pos_i]
            close_div_rate = args.close_div_rates[pos_i]
            ma_bar_count   = args.use_ma_bar_counts[pos_i]
            max_hold_count = args.max_hold_bar_counts[pos_i]
            use_bar_counts.append(ma_bar_count)
            use_leverage.append(True)
            pairs.append("btc_jpy")

            decider = PriceDeciderByMA(use_ma_count=ma_bar_count,
                                       buy_ma_div_rate=open_div_rate,
                                       sell_div_rate_from_buy_value=close_div_rate,
                                       sell_bar_count_to_hold=max_hold_count)
            price_deciders.append(decider)
            
            timelimits_to_grouping_transaction.append(10) # default value

    else:
        print("**Parameters in json file override argumented parameters**")
        algorithm_config = AlgorithmConfig.load_from_json(args.config_json)
        for config_i, config in enumerate(algorithm_config.configs):
            decider = config.create_price_decider()
            assert (decider is not None)
            price_deciders.append(decider)
            use_bar_counts.append(config.use_bar_count)
            lots.append(config.lot)
            pairs.append(config.pair)
            use_leverage.append(config.use_leverage)
            # grouping timelimit
            if "timelimit_to_grouping_transaction" in config.all_parameters:
                timelimits_to_grouping_transaction.append(int(config.all_parameters["timelimit_to_grouping_transaction"]))
            else:
                timelimits_to_grouping_transaction.append(10)  # default value


    # make api instances
    technical_calculator = TechnicalCalculator(list(set(use_bar_counts)))
    api, chart_updater = select_api_and_chartupdater(args.trade_center, args.bar_minutes, technical_calculator, pairs)
    print(api)

    # make position managers
    position_traders = []
    
    # make positions
    for pos_i in range(len(price_deciders)):
        decider = price_deciders[pos_i]
        print("%dth position use_leverage=%s" % (pos_i, str(use_leverage[pos_i]),))
        trader = OnePositionTrader(price_decide_algorithm=decider,
                                   api=api,
                                   pair=pairs[pos_i],
                                   use_leverage=use_leverage[pos_i])
        trader.set_max_total_position_price_base(0)   # at first, set to 0
        trader.set_timelimit_to_grouping_transaction(timelimits_to_grouping_transaction[pos_i])
        position_traders.append(trader)


    # preload chart data if possible
    if args.preload_chart is not None:
        raise NotImplemented("not supported now")
        preload_chart(chart, args.preload_chart)

    callback_on_update=lambda s=None: process_status_and_orders_with_chart_check(api, chart_updater, s, position_traders, lots)
    chart_updater.set_callback_on_update(callback_on_update)

    #while chart_updater.is_started is False:
    #    time.sleep(0.1)
    #chart_updater.start_btc_jpy_subscribe()  # start update of websocket listening
    
    # set signal interrupter
    def stop(a,b):
        chart_updater.set_reconnect_and_resubscribe_when_closed(False)
        chart_updater.stop()
        sys.exit(-1)

    try:
        #signal.signal(signal.SIGQUIT, stop)
        #signal.signal(signal.SIGHUP, stop)
        #signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
    except:
        pass

    # update position manager loop!!!
    while True:
        #chart.update_freeze_state(TimeUtil.now_timestamp_utc())
        process_status_and_orders(api, chart_updater, None, position_traders, lots)
        time.sleep(9.5)  # 

if __name__ == "__main__":
    main()

