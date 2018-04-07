cryptocurrency-autotrading
==========

※English follows after Japanese.

## Overview
暗号通貨の自動トレードを行うプログラムです。

## Description

以下に対応した自動トレードプログラムです。

- 値動きデータをAPI経由でリアルタイムに取得し、分足単位のデータとしてメモリ上に格納。
- 分足単位のデータを利用して売買判断をする各種アルゴリズムを載せることが可能（tick単位での売買判断には未対応）。
- 実際に実装しているアルゴリズムは以下の3つ
  - 「単純移動平均線の値*指定割合1」の位置にin指値を置き続け、約定したら「約定値*指定割合2」の位置に決済指値を置き続ける
  - 直近最高値を超えたときに指値を置き、約定したら↑と同様に決済指値を置く
  - 指定した回数 陽線/陰線 が続いたときに指値を置く/成行で発注し、約定したら↑と同様に決済指値を置く
  - 上記3アルゴリズムはすべて「ポジション保有後、一定時間超えても決済されない場合は成行で強制決済」機能付き
- 疑似的な stoploss 機能も実装。

## Requirements

## Usage

## Licenses

外部ライブラリを除き、BSDライセンスに準拠します。詳細は LICENSE.txt をご覧ください。
外部ライセンスに関してはオリジナルのライセンスを継承します。

==========

In English

## Overview
暗号通貨の自動トレードを行うプログラムです。

## Description

以下に対応した自動トレードプログラムです。

- 値動きデータをAPI経由でリアルタイムに取得し、分足単位のデータとしてメモリ上に格納。
- 分足単位のデータを利用して売買判断をする各種アルゴリズムを載せることが可能（tick単位での売買判断には未対応）。
- 実際に実装しているアルゴリズムは以下の3つ
  - 「単純移動平均線の値*指定割合1」の位置にin指値を置き続け、約定したら「約定値*指定割合2」の位置に決済指値を置き続ける
  - 直近最高値を超えたときに指値を置き、約定したら↑と同様に決済指値を置く
  - 指定した回数 陽線/陰線 が続いたときに指値を置く/成行で発注し、約定したら↑と同様に決済指値を置く
  - 上記3アルゴリズムはすべて「ポジション保有後、一定時間超えても決済されない場合は成行で強制決済」機能付き
- 疑似的な stoploss 機能も実装。

## Requirements

## Usage

## Licenses

Except for external libraries and resources, this software is released under the New BSD License, see LICENSE.txt.
External libraries and resources which are used in this project inherit their original license.
