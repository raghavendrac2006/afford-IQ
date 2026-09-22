"""
Currency Normalization Infrastructure for Afford IQ On-Device Financial Decision Agent
Provides deterministic FX conversion using dataset/exchange_rates.csv.
"""
from typing import Dict, Tuple, Optional, List
try:
    from models import ExchangeRate, FinancialEvent
except ImportError:
    from code.models import ExchangeRate, FinancialEvent


class CurrencyConverter:
    def __init__(self, exchange_rates: List[ExchangeRate]):
        # Index: (rate_date, from_currency, to_currency) -> rate
        self.rates_index: Dict[Tuple[str, str, str], float] = {}
        for r in exchange_rates:
            key = (r.rate_date, r.from_currency, r.to_currency)
            self.rates_index[key] = r.rate

    def get_rate(self, rate_date: str, from_curr: str, to_curr: str) -> Optional[float]:
        if from_curr == to_curr:
            return 1.0
        return self.rates_index.get((rate_date, from_curr, to_curr))

    def convert(
        self,
        amount: Optional[float],
        from_curr: str,
        to_curr: str,
        date_str: str
    ) -> Optional[float]:
        """
        Converts an amount from from_curr to to_curr on date_str.
        Returns converted amount or None if amount or rate is missing.
        """
        if amount is None:
            return None

        if from_curr == to_curr:
            return amount

        rate = self.get_rate(date_str, from_curr, to_curr)
        if rate is None:
            return None

        return amount * rate

    def convert_event(
        self,
        event: FinancialEvent,
        target_currency: str,
        use_date: str = 'settlement_date'
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Converts a FinancialEvent's amount to target_currency.
        use_date: 'settlement_date' or 'event_date'
        Returns: (converted_amount, rate_used)
        """
        if event.amount is None:
            return None, None

        date_str = event.settlement_date if use_date == 'settlement_date' else event.event_date
        rate = self.get_rate(date_str, event.currency, target_currency)
        if rate is None:
            return None, None

        return event.amount * rate, rate
