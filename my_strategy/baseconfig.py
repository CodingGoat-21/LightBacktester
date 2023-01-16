# @Time    : 2022/10/25 22:19
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : baseconfig.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
from datetime import datetime


class BaseConfig():

    # backtest range
    fromdate = datetime(2016, 1, 1)
    todate = datetime(2022, 1, 1)

    # basic parameters
    startcash = 10000  # start cash
    stocklike = True
    mult = 1
    margin = 1
    commission = 0.0
    interest = 0.0

    # info print
    print_orders_trades = False