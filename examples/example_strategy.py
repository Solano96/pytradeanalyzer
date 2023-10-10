from pandas import DataFrame
from typing import Any

from src.strategy import Strategy


class ExampleStrategy(Strategy):

    def __init__(self, df: DataFrame, init_capital: float, commision_config: Any):
        super().__init__(df, init_capital, commision_config)

    def next(self):
        i = self.current_period
        if i > 5:
            if self.shares == 0:
                if self.data_close[i] > self.data_close[i-1]:
                    if self.data_close[i-1] > self.data_close[i-2]:
                        self.buy(all=True)

            if self.shares > 0:
                if self.data_close[i] < self.data_close[i-1]:
                    if self.data_close[i-1] < self.data_close[i-2]:
                        self.sell(all=True)