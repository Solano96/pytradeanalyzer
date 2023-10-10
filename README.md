# pytradeanalyzer

Python library for backtesting. Library still under development...

This library arises due to some shortcomings in order to make more realistic simulations, among others the cost of the commission for each operation in a much more flexible and customizable way. On the other hand, it has been made a much lighter library and also allows interactive charts with plotly.

## Commission example
Examples of commision config:
1. Without interval:
```
    commission = {'amount': 2}
    commission = {'percentage': 1}
```

2. With different intervals
```
    commission = [
        {'interval': (0, 1000), 'commission': {'amount': 5}},
        {'interval': (1000, 5000), 'commission': {'percentage': 2}},
        {'interval': (5000, float('inf')), 'commission': {'percentage': 1}}
    ]
```

3. Differentiating between buy and sell
```
    commission = {
        'buy': {'amount': 2},
        'sell': {'percentage': 1}
    }

    commission = {
        'buy': [
            {'interval': (0, 1000), 'commission': {'amount': 5}},
            {'interval': (1000, 5000), 'commission': {'percentage': 2}},
            {'greater_than': 5000, 'commission': {'percentage': 1}}
        ],
        'sell': {'percentage': 1}
    }
```

It is possible to apply a fixed commission and also add a variable part
```
  commission = {
    'amount': 2,
    'percentage': 1
  }
```
