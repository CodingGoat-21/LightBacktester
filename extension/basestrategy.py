# @Time    : 2022/10/25 17:03
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : basestrategy.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
import backtrader as bt
import importlib
from LightBacktester.run import SelectStrategy





def getAllParameters(configObj) -> tuple:
    """
    Convert config into tuple in order to plug into bt.Strategy
    :param configObj: Config from my_strategy
    :return: tuple
    """
    all_params = []
    for attr in dir(configObj):
        if not attr.endswith('__'):
            all_params.append((attr, getattr(configObj, attr)))
    return tuple(all_params)