# @Time    : 2022/10/25 22:19
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : comminfo.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
import backtrader as bt


class FuturesCommInfo(bt.CommInfoBase):
    params = (
        ("stocklike", False),
        ("commtype", bt.CommInfoBase.COMM_PERC),  # 按比例收取手续费
        ("percabs", True),  # 0.0002 = 0.2%
        ("commission", None),
        ("mult", 1),
        ("margin", None),
        ("leverage", 1.0),  # no leverage for now
        ("interest", 0.0)  # no yearly interest charged for holding a short selling position
    )

    def _getcommission(self, size, price, pseudoexec):
        """
        Commission = size *  price * proportion of commission * contract multiplier
        """
        return abs(size) * price * self.p.commission * self.p.mult

    def get_margin(self, price):
        """
        margin per trade = price * contract multiplier * margin rate
        """
        return price * self.p.mult * self.p.margin