# @Time    : 2022/10/25 23:01
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : strategy.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import backtrader as bt

from LightBacktester.extension.basestrategy import BaseStrategy
from LightBacktester.extension.basestrategy import getAllParameters
from LightBacktester.model.mean_variance_optimization import meanVarianceOptimization
from run_strategy import Config


class Strategy(BaseStrategy):
    params = getAllParameters(Config)

    def __init__(self):
        super().__init__()

        # date
        self.current_date = None

        # put assets data
        self.assets = self.datas

        # results
        self.assets_name = [a._name for a in self.assets]
        self.dates_list = []
        self.weights = np.zeros(len(self.assets))  # single period weights
        self.weights_list = []  # whole period weights
        self.total_port_value = []  # total portfolio value array
        self.port_std = []  # portfolio volatility array

        # portfolio optimization parameters
        self.weights_sum = self.p.weights_sum

        # initialize model
        self.portOptModel = meanVarianceOptimization()
        # Set bounds for different assets
        bounds = list((0, 0) for asset_index in range(8))
        for asset_index in range(len(self.assets)):
            # high  risk asset bound
            if self.asset_name[asset_index] in self.p.high_risk_asset:
                bounds[asset_index] = self.p.high_risk_bound
            # low risk asset bound
            elif self.asset_name[asset_index] in self.p.low_risk_asset:
                bounds[asset_index] = self.p.low_risk_bound
        self.bounds = tuple(bounds)

        # set flag
        self.if_rebalance = False
        self.is_triggered = False

        # order list, in order to cancel all the orders before the rebalance date
        self.order_list = []

        # rebalance timer
        self.add_timer(
            when=bt.Timer.SESSION_START,
            monthdays=self.p.rebal_monthday,  # date in each month
            monthcarry=True,  # if the day is not trading day, move to the next day that can be traded
        )

    # next runs after timer
    def next(self):

        # current date
        self.current_date = bt.num2date(self.assets[0].datetime[0])

        # get current total value
        total_value = self.broker.getvalue()
        self.total_port_value.append(total_value)
        # calculate portfolio volatility in the past risk_control_period days
        period_volatility = (pd.Series(self.total_port_value).pct_change()[
                             -self.p.std_calculate_period:]).std() * np.sqrt(self.p.data_frequency)
        self.port_std.append(period_volatility)

        # cancel all the order
        for o in self.order_list:
            self.cancel(o)
        # reset the order list
        self.order_list = []

        # risk control
        # self.if_rebalance := portfolio risk control and should not be the rebalancing day
        # self.port_std := the length of port_std should be greater than risk_control_period
        # self.p.risk_mode := the mode should be True
        if (len(self.port_std) >= self.p.risk_control_period) and self.p.risk_mode and not self.if_rebalance:
            # get the highest volatility in the past risk_control_period days
            self.highest_vol = max(self.port_std[-self.p.risk_control_period:])
            # get risk control signal
            self.is_triggered = self.highest_vol > self.p.target_vol
            if self.is_triggered:
                self.log('Portfolios risk too high. Volatility: {}'.format(self.highest_vol))
                self.rebalance_portfolio()

        # reset flag
        self.is_triggered = False
        self.if_rebalance = False

        # save weights results
        # self.dates_list.append(self.current_date)
        # self.weights_list.append(
        #     [(self.getposition(a).size * self.getposition(a).price) / self.broker.getvalue() for i, a in
        #      enumerate(self.assets)])

    def notify_timer(self, timer, when):

        # check if the volatility reach the trigger condition
        if (len(self.port_std) >= self.p.risk_control_period) and self.p.risk_mode:
            # get the highest volatility in the past risk_control_period days
            self.highest_vol = max(self.port_std[-self.p.risk_control_period:])
            # get risk control signal
            self.is_triggered = self.highest_vol > self.p.target_vol

        # rebalance
        self.rebalance_portfolio()

        # save weights results
        # self.dates_list.append(self.current_date)
        # self.weights_list.append(
        #     [(self.getposition(a).size * self.getposition(a).price) / self.broker.getvalue() for i, a in
        #      enumerate(self.assets)])

        # reset flag
        self.is_triggered = False
        self.if_rebalance = True

    def rebalance_portfolio(self):

        # check if trigger risk control module and adjust targeted volatility and constant_cash_weight
        if self.is_triggered:
            weights_sum = self.p.weights_sum - (self.highest_vol - self.p.target_vol) / self.p.target_vol
            constant_cash_weight = 1 / weights_sum
        else:
            weights_sum = self.p.weights_sum
            constant_cash_weight = self.p.constant_cash_weight

        # cancel all the order
        for o in self.order_list:
            self.cancel(o)
        # reset the order list
        self.order_list = []

        # initialize
        self.ret_matrix = []
        self.current_trend_signal = []
        self.ret_ave = None
        self.ret_std = None
        self.ret_cov = None

        for i, d in enumerate(self.assets):
            # original ret
            close = np.array(self.assets[i].close)
            ret = np.diff(close) / close[1:]
            self.ret_matrix.append(ret[:self.p.std_calculate_period])
            # trend signal
            self.current_trend_signal.append(self.assets[i].trend_signal[0])

        # matrix's layout should be len(period) x n, where n is the number of assets
        self.ret_matrix = np.array(self.ret_matrix).transpose(1, 0)

        # calculate average return and covariance
        _, self.ret_std, self.ret_cov = self.portOptModel.calculate_ret_and_cov(self.ret_matrix, self.p.data_frequency)

        # According to MAD5 return rate algorithm, expected return rate = ∑ trend signal × asset volatility × asset weight,
        # that is, the return rate in the original model is changed into trend signal x volatility
        self.ret_ave = np.array(self.ret_std * self.current_trend_signal)

        # get weights by mean variance optimization
        self.weights = self.portOptModel.max_portfolio_return(self.ret_ave,
                                                              self.ret_cov,
                                                              self.p.target_vol,
                                                              weights_sum,
                                                              self.bounds)

        # always keep constant cash weight
        self.weights = self.weights * (1 - constant_cash_weight)

        # execute orders
        # rank assets descending by positions
        assets_weights_rank = [(self.assets[i], self.weights[i]) for i in range(len(self.assets))]
        if self.broker.getvalue() == 0:
            # sort weights, buy the largest weight assets
            assets_weights_rank.sort(key=lambda x: x[1], reverse=True)
        else:
            # sort value
            assets_weights_rank.sort(key=lambda x: self.broker.getvalue([x[0]]), reverse=True)

        for a_w in assets_weights_rank:
            # trade asset
            a = a_w[0]
            # weight
            w = a_w[1]
            # target value
            target_value = w * self.broker.getvalue() * (
                        1 - self.p.trade_percet)  # leave trade_percet cash to cover the commission and calculation error
            # size
            size = int(abs(self.broker.getvalue([a]) - target_value) / a.close[0])
            if target_value < self.broker.getvalue([a]):
                # larger position, sell
                o = self.sell(a, size=size, price=a.close[0])

            else:
                # fewer positions, buy
                o = self.buy(a, size=size, price=a.close[0])

            # mark the order
            self.order_list.append(o)