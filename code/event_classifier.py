"""
Event Classifier for HackerRank Orchestrate: Buy or Wait?
Provides deterministic classification of financial events by cash-flow status and direction.
"""
from dataclasses import dataclass
from typing import Dict, Any

try:
    from models import FinancialEvent
except ImportError:
    from code.models import FinancialEvent


@dataclass
class EventClassification:
    category: str
    direction_category: str
    is_cash_flow_effective: bool
    explanation: str


class EventClassifier:
    @staticmethod
    def classify_event(event: FinancialEvent) -> EventClassification:
        # Determine normalized direction
        if event.direction == 'credit':
            dir_cat = 'inflow'
        elif event.direction == 'debit':
            dir_cat = 'outflow'
        elif event.direction == 'non_cash':
            dir_cat = 'non_cash'
        else:
            dir_cat = 'unknown'

        # Determine cash-flow status category
        status = event.status.lower()
        event_type = event.event_type.lower()

        if status == 'cancelled':
            cat = 'cancelled'
            effective = False
            expl = "Event is cancelled and has no effect on cash flow."

        elif status == 'failed':
            cat = 'failed'
            effective = False
            expl = "Event failed and has no effect on cash flow."

        elif status == 'unrealized' or dir_cat == 'non_cash' or event_type == 'investment_valuation':
            cat = 'unrealized_non_cash'
            effective = False
            expl = "Unrealized investment valuation or non-cash record. Does not contribute to available cash."

        elif status == 'settled':
            cat = 'settled_cash'
            effective = True
            expl = f"Settled transaction confirmed as cash {dir_cat}."

        elif status == 'pending':
            if dir_cat == 'outflow':
                cat = 'pending_debit_reservation'
                effective = True
                expl = "Pending debit must be reserved against available balance immediately."
            elif dir_cat == 'inflow':
                cat = 'pending_credit_not_counted'
                effective = False
                expl = "Pending credit must NOT be counted towards cash balance until fully settled."
            else:
                cat = 'pending_other'
                effective = False
                expl = "Pending non-cash event."

        elif status == 'scheduled':
            cat = 'scheduled_future_cash'
            effective = True
            expl = f"Scheduled future transaction to take effect on settlement date ({event.settlement_date})."

        else:
            cat = 'unknown'
            effective = False
            expl = f"Unknown event status: {event.status}"

        return EventClassification(
            category=cat,
            direction_category=dir_cat,
            is_cash_flow_effective=effective,
            explanation=expl
        )
