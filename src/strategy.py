from abc import ABC, abstractmethod
import logging
from pandas import DataFrame
from typing import Any, List, Optional
from datetime import datetime

from src.backtesting_engine.plot_chart import plot_candlestick
from src.backtesting_engine.type_dict_classes import (
    CompletedOrder,
    DateValue
)
from src.backtesting_engine.commission_calculator import CommissionCalculator


class StrategyMetrics:

    def __init__(self) -> None:
        self.total_trades = 0
        self.positive_trades = 0
        self.negative_trades = 0
        self.average_trades = 0
        self.average_positive_trades = 0
        self.average_negative_trades = 0
        self.max_drawdown = 0
        self.accumulate = 0
        self.accumulate_profit = 0
        self.accumulate_loss = 0
        self.drawdowns = []


class Strategy(ABC):

    def __init__(self, df: DataFrame, init_capital: float, commission_config: Any):
        self.df = df
        self.init_capital = init_capital
        self.capital = init_capital
        self.shares = 0
        self.commission_config = commission_config
        self.current_period = 0
        self.data_close: List[float] = list(self.df['Close'])
        self.data_open: List[float] = list(self.df['Open'])
        self.data_high: List[float] = list(self.df['High'])
        self.data_low: List[float] = list(self.df['Low'])
        self.dates: List[datetime] = list(self.df.index)
        self.data = self.df.reset_index().to_dict('records')
        self.completed_purchases: List[CompletedOrder] = []
        self.completed_sales: List[CompletedOrder] = []
        self.completed_transactions: List[CompletedOrder] = []
        self.historical_capital: List[DateValue] = []
        self.indicators = []
        self.metrics = StrategyMetrics()
        self._pending_orders = {}
        self._order_id = 0
        self._before_shares = 0
        self._before_capital = init_capital
        self._capital_before_buy = init_capital

    def buy(self, **options):
        logging.info(f'{self.dates[self.current_period]} CREATE BUY ORDER. {options}')
        self._pending_orders[str(self._order_id)] = {'type': 'buy', 'options': options}
        self._order_id += 1
    
    def sell(self, **options):
        logging.info(f'{self.dates[self.current_period]} CREATE SELL ORDER. {options}')
        self._pending_orders[str(self._order_id)] = {'type': 'sell', 'options': options}
        self._order_id += 1

    @abstractmethod
    def next(self):
        pass

    def execute_strategy(self):
        logging.info('START STRATEGY SIMULATION')
        self.current_period = 0

        for row in self.data:
            logging.debug(f'{self.dates[self.current_period]} OPEN: {self.data_open[self.current_period]}, CLOSE: {self.data_close[self.current_period]}')
            self._process_pending_orders()
            self._update_strategy_metrics()
            self.current_data = row
            self.next()
            date_value = {
                'date': self.dates[self.current_period],
                'value': self.capital + self.shares*self.data_close[self.current_period]
            }
            self.historical_capital.append(date_value)
            self.current_period += 1

        logging.info('END STRATEGY SIMULATION')

        return self.capital, self.shares, self.capital + self.shares*self.data_close[self.current_period-1]

    def _buy(self, options: dict) -> bool:
        order_type = options['order_type'] if 'order_type' in options else 'market_order'

        if order_type == 'limit':
            buy_price = options['buy_price']
            if self.data_open[self.current_period] > buy_price:
                return False

        price_per_share = self.data_open[self.current_period]
        number_shares = 0
        if 'number_shares' in options:
            number_shares = options['number_shares']
        elif 'all' in options:
            if options['all']:
                find_number_shares = False
                number_shares = self.capital//price_per_share
                while not find_number_shares:
                    operation_amount = price_per_share*number_shares
                    operation_amount += CommissionCalculator.get_commission_cost(self.commission_config, operation_amount, 'buy')
                    if self.capital >= operation_amount:
                        find_number_shares = True
                    else:
                        number_shares -= 1
        elif 'capital_percentage' in options:
            number_shares = self.capital*options['capital_percentage']//price_per_share
        elif 'capital_amount' in options:
            number_shares = options['capital_amount']//price_per_share
        else:
            number_shares = 1
        
        order_completed = False
        order_canceled_msg = 'Order canceled. '
        number_shares = int(number_shares)

        if number_shares > 0:
            operation_amount = price_per_share*number_shares
            commission = CommissionCalculator.get_commission_cost(self.commission_config, operation_amount, 'buy')
            if self.capital >= operation_amount+commission:
                self.capital -= commission
                self.capital -= operation_amount
                self.shares += number_shares
                order_completed = True
            else:
                order_canceled_msg += 'The capital is less than the cost of the purchase.'
        else:
            order_canceled_msg += 'Number of shares to buy must to be greater than 0.'

        if order_completed:
            self.completed_purchases.append(
                {
                    'date': self.dates[self.current_period],
                    'price': price_per_share,
                    'number_shares': number_shares,
                    'type': 'purchase'
                }
            )
            self.completed_transactions.append(self.completed_purchases[-1])
            logging.info(f'{self.dates[self.current_period]} BUY order completed')
            logging.info(f'{self.dates[self.current_period]} >> Price: {price_per_share}')
            self._log_current_portfolio()
        else:
            logging.info(order_canceled_msg)

        return True

    def _sell(self, options):
        order_type = options['order_type'] if 'order_type' in options else 'market_order'

        if order_type == 'limit':
            sell_price = options['sell_price']
            if self.data_open[self.current_period] < sell_price:
                return False

        price_per_share = self.data_open[self.current_period]
        if 'number_shares' in options:
            number_shares = options['number_shares']
        elif 'number_shares_percentage' in options:
            number_shares = int(self.shares*options['number_shares_percentage'])
        elif 'all' in options:
            number_shares = self.shares
        else:
            number_shares = 1

        order_completed = False
        order_canceled_msg = 'Order canceled. '
        number_shares = int(number_shares)

        if number_shares > 0:
            if number_shares <= self.shares:
                operation_amount = number_shares*price_per_share
                self.capital -= CommissionCalculator.get_commission_cost(self.commission_config, operation_amount, 'buy')
                self.capital += operation_amount
                self.shares -= number_shares
                order_completed = True
            else:
                order_canceled_msg += 'The number of shares to be sold is greater than the number of shares owned.'
        else:
            order_canceled_msg += 'Number of shares to sell must to be greater than 0.'
            
        if order_completed:
            self.completed_sales.append(
                {
                    'date': self.dates[self.current_period],
                    'price': price_per_share,
                    'number_shares': number_shares,
                    'type': 'sale'
                }
            )
            self.completed_transactions.append(self.completed_sales[-1])
            logging.info(f'{self.dates[self.current_period]} SELL order completed')
            logging.info(f'{self.dates[self.current_period]} >> Price: {price_per_share}')
            self._log_current_portfolio()
        else:
            logging.info(order_canceled_msg)

        return True

    def _log_current_portfolio(self) -> None:
        logging.info(f'{self.dates[self.current_period]} >> Capital: {self.capital}')
        logging.info(f'{self.dates[self.current_period]} >> Shares: {self.shares}')
        logging.info('---------------------------------------------------------')

    def _process_pending_orders(self) -> None:
        orders_to_delete = []

        for order_id, order_config in self._pending_orders.items():
            if order_config['type'] == 'buy':
                if self._buy(order_config['options']):
                    orders_to_delete.append(order_id)
            elif order_config['type'] == 'sell':
                if self._sell(order_config['options']):
                    orders_to_delete.append(order_id)

        for order_id in orders_to_delete:
            self._pending_orders.pop(order_id)

    def _update_strategy_metrics(self) -> None:
        if self.shares == 0 and self._before_shares > 0:
            trade_return = (self.capital-self._capital_before_buy)/self._capital_before_buy
            self.metrics.total_trades += 1
            self.metrics.accumulate += trade_return
            self.metrics.average_trades = self.metrics.accumulate/self.metrics.total_trades

            if trade_return >= 0:
                self.metrics.positive_trades += 1
                self.metrics.accumulate_profit += trade_return
                self.metrics.average_positive_trades = self.metrics.accumulate_profit/self.metrics.positive_trades
            elif trade_return < 0:
                self.metrics.negative_trades += 1
                self.metrics.accumulate_loss += trade_return
                self.metrics.average_negative_trades = self.metrics.accumulate_loss/self.metrics.negative_trades

            self._capital_before_buy = self.capital

        min_period_value = self.capital + self.shares*self.data_low[self.current_period]
        max_period_value = self.capital + self.shares*self.data_high[self.current_period]

        if len(self.metrics.drawdowns) == 0 or max_period_value > self.metrics.drawdowns[-1]['max']:
            drawdown = {
                'min': min_period_value,
                'max': max_period_value,
                'drawdown': 100*(max_period_value-min_period_value)/max_period_value
            }
            self.metrics.drawdowns.append(drawdown)
        elif min_period_value < self.metrics.drawdowns[-1]['min']:
            self.metrics.drawdowns[-1]['min'] = min_period_value
            self.metrics.drawdowns[-1]['drawdown'] = 100*(self.metrics.drawdowns[-1]['max']-min_period_value)/self.metrics.drawdowns[-1]['max']

        if self.metrics.drawdowns[-1]['drawdown'] > self.metrics.max_drawdown:
            self.metrics.max_drawdown = self.metrics.drawdowns[-1]['drawdown']

        self._before_shares = self.shares
        self._before_capital = self.capital

    def cancel_pending_orders(self):
        self._pending_orders = {}

    def exist_pending_orders(self) -> bool:
        if len(self._pending_orders) > 0:
            return True
        else:
            return False

    def plot_strategy(
        self,
        plot_type='candle',
        theme_name: str = 'LIGHT_THEME',
        data_name: str = '',
        width: Optional[int] = None,
        height: Optional[int] = None,
        show_fig: bool = True,
        save_fig: bool = False,
        path_fig: str = ''
    ) -> None:
        plot_candlestick(
            df=self.df,
            plot_type=plot_type,
            indicators=self.indicators,
            operations={'buy': self.completed_purchases, 'sell': self.completed_sales},
            capital_series=self.historical_capital,
            theme_name=theme_name,
            data_name=data_name,
            width=width,
            height=height,
            show_fig=show_fig,
            save_fig=save_fig,
            path_fig=path_fig
        )

    def get_buy_and_hold_profit_before_period(self, to_period: int = -1) -> float:
        profit = self.init_capital*self.df['Close'][to_period]/self.df['Open'][0]
        profit -= CommissionCalculator.get_commission_cost(self.commission_config, self.init_capital*self.df['Close'][0], 'buy')
        return profit


