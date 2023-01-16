# @Time    : 2022/10/25 13:12
# @Author  : Gaochen Gu (CodingGoat-21)
# @File    : mean_variance_optimization.py
# @Software: PyCharm 
# -*- coding: utf-8 -*-
import numpy as np
import scipy.optimize as sco


class meanVarianceOptimization():
    """
    Module function:
    """

    def _init_(self):
        pass

    @staticmethod
    def calculate_ret_and_cov(ret_matrix, data_frequency):
        """
        Calculate mean return and return covariance for further calculation
        :param ret_martix: the asset should be listed by COLUMNS in the matrix
        :param data_frequency: the value to annualize the mean return and volatility
        :return: ret_ave shapes as n x 1, ret_cov shapes as n x n (which n is the number of assets)
        """

        # Annualized return array (columns average return)
        ret_ave = np.mean(ret_matrix, axis=0) * data_frequency

        # Annualized standard deviation matrix
        ret_std = np.std(ret_matrix, axis=0) * data_frequency ** (1 / 2)

        # Annualized covariance matrix
        ret_cov = np.cov(ret_matrix.transpose(1, 0)) * data_frequency

        return ret_ave, ret_std, ret_cov

    def max_portfolio_return(self, mean_returns, cov_matrix, target_volatility, weights_sum, bounds=None):
        """
        Maximize the portfolio return given a targeted volatility
        :param mean_returns: shape as n x 1
        :param cov_matrix: shape as n x n
        :param target_volatility:
        :param weights_sum: total weights constraint
        :param bounds: set bounds for different assets, default None
        :return: opitmized return
        """

        # set value
        self.mean_returns = mean_returns
        self.cov_matrix = cov_matrix
        self.target_volatility = target_volatility

        # Extract the number of assets from the length of the returns vector
        num_assets = len(self.mean_returns)

        # Creates a tuple with the variables to be uses by the objective function
        args = self.mean_returns

        # The Constraints
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - weights_sum},
                       # The Constraints that the sum of the weight has to be equal to one
                       {'type': 'eq',
                        'fun': lambda x: np.dot(x.T, np.dot(self.cov_matrix, x)) - self.target_volatility ** 2}
                       # The Constraints that portfolio volatility should be the smallest
                       ,)


        # This runs the actual optimization
        result = sco.minimize(self._neg_portfolio_return, num_assets * [1. / num_assets, ], args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)

        # This put the results in a series
        opt_weights = result['x']
        return opt_weights

    @staticmethod
    def _neg_portfolio_return(weights, mean_returns):
        return -np.dot(weights.T, mean_returns)