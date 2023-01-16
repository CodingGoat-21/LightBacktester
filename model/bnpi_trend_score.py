# @Time    : 2022/10/28 15:01
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : bnpi_trend_score.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
import pandas as pd


def bnpi_trend_score(data: pd.DataFrame, rolling_window: int) -> pd.DataFrame:
    """
    Trend score algorithm from BNPIMAD5 strategy
    :param data: close pirce dataframe
    :param rolling_window:
    :return: trend score
    """
    trend_signal = data.rolling(rolling_window).apply(_rank_percentage).iloc[rolling_window + 1:].rank(axis=1,
                                                                                                    method='first')

    # The ranking is [1-8], where 1 is the smallest and 8 is the largest
    trend_signal[trend_signal == 1] = -1/3
    trend_signal[trend_signal == 2] = -1/6
    trend_signal[trend_signal == 3] = 0
    trend_signal[trend_signal == 4] = 1/6
    trend_signal[trend_signal == 5] = 1/3
    trend_signal[trend_signal == 6] = 1/2
    trend_signal[trend_signal == 7] = 2/3
    trend_signal[trend_signal == 8] = 1.0

    """
    The trend score is generated from current date close price, and should be used for the next trading date,
    which should be shift 1 down
    """
    return trend_signal.shift(1)


def _rank_percentage(x):
    return pd.Series(x).rank(pct=True).iloc[-1]