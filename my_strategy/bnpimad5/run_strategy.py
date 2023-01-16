# @Time    : 2022/10/27 23:06
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : run_strategy.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
from datetime import datetime
import pandas as pd

import backtrader as bt
from backtrader.feeds import PandasData  # to extend DataFeeds

from LightBacktester.my_strategy.baseconfig import BaseConfig
from LightBacktester.my_strategy.comminfo import FuturesCommInfo
from LightBacktester.model.bnpi_trend_score import bnpi_trend_score
from LightBacktester.extension.dataloader import DataLoader
from strategy import Strategy



class Config(BaseConfig):
    """
    Set your strategy custom parameters here
    """

    """ path parameters """
    data_load_mode = 'local'
    data_file_name = 'multi_asset.csv'

    """ data preprocessing parameters """
    rolling_window = 252

    """ risk control parameters """
    risk_mode = True
    risk_control_period = 20  # backtest days for risk control
    std_calculate_period = 30  # backtest days to calculate volatility

    """ mvo parameters """
    weights_sum = 2
    target_vol = 0.05  # target volatility in mean variance optimization
    high_risk_asset = ['BB_COM', 'EUROSTOXX50', 'N225', 'SP500', 'SPGSGC']
    low_risk_asset = ['GER_10Y', 'JAP_10Y', 'US_10Y']
    high_risk_bound = (0, 0.25)
    low_risk_bound = (0, 0.5)

    """ strategy parameters """
    rebal_monthday = [30]  # portfolios rebalance date for each period
    data_frequency = 252  # input data frequency
    constant_cash_weight = 1 / weights_sum  # control holding position weight
    trade_percet = 0.02

    """ backtest range """
    fromdate = datetime(2016, 1, 1)
    todate = datetime(2022, 8, 1)

    """ basic parameters """
    startcash = 1000000000  # start cash
    mult = 1
    margin = 1 / weights_sum
    commission = 0.0002


class Comminfo(FuturesCommInfo):
    """
    Set your strategy custom commission information here
    """
    params = (
        ("stocklike", False),
        ("commtype", bt.CommInfoBase.COMM_PERC),  # commision at percentage
        ("percabs", True),  # 0.0002 = 0.2%
        ("commission", Config.commission),
        ("mult", Config.mult),
        ("margin", Config.margin),
        ("leverage", 1.0),  # no leverage for now
        ("interest", 0.0)  # no yearly interest charged for holding a short selling position
    )


class DataPreprocessing():
    """
    Set your strategy custom data preprocessing here
    """
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.data.index = pd.to_datetime(data.index)

    def get_data(self) -> pd.DataFrame:
        return self.data.iloc[:, 1:]

    def get_benchmark(self) -> pd.Seires:
        return self.data.iloc[:, 0]

    def get_trend_score(self, rolling_window: int) -> pd.DataFrame:
        return bnpi_trend_score(self.data, rolling_window)


class DataExtend(PandasData):
    """
    Extend your data line here
    """
    lines = ('trend_signal',)
    params = (('trend_signal', 8),)


class Result():
    pass


class Analyzer():
    pass


"""
Strategy run function
"""


def run():

    """
    Load data
    """
    dataloader = DataLoader(Config.data_load_mode)
    datas = dataloader.start_load()

    """
    Preprocess data
    """
    preprocess = DataPreprocessing(datas)
    mad5_assets = preprocess.get_data()
    benchmark = preprocess.get_benchmark()
    bnpp_trend_score = preprocess.get_trend_score(Config.rolling_window)

    """
    Set cerebro
    """
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)

    """
    Add data
    """
    for asset_name in mad5_assets.columns:
        df = pd.merge(mad5_assets[asset_name], pd.DataFrame(bnpp_trend_score[asset_name]), left_index=True,
                      right_index=True)
        df.columns = ['close', 'trend_signal']
        data = DataExtend(
            dataname=df,
            close=0,
            trend_signal=1,
            high=None,
            low=None,
            volume=None,
            openinterest=None,
            fromdate=Config.fromdate,
            todate=Config.todate,
            plot=False
        )

        cerebro.adddata(data, name=asset_name)

    """
    Set comminfo
    """
    comminfo = Comminfo()

    """
    Set broker
    """
    cerebro.broker.addcommissioninfo(comminfo)
    cerebro.broker.setcash(Config.startcash)
    cerebro.broker.set_coc(True)  # trade with close price
    cerebro.broker.set_int2pnl(True)  # set interests to profit and loss

    """
    Add stategy
    """
    cerebro.addstrategy(Strategy)