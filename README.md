cryptocurrency-autotrading
==========

※Japanese follows after English.

## Overview
Crypto-currency auto trading system.

Until end of 2017, this system earns 5%～10% per month but probably does not work well on current market.

## Description

Crypto-currency auto trading system.
※Coincheck is only supported.

Details:
- Get ticks via websocket in realtime and save them as minute chart on memory.
- Many algorithms that use the minute chart data can be run on this system (trading according ticks are not supported).
- These algorithms are implemented in this repository
  - Use simple move average based algorithm. Set a limit order "move average value" * "discount rate". After contract, set limit "contract value" * "limit rate".
  - Check recent highest / lowest value and if a current value is over it, perform buy / sell order. (range brake system).
  - If positive/negative chart continuous count is over pre-set count, perform buy / sell order.
  - These all three algorithms forcely make market close order if a position holding time is too long (the time is set by config).
- Pseudo stoploss system is implemented.


## Requirements

- OS: POSIX
- Python 3.x
- python-dateutil
- websocket-client (install via pip)

## Usage

- Preparation
  - Create a coincheck API key (see other blogs for details of creating API keys).
  - These permissions are required.
    - new order, order list not contracted, cancel order, transaction history, positioni list, account information, balances, leverage account balances
  - Make a text file that contains [API Access Key] at line 1, [API Secret Key] at line 2, then place it to:
    - real_trade/keys/coincheck.txt
    - !! DO NOT ADD THIS FILE TO GIT OR OTHER VERSION CONTROL SYSTEM !!

- How to run
  - With this arguments can run the auto-trade system on read_trade directory.
```run.sh
>python MoveAverageTrade_Main.py --bar_minutes 1 --config_json configs/config_sample.json
```
  - Parameters
    - --bar_minutes: required. Decide what minutes you will use
    - --config_json: required. Set a json file that algorithm parameters are written in. See real_trade/configs/config_sample.json, real_trade/AlgorithmConfig.py and price decide algorithm for detail.
    - --test_bot: run on test mode. Collateral jpy and btc are set to very small. The real value is hard-coded.
    - --check_stop_make_position_file: Set a file path to argument. If a file exists at the path, this program will not create new positions.
    - --preload_chart: Load old chart data that are before start running this program.
    - --trade_center: Set a trade center. Currently only "coincheck" is supported.
    - [deprecated parameters]
      - use_ma_bar_counts, open_div_rates, close_div_rates, max_hold_bar_counts, lots
      - These parameters should be written in "config_json" parameter file.

## Licenses

Except for external libraries and resources, this software is released under the New BSD License, see LICENSE.txt.
External libraries and resources which are used in this project inherit their original license.

==========

日本語版README

## Overview
暗号通貨の自動トレードを行うプログラムです。

2017年終わりごろまでは月5%～10%の割合で利益が出ていましたが、現在の相場では利益が出せないものかと思います。

## Description

以下に対応した暗号通貨自動トレードプログラムです。
※現在取引所はCoincheckのみ対応済

- 値動きデータをAPI経由でリアルタイムに取得し、分足単位のデータとしてメモリ上に格納。
- 分足単位のデータを利用して売買判断をする各種アルゴリズムを載せることが可能（tick単位での売買判断には未対応）。
- 実際に実装しているアルゴリズムは以下の3つ
  - 「単純移動平均線の値*指定割合1」の位置にin指値を置き続け、約定したら「約定値*指定割合2」の位置に決済指値を置き続ける
  - 直近最高値を超えたときに指値を置き、約定したら↑と同様に決済指値を置く
  - 指定した回数 陽線/陰線 が続いたときに指値を置く/成行で発注し、約定したら↑と同様に決済指値を置く
  - 上記3アルゴリズムはすべて「ポジション保有後、一定時間超えても決済されない場合は成行で強制決済」機能付き
- 疑似的な stoploss 機能も実装。

## Requirements

- OS: POSIX準拠
- Python 3.x
- python-dateutil
- websocket-client (install via pip)

## Usage

- 事前準備
  - Coincheckを利用するため、CoincheckのAPIキーを発行してください（詳細は他の方が解説しているので調べてください）
  - 以下の permission が必要です
    - 新規注文, 未決済の注文一覧, 注文のキャンセル, 取引履歴, ポジション一覧, アカウント情報, 残高, レバレッジアカウントの残高
  - 生成されたAPIキーの[アクセスキー]を1行目、[シークレットキー]を2行目に書いたテキストファイルを以下においてください
    - real_trade/keys/coincheck.txt
    - !! このファイルは絶対にgit管理下に置かないでください

- 動作方法
  - real_trade ディレクトリ上で以下のような引数を与えることで最低限度の実行が可能です
```run.sh
>python MoveAverageTrade_Main.py --bar_minutes 1 --config_json configs/config_sample.json
```
  - 以下、引数の説明です
    - --bar_minutes: 必須。何分足を利用するかの指定
    - --config_json: 必須。アルゴリズムのパラメータが書かれたjsonを指定します。詳細は real_trade/configs/config_sample.json, real_trade/AlgorithmConfig.py, 実行する価格決定アルゴリズムを参照してください。
    - --test_bot: テストモードで動作します。使用する証拠金やbtcの量をかなり小さめに設定します。実際の量はハードコーディングされています。
    - --check_stop_make_position_file: 引数にファイルパスを指定します。指定したパスにファイルが存在すれば、このプログラムは既に持っているポジションを決済後、新規にポジションを作りません。
    - --preload_chart: 本プログラムは起動直後から分足データを溜め始めますが、この引数で指定したファイルから実行時刻以前のチャート情報を読み込ませることができます。
    - --trade_center: 取引所を変更する場合に使います。現在は"coincheck"のみ対応
    - [deprecated parameters]
      - use_ma_bar_counts, open_div_rates, close_div_rates, max_hold_bar_counts, lots
      - これらのパラメータは config_json で指定する json ファイル内に書かれていることを期待しています。

## Licenses

外部ライブラリを除き、BSDライセンスに準拠します。詳細は LICENSE.txt をご覧ください。
外部ライセンスに関してはオリジナルのライセンスを継承します。

==========

