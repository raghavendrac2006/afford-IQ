"""
Financial State Reconstruction for Afford IQ On-Device Financial Decision Agent
Calculates liquid cash positions, reserved pending debits, and essential budgets.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from models import FinancialProfile, FinancialEvent
    from event_classifier import EventClassifier, EventClassification
    from currency import CurrencyConverter
    from image_resolver import ImageResolver
except ImportError:
    from code.models import FinancialProfile, FinancialEvent
    from code.event_classifier import EventClassifier, EventClassification
    from code.currency import CurrencyConverter
    from code.image_resolver import ImageResolver


@dataclass
class UserFinancialState:
    user_id: str
    home_currency: str
    request_date: str
    current_available_balance: float
    minimum_balance_to_keep: float
    settled_past_inflows_converted: float
    settled_past_outflows_converted: float
    pending_debit_reservations_converted: float
    pending_credits_excluded_converted: float
    scheduled_future_inflows_converted: float
    scheduled_future_outflows_converted: float
    unrealized_investments_excluded: float
    starting_safe_balance: float
    reserved_pending_debit_ids: List[str] = field(default_factory=list)


class FinancialStateResolver:
    def __init__(self, currency_converter: CurrencyConverter, image_resolver: Optional[ImageResolver] = None):
        self.currency_converter = currency_converter
        self.image_resolver = image_resolver
        self.classifier = EventClassifier()

    def resolve_event_amount_converted(self, evt: FinancialEvent, home_curr: str) -> float:
        amt = evt.amount
        if amt is None and self.image_resolver:
            res = self.image_resolver.resolve_event_amount(evt)
            if res.get("resolved") and res.get("amount") is not None:
                amt = res["amount"]

        if amt is None or amt <= 0:
            return 0.0

        # Convert currency
        conv_amt = self.currency_converter.convert(amt, evt.currency, home_curr, evt.event_date)
        return conv_amt if conv_amt is not None else 0.0

    def resolve_state(
        self,
        profile: FinancialProfile,
        user_events: List[FinancialEvent],
        request_date: str
    ) -> UserFinancialState:
        home_curr = profile.home_currency
        curr_bal = profile.current_available_balance
        min_bal = profile.minimum_balance_to_keep

        settled_past_inflows = 0.0
        settled_past_outflows = 0.0
        pending_debit_reservations = 0.0
        pending_credits_excluded = 0.0
        scheduled_future_inflows = 0.0
        scheduled_future_outflows = 0.0
        unrealized_excluded = 0.0
        reserved_debit_ids = []

        for evt in user_events:
            cl = self.classifier.classify_event(evt)
            amount_val = self.resolve_event_amount_converted(evt, home_curr)

            if cl.category == 'pending_debit_reservation':
                # Pending debits on or before request_date must be reserved against balance immediately
                if evt.event_date <= request_date:
                    pending_debit_reservations += amount_val
                    reserved_debit_ids.append(evt.event_id)

            elif cl.category == 'pending_credit_not_counted':
                # Pending credits are excluded until settled
                pending_credits_excluded += amount_val

            elif cl.category == 'unrealized_non_cash':
                # Non-cash investment valuations excluded
                unrealized_excluded += amount_val

            elif cl.category == 'settled_cash':
                if evt.settlement_date <= request_date:
                    if cl.direction_category == 'inflow':
                        settled_past_inflows += amount_val
                    elif cl.direction_category == 'outflow':
                        settled_past_outflows += amount_val

            elif cl.category == 'scheduled_future_cash':
                if evt.settlement_date > request_date:
                    if cl.direction_category == 'inflow':
                        scheduled_future_inflows += amount_val
                    elif cl.direction_category == 'outflow':
                        scheduled_future_outflows += amount_val

        # Starting safe balance on request_date is current_available_balance minus pending debits reserved
        starting_safe_balance = curr_bal - pending_debit_reservations

        return UserFinancialState(
            user_id=profile.user_id,
            home_currency=home_curr,
            request_date=request_date,
            current_available_balance=curr_bal,
            minimum_balance_to_keep=min_bal,
            settled_past_inflows_converted=settled_past_inflows,
            settled_past_outflows_converted=settled_past_outflows,
            pending_debit_reservations_converted=pending_debit_reservations,
            pending_credits_excluded_converted=pending_credits_excluded,
            scheduled_future_inflows_converted=scheduled_future_inflows,
            scheduled_future_outflows_converted=scheduled_future_outflows,
            unrealized_investments_excluded=unrealized_excluded,
            starting_safe_balance=starting_safe_balance,
            reserved_pending_debit_ids=reserved_debit_ids
        )
