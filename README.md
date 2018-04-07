cryptocurrency-autotrading
==========

��Japanese follows after English.

## Overview
Crypto-currency auto trading system.

Until end of 2017, this system earns 5%�`10% per month but probably does not work well on current market.

## Description

Crypto-currency auto trading system.
��Coincheck is only supported.

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

���{���README

## Overview
�Í��ʉ݂̎����g���[�h���s���v���O�����ł��B

2017�N�I��育��܂ł͌�5%�`10%�̊����ŗ��v���o�Ă��܂������A���݂̑���ł͗��v���o���Ȃ����̂��Ǝv���܂��B

## Description

�ȉ��ɑΉ������Í��ʉݎ����g���[�h�v���O�����ł��B
�����ݎ������Coincheck�̂ݑΉ���

- �l�����f�[�^��API�o�R�Ń��A���^�C���Ɏ擾���A�����P�ʂ̃f�[�^�Ƃ��ă�������Ɋi�[�B
- �����P�ʂ̃f�[�^�𗘗p���Ĕ������f������e��A���S���Y�����ڂ��邱�Ƃ��\�itick�P�ʂł̔������f�ɂ͖��Ή��j�B
- ���ۂɎ������Ă���A���S���Y���͈ȉ���3��
  - �u�P���ړ����ϐ��̒l*�w�芄��1�v�̈ʒu��in�w�l��u�������A��肵����u���l*�w�芄��2�v�̈ʒu�Ɍ��ώw�l��u��������
  - ���ߍō��l�𒴂����Ƃ��Ɏw�l��u���A��肵���灪�Ɠ��l�Ɍ��ώw�l��u��
  - �w�肵���� �z��/�A�� ���������Ƃ��Ɏw�l��u��/���s�Ŕ������A��肵���灪�Ɠ��l�Ɍ��ώw�l��u��
  - ��L3�A���S���Y���͂��ׂāu�|�W�V�����ۗL��A��莞�Ԓ����Ă����ς���Ȃ��ꍇ�͐��s�ŋ������ρv�@�\�t��
- �^���I�� stoploss �@�\�������B

## Requirements

- OS: POSIX����
- Python 3.x
- python-dateutil
- websocket-client (install via pip)

## Usage

- ���O����
  - Coincheck�𗘗p���邽�߁ACoincheck��API�L�[�𔭍s���Ă��������i�ڍׂ͑��̕���������Ă���̂Œ��ׂĂ��������j
  - �ȉ��� permission ���K�v�ł�
    - �V�K����, �����ς̒����ꗗ, �����̃L�����Z��, �������, �|�W�V�����ꗗ, �A�J�E���g���, �c��, ���o���b�W�A�J�E���g�̎c��
  - �������ꂽAPI�L�[��[�A�N�Z�X�L�[]��1�s�ځA[�V�[�N���b�g�L�[]��2�s�ڂɏ������e�L�X�g�t�@�C�����ȉ��ɂ����Ă�������
    - real_trade/keys/coincheck.txt
    - !! ���̃t�@�C���͐�΂�git�Ǘ����ɒu���Ȃ��ł�������

- ������@
  - real_trade �f�B���N�g����ňȉ��̂悤�Ȉ�����^���邱�ƂōŒ���x�̎��s���\�ł�
```run.sh
>python MoveAverageTrade_Main.py --bar_minutes 1 --config_json configs/config_sample.json
```
  - �ȉ��A�����̐����ł�
    - --bar_minutes: �K�{�B�������𗘗p���邩�̎w��
    - --config_json: �K�{�B�A���S���Y���̃p�����[�^�������ꂽjson���w�肵�܂��B�ڍׂ� real_trade/configs/config_sample.json, real_trade/AlgorithmConfig.py, ���s���鉿�i����A���S���Y�����Q�Ƃ��Ă��������B
    - --test_bot: �e�X�g���[�h�œ��삵�܂��B�g�p����؋�����btc�̗ʂ����Ȃ菬���߂ɐݒ肵�܂��B���ۂ̗ʂ̓n�[�h�R�[�f�B���O����Ă��܂��B
    - --check_stop_make_position_file: �����Ƀt�@�C���p�X���w�肵�܂��B�w�肵���p�X�Ƀt�@�C�������݂���΁A���̃v���O�����͊��Ɏ����Ă���|�W�V���������ό�A�V�K�Ƀ|�W�V���������܂���B
    - --preload_chart: �{�v���O�����͋N�����ォ�番���f�[�^�𗭂ߎn�߂܂����A���̈����Ŏw�肵���t�@�C��������s�����ȑO�̃`���[�g����ǂݍ��܂��邱�Ƃ��ł��܂��B
    - --trade_center: �������ύX����ꍇ�Ɏg���܂��B���݂�"coincheck"�̂ݑΉ�
    - [deprecated parameters]
      - use_ma_bar_counts, open_div_rates, close_div_rates, max_hold_bar_counts, lots
      - �����̃p�����[�^�� config_json �Ŏw�肷�� json �t�@�C�����ɏ�����Ă��邱�Ƃ����҂��Ă��܂��B

## Licenses

�O�����C�u�����������ABSD���C�Z���X�ɏ������܂��B�ڍׂ� LICENSE.txt ���������������B
�O�����C�Z���X�Ɋւ��Ă̓I���W�i���̃��C�Z���X���p�����܂��B

==========

