# @Time    : 2022/10/25 22:19
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : dataloader.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
from LightBacktester.run import SelectStrategy
import importlib
import pandas as pd


class DataLoader():
    """
    There are two kinds to mode to load data for strategy:
    'local': The data is put in the {strategy_name}/data file
    'ts': Get data from tushare Todo
    'ak': Get data from akshare Todo
    """
    def __init__(self, load_mode: str):
        self.load_mode = load_mode

        if self.load_mode == "local":
            run_strategy = importlib.import_module(SelectStrategy.my_strategy_run_path)
            data_file_name = run_strategy.Config.data_file_name
            strategy_name = SelectStrategy.my_strategy_name
            self.data_path = f"LightBacktester/my_strategy/{strategy_name}/data/{data_file_name}"
        else:
            self.data_path = None

    def start_load(self):
        if self.load_mode == "local":
            if self.data_path.endswith('csv'):
                return pd.read_csv(self.data_path, index_col=0)
            if self.data_path.endswith('xlsx'):
                return pd.read_xlsx(self.data_path, index_col=0)
