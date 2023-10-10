from typing import List, NewType, TypedDict, Tuple, Union, Optional
from datetime import datetime

class CompletedOrder(TypedDict):
    date: datetime
    price: float
    number_shares: int
    type: str


class DateValue(TypedDict):
    date: datetime
    value: float

'''
Example of commission config with different intervals
[
    {'interval': (0, 1000), 'amount': 5},
    {'interval': (1000, 5000), 'percentage': 2},
    {'greater_than': 5000, 'percentage': 1}
]
Example of commission
'''

class CommissionSingleConfig(TypedDict, total=False):
    amount: float
    percentage: float


class CommissionIntervalConfig(TypedDict):
    interval: Tuple[float, float]
    commission: CommissionSingleConfig


class CommissionBuySellConfig(TypedDict):
    buy: Union[CommissionSingleConfig, List[CommissionIntervalConfig]]
    sell: Union[CommissionSingleConfig, List[CommissionIntervalConfig]]


CommissionConfig = Union[CommissionSingleConfig, List[CommissionIntervalConfig], CommissionBuySellConfig]


class OperationInfo(TypedDict):
    date: datetime
    type: str
    share_price: float
    number_shares: int
    total_operation: float
    operation_cost: float
    leftover_money: Optional[float]
    accumulated_cost: Optional[float]
    operation_profit: Optional[float]