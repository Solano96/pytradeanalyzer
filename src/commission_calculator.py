
class CommissionCalculator:
    '''
    Example of commision config:
    1. Without interval:
        {'amount': 2}
        {'percentage': 1}

    2. With different intervals
        [
            {'interval': (0, 1000), 'commission': {'amount': 5}},
            {'interval': (1000, 5000), 'commission': {'percentage': 2}},
            {'interval': (5000, float('inf')), 'commission': {'percentage': 1}}
        ]

    3. Differentiating between buy and sell
        {
            'buy': {'amount': 2},
            'sell': {'percentage': 1}
        }

        {
            'buy': [
                {'interval': (0, 1000), 'commission': {'amount': 5}},
                {'interval': (1000, 5000), 'commission': {'percentage': 2}},
                {'greater_than': 5000, 'commission': {'percentage': 1}}
            ],
            'sell': {'percentage': 1}
        }

    It is possible to apply a fixed commission and also add a variable part
    {'amount': 2, 'percentage': 1}
    '''

    @classmethod
    def _get_commision_cost(cls, commission_single_config, operation_amount: float) -> float:
        if 'amount' in commission_single_config or 'percentage' in commission_single_config:
            commission_cost = 0
            if 'amount' in commission_single_config:
                commission_cost += commission_single_config['amount']
            if 'percentage' in commission_single_config:
                commission_cost += operation_amount*(commission_single_config['percentage']/100)
            return commission_cost
        else:
            raise Exception("ERROR: commission config not valid.")

    @classmethod
    def get_commission_cost(cls, commission_config, operation_amount: float, operation_type: str = '') -> float:
        if isinstance(commission_config, dict):
            if 'sell' in commission_config and 'buy' in commission_config:
                return cls.get_commission_cost(commission_config[operation_type], operation_amount)
            else:
                return cls._get_commision_cost(commission_config, operation_amount)
        elif isinstance(commission_config, list):
            apply_commission = False
            for commission in commission_config:
                if 'interval' in commission:                    
                    interval = commission['interval']
                    if operation_amount >= interval[0] and operation_amount < interval[1]:
                        apply_commission = True
                elif 'greater_than' in commission:
                    if operation_amount >= commission['greater_than']:
                        apply_commission = True
                if apply_commission:
                    return cls._get_commision_cost(commission, operation_amount)
        else:
            raise Exception("ERROR: commission config not valid.")